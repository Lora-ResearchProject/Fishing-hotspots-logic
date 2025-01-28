#!/bin/bash

# Define variables
LOGFILE="$(pwd)/deploy.log"
REPO_DIR="$(pwd)"  # The repository directory is the current working directory
DOCKERFILE="Dockerfile"
IMAGE_NAME="fishing-hotspots-api"
CONTAINER_NAME="fishing-hotspots-api-container"

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
    docker stop "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    docker rmi "$IMAGE_NAME" || true
} >> "$LOGFILE" 2>&1 || { echo "Failed to stop and remove containers and images" >> "$LOGFILE"; exit 1; }

# Build the image using the Dockerfile
{
    docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" .
} >> "$LOGFILE" 2>&1 || { echo "Failed to build the Docker image" >> "$LOGFILE"; exit 1; }

# Run the container from the built image
{
    docker run -d --name "$CONTAINER_NAME" "$IMAGE_NAME"
} >> "$LOGFILE" 2>&1 || { echo "Failed to start the Docker container" >> "$LOGFILE"; exit 1; }

# Log the completion of the deployment
echo "Deployment completed at $(date)" >> "$LOGFILE"
