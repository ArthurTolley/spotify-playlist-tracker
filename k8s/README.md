# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Spotify Playlist Tracker backend.

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured to access your cluster
- Docker registry access (Docker Hub, GitHub Container Registry, etc.)

## Quick Start

### 1. Build and Push Docker Image

```bash
# From the backend directory
cd backend

# Build the Docker image
docker build -t your-registry/spotify-tracker-backend:latest .

# Push to your registry
docker push your-registry/spotify-tracker-backend:latest
```

### 2. Update Configuration

Edit the following files with your actual values:

**k8s/secret.yaml:**
- Update `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` with your Spotify API credentials
- Update `FLASK_SECRET_KEY` with a secure random string
- Update `DATABASE_URL` with your PostgreSQL connection string

**k8s/configmap.yaml:**
- Update `SPOTIPY_REDIRECT_URI` with your Cloudflare tunnel URL
- Update `CORS_ORIGINS` with your GitHub Pages URL

**k8s/deployment.yaml:**
- Update the `image` field with your Docker image registry path

**k8s/postgres.yaml:**
- Update `POSTGRES_PASSWORD` in the postgres-secret

### 3. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -k k8s/

# Or apply individual files
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 4. Verify Deployment

```bash
# Check namespace
kubectl get namespace spotify-tracker

# Check all resources
kubectl get all -n spotify-tracker

# Check pod logs
kubectl logs -n spotify-tracker -l app=spotify-tracker,component=backend

# Check database connection
kubectl exec -it -n spotify-tracker deployment/postgres -- psql -U spotifytracker -d spotify_tracker
```

### 5. Troubleshooting

```bash
# Describe pod for events
kubectl describe pod -n spotify-tracker -l component=backend

# Get pod logs
kubectl logs -n spotify-tracker -l component=backend --tail=100

# Access pod shell
kubectl exec -it -n spotify-tracker deployment/spotify-tracker-backend -- /bin/bash

# Port forward for local testing
kubectl port-forward -n spotify-tracker service/spotify-tracker-backend 8888:8888
```

## Creating Secrets Securely

Instead of storing secrets in YAML files, create them using kubectl:

```bash
kubectl create secret generic spotify-tracker-secrets \
  --from-literal=SPOTIPY_CLIENT_ID=your_client_id \
  --from-literal=SPOTIPY_CLIENT_SECRET=your_client_secret \
  --from-literal=FLASK_SECRET_KEY=your_flask_secret \
  --from-literal=DATABASE_URL=postgresql://user:pass@postgres-service:5432/spotify_tracker \
  -n spotify-tracker

kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=spotifytracker \
  --from-literal=POSTGRES_PASSWORD=secure_password \
  --from-literal=POSTGRES_DB=spotify_tracker \
  -n spotify-tracker
```

## Updating the Deployment

```bash
# Update image
kubectl set image deployment/spotify-tracker-backend \
  backend=your-registry/spotify-tracker-backend:new-tag \
  -n spotify-tracker

# Restart pods
kubectl rollout restart deployment/spotify-tracker-backend -n spotify-tracker

# Check rollout status
kubectl rollout status deployment/spotify-tracker-backend -n spotify-tracker
```

## Cleanup

```bash
# Delete all resources
kubectl delete -k k8s/

# Or delete namespace (removes everything)
kubectl delete namespace spotify-tracker
```
