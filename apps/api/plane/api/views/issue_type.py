# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# Lumnus fork addition: public-API endpoints for work item types + project
# features (work-item-types toggle). CE ships the IssueType model + the
# Project.is_issue_type_enabled flag but not the public-API surface (it lived in
# the closed ee/ package). These expose the Mode-B (per-project) path the Plane
# SDK / MCP `resolve_work_item_type` uses, so Epic/Story/Task become drivable via
# PAT-authenticated REST + the local MCP. See run 2026-W26/2026-06-22-plane-epics-full-stack.

# Django imports
from django.db import IntegrityError
from django.db.models import Q

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.api.serializers import (
    WorkItemTypeSerializer,
    WorkItemTypeCreateUpdateSerializer,
)
from plane.app.permissions import ProjectMemberPermission
from plane.db.models import IssueType, ProjectIssueType, Project

from .base import BaseAPIView


# Project feature flags exposed via the public API and the Project model field
# they map to. SDK ProjectFeature carries more keys; we surface the ones the
# CE Project model backs, with work_item_types as the load-bearing one.
PROJECT_FEATURE_MAP = {
    "cycles": "cycle_view",
    "modules": "module_view",
    "views": "issue_views_view",
    "pages": "page_view",
    "intakes": "intake_view",
    "work_item_types": "is_issue_type_enabled",
}


def _feature_payload(project):
    return {feat: bool(getattr(project, field, False)) for feat, field in PROJECT_FEATURE_MAP.items()}


def _ensure_default_types(project):
    """On enabling work item types, ensure the Task (default) + Epic types exist
    and are linked to the project — mirrors Plane's enable-auto-creates-two-types
    behaviour."""
    workspace_id = project.workspace_id

    def _ensure(name, is_epic, is_default):
        issue_type = (
            IssueType.objects.filter(
                workspace_id=workspace_id,
                project_issue_types__project_id=project.id,
                name=name,
            ).first()
        )
        if issue_type is None:
            issue_type = IssueType.objects.create(
                workspace_id=workspace_id,
                name=name,
                is_epic=is_epic,
                is_default=is_default,
            )
        ProjectIssueType.objects.get_or_create(
            project_id=project.id,
            issue_type=issue_type,
            defaults={"is_default": is_default},
        )

    _ensure("Task", is_epic=False, is_default=True)
    _ensure("Epic", is_epic=True, is_default=False)


class ProjectFeatureAPIEndpoint(BaseAPIView):
    """Get / update a project's feature flags (work-item-types toggle)."""

    permission_classes = [ProjectMemberPermission]

    def get(self, request, slug, project_id):
        project = Project.objects.get(workspace__slug=slug, pk=project_id)
        return Response(_feature_payload(project), status=status.HTTP_200_OK)

    def patch(self, request, slug, project_id):
        project = Project.objects.get(workspace__slug=slug, pk=project_id)
        was_enabled = bool(project.is_issue_type_enabled)
        changed = []
        for feat, field in PROJECT_FEATURE_MAP.items():
            if feat in request.data:
                setattr(project, field, bool(request.data[feat]))
                changed.append(field)
        if changed:
            project.save(update_fields=changed + ["updated_at"])
        # Auto-create Task + Epic on the enable transition.
        if not was_enabled and project.is_issue_type_enabled:
            _ensure_default_types(project)
        return Response(_feature_payload(project), status=status.HTTP_200_OK)


class WorkItemTypeListCreateAPIEndpoint(BaseAPIView):
    """List / create work item types for a project."""

    serializer_class = WorkItemTypeSerializer
    model = IssueType
    permission_classes = [ProjectMemberPermission]
    use_read_replica = True

    def get_queryset(self):
        return (
            IssueType.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project_issue_types__project_id=self.kwargs.get("project_id"))
            .filter(
                project_issue_types__project__project_projectmember__member=self.request.user,
                project_issue_types__project__project_projectmember__is_active=True,
            )
            .select_related("workspace")
            .distinct()
            .order_by("level", "-created_at")
        )

    def get(self, request, slug, project_id):
        types = self.get_queryset()
        return Response(WorkItemTypeSerializer(types, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, slug, project_id):
        project = Project.objects.get(workspace__slug=slug, pk=project_id)
        # External-id dedup (integration safety), mirrors the Label endpoint.
        ext_id = request.data.get("external_id")
        ext_src = request.data.get("external_source")
        if ext_id and ext_src:
            existing = IssueType.objects.filter(
                workspace_id=project.workspace_id,
                project_issue_types__project_id=project_id,
                external_source=ext_src,
                external_id=ext_id,
            ).first()
            if existing:
                return Response(
                    {
                        "error": "Work item type with the same external id and source already exists",
                        "id": str(existing.id),
                    },
                    status=status.HTTP_409_CONFLICT,
                )
        serializer = WorkItemTypeCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            issue_type = serializer.save(workspace_id=project.workspace_id)
        except IntegrityError:
            return Response({"error": "The payload is not valid"}, status=status.HTTP_400_BAD_REQUEST)
        ProjectIssueType.objects.get_or_create(
            project_id=project_id,
            issue_type=issue_type,
            defaults={"is_default": bool(request.data.get("is_default", False))},
        )
        return Response(WorkItemTypeSerializer(issue_type).data, status=status.HTTP_201_CREATED)


class WorkItemTypeDetailAPIEndpoint(BaseAPIView):
    """Retrieve / update / delete a single work item type."""

    serializer_class = WorkItemTypeSerializer
    model = IssueType
    permission_classes = [ProjectMemberPermission]

    def _get_object(self, slug, project_id, pk):
        return IssueType.objects.filter(
            workspace__slug=slug,
            project_issue_types__project_id=project_id,
        ).distinct().get(pk=pk)

    def get(self, request, slug, project_id, pk):
        issue_type = self._get_object(slug, project_id, pk)
        return Response(WorkItemTypeSerializer(issue_type).data, status=status.HTTP_200_OK)

    def patch(self, request, slug, project_id, pk):
        issue_type = self._get_object(slug, project_id, pk)
        serializer = WorkItemTypeCreateUpdateSerializer(issue_type, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(WorkItemTypeSerializer(issue_type).data, status=status.HTTP_200_OK)

    def delete(self, request, slug, project_id, pk):
        issue_type = self._get_object(slug, project_id, pk)
        if issue_type.is_default:
            return Response(
                {"error": "The default work item type cannot be deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        issue_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
