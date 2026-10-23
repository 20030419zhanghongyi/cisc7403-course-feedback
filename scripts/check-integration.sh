#!/bin/sh
# Run from any directory; read-only preflight for the full three-service draft.
set -eu
cd "$(dirname "$0")/.."
missing=0
for file in feedback/Dockerfile database/init.sql dashboard/Dockerfile .env; do
    if [ ! -f "$file" ]; then
        printf 'Missing required file: %s\n' "$file" >&2
        missing=1
    fi
done
if [ "$missing" -ne 0 ]; then
    printf 'Integration is not ready. Use compose.dev.yml for independent dashboard development.\n' >&2
    exit 1
fi
docker compose -f docker-compose.yml config --quiet
printf 'Required files and Compose syntax checked. Full build and runtime still need verification.\n'
