#!/bin/bash

set -e  # Exit on error

# Change to the project directory
cd /home/shuence/ai

# Pull latest changes from git
echo "Pulling latest changes from git..."
git pull

# Stop existing containers
echo "Stopping existing containers..."
docker compose down

# Build containers
echo "Building containers..."
docker compose build

# Start containers in detached mode
echo "Starting containers..."
docker compose up -d

echo "Deployment complete!"

