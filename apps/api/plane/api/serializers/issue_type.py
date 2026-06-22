# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# Lumnus fork addition: public-API serializers for work item types (issue types).
# CE ships the IssueType model but not the public-API surface (it lived in the
# closed ee/ package). These expose it for PAT-authenticated REST + MCP use.

# Third party imports
from rest_framework import serializers

# Module imports
from .base import BaseSerializer
from plane.db.models import IssueType


class WorkItemTypeCreateUpdateSerializer(BaseSerializer):
    """Writable serializer for creating/updating a work item type."""

    class Meta:
        model = IssueType
        fields = [
            "name",
            "description",
            "logo_props",
            "is_epic",
            "is_default",
            "is_active",
            "level",
            "external_source",
            "external_id",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class WorkItemTypeSerializer(BaseSerializer):
    """Full serializer for a work item type. `project_ids` is derived from the
    ProjectIssueType link rows so the shape matches the Plane SDK contract."""

    project_ids = serializers.SerializerMethodField()

    class Meta:
        model = IssueType
        fields = "__all__"
        read_only_fields = [
            "id",
            "workspace",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_project_ids(self, obj):
        # Annotated in the queryset where available; fall back to a relation read.
        if hasattr(obj, "project_ids") and isinstance(obj.project_ids, list):
            return [str(pid) for pid in obj.project_ids if pid]
        return [
            str(pit.project_id)
            for pit in obj.project_issue_types.all()
            if pit.project_id
        ]
