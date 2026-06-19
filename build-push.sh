#!/bin/bash
set -e
cd /tmp/plane-build
export DOCKER_BUILDKIT=1
REG=registry.lab.lumnus.net/staging/lumnus
REL=lumnus-2026-06-19
echo "=== BUILD START $(date -u) ==="
build() {
  local name=$1 ctx=$2 df=$3
  echo ">>> $name ($(date -u))"
  docker build --build-arg DOCKER_BUILDKIT=1 -t $REG/plane-$name:$REL -f "$df" "$ctx" \
    && docker push $REG/plane-$name:$REL && echo "<<< $name DONE $(date -u)"
}
build backend  ./apps/api  ./apps/api/Dockerfile.api
build frontend .           ./apps/web/Dockerfile.web
build space    .           ./apps/space/Dockerfile.space
build admin    .           ./apps/admin/Dockerfile.admin
build live     .           ./apps/live/Dockerfile.live
echo "=== BUILD ALL DONE $(date -u) ==="
