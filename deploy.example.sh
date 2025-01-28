#!/bin/bash

# Define variables
LOGFILE="$(pwd)/deploy.log"
REPO_DIR="$(pwd)"  # The repository directory is the current working directory
DOCKER_COMPOSE_FILE="docker-compose.yaml"

# Log the start of the deployment
echo "Deployment started at $(date)" >> "$LOGFILE"

# Navigate to the repository directory
cd "$REPO_DIR" || { echo "Failed to change directory" >> "$LOGFILE"; exit 1; }

# Pull the latest changes from the main branch
{
    git fetch origin main && 
    git reset --hard origin/main && 
    git clean -fd
} >> "$LOGFILE" 2>&1 || { echo "Git operations failed" >> "$LOGFILE"; exit 1; }

# Stop and remove existing containers and project-specific images
{
    docker compose down --rmi all
} >> "$LOGFILE" 2>&1 || { echo "Failed to stop and remove containers and images" >> "$LOGFILE"; exit 1; }

# Build and start the containers using Docker Compose
{
    docker compose -f "$DOCKER_COMPOSE_FILE" up --build -d
} >> "$LOGFILE" 2>&1 || { echo "Failed to build and start containers" >> "$LOGFILE"; exit 1; }

# Log the completion of the deployment
echo "Deployment completed at $(date)" >> "$LOGFILE"
