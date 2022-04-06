#!/usr/bin/env bash

# Helper to maintain code duplication.
# SHOULD: Find a valid Typescript config such that
# the shared code can reside in a shared directory.
# Currently, importing dependencies that are only
# available in the subdirectories (e.g., in queue)
# but not at this higher shared level causes
# the deployment to fail.

cp queue/handler.ts database/handler.ts
cp queue/handler.ts storage/handler.ts
