# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# Lumnus fork addition: public-API routes for work item types + project features.

from django.urls import path

from plane.api.views import (
    WorkspaceFeatureAPIEndpoint,
    ProjectFeatureAPIEndpoint,
    WorkItemTypeListCreateAPIEndpoint,
    WorkItemTypeDetailAPIEndpoint,
)


urlpatterns = [
    path(
        "workspaces/<str:slug>/features/",
        WorkspaceFeatureAPIEndpoint.as_view(http_method_names=["get", "patch"]),
        name="workspace-features",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/features/",
        ProjectFeatureAPIEndpoint.as_view(http_method_names=["get", "patch"]),
        name="project-features",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/work-item-types/",
        WorkItemTypeListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="work-item-types",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/work-item-types/<uuid:pk>/",
        WorkItemTypeDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="work-item-types",
    ),
]
