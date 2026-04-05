#!/bin/bash

# Parse arguments
PROFILE=${1:-all}

echo "Stopping containers..."
if [ "$PROFILE" == "full" ]; then
    docker compose -f docker-compose.yml -f docker-compose.mlops.yml -f docker-compose.observability.yml down -v
elif [ "$PROFILE" == "mlops" ]; then
    docker compose -f docker-compose.yml -f docker-compose.mlops.yml down -v
else
    docker compose down -v
fi

echo "Removing orphaned containers if any..."
docker compose down --remove-orphans

echo "Cleaning local checkpoint directories..."
rm -rf ./spark_checkpoints/*

echo "Reset complete. To build and start again:"
if [ "$PROFILE" == "full" ]; then
    echo "  make up-full"
elif [ "$PROFILE" == "mlops" ]; then
    echo "  make up-mlops"
else
    echo "  make up"
fi
