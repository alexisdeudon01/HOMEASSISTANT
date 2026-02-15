#!/bin/bash

# Script to export environment variables from .env file
# This script is sourced by Docker containers to load environment variables

set -a
if [ -f "/app/.env" ]; then
    echo "Loading environment variables from /app/.env"
    source /app/.env
elif [ -f "/app/../.env" ]; then
    echo "Loading environment variables from /app/../.env"
    source /app/../.env
elif [ -f "/.env" ]; then
    echo "Loading environment variables from /.env"
    source /.env
else
    echo "Warning: No .env file found. Using default environment variables."
fi
set +a

# Export all variables for subprocesses
export $(cut -d= -f1 /proc/self/environ | grep -v "^$" | xargs) 2>/dev/null || true
