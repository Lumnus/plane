#!/bin/bash
set -e
cd /tmp/plane-build
export DOCKER_BUILDKIT=1
REG=registry.lab.lumnus.net/staging/lumnus
REL=lumnus-2026-06-19-oidc
echo "=== OIDC BUILD START $(date -u) ==="
echo ">>> backend ($(date -u))"
docker build --build-arg DOCKER_BUILDKIT=1 -t $REG/plane-backend:$REL -f ./apps/api/Dockerfile.api ./apps/api \
  && docker push $REG/plane-backend:$REL && echo "<<< backend DONE $(date -u)"
echo ">>> frontend/web ($(date -u))"
docker build --build-arg DOCKER_BUILDKIT=1 -t $REG/plane-frontend:$REL -f ./apps/web/Dockerfile.web . \
  && docker push $REG/plane-frontend:$REL && echo "<<< frontend DONE $(date -u)"
echo "=== OIDC BUILD ALL DONE $(date -u) ==="
