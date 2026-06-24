#!/usr/bin/env bash
# run.sh
#
# run and reload (dev mode)

docker compose up -d
watchfiles --ignore-paths ./services,./logs "python -m agent" .
