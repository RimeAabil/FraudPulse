#!/bin/bash

echo "Stopping all containers..."
docker-compose down -v

echo "Removing orphaned containers if any..."
docker-compose down --remove-orphans

echo "Rebuilding and starting clean..."
docker-compose up --build -d

echo "Reset complete. Check logs with: docker-compose logs -f"
