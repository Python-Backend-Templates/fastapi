#!/bin/bash

# if any of the commands fails for any reason, the entire script fails
set -o errexit

# fail exit if one of pipe command fails
set -o pipefail

# exits if any of variables is not set
set -o nounset

echo "[MIGRATE]"
alembic upgrade head

echo "[RUN SERVER]"
uvicorn main:app --host 0.0.0.0 --port $ASGI_PORT --reload
