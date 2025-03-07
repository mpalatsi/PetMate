#!/bin/bash

# Script to rebuild and restart the Docker containers

echo "Stopping existing containers..."
docker-compose down

echo "Rebuilding the web container (no cache)..."
docker-compose build --no-cache web

echo "Starting containers..."
docker-compose up -d

echo "Containers started. Showing logs..."
docker-compose logs -f 