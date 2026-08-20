# spotify-tracker Helm chart

Deploys the Spotify Playlist Tracker backend + Postgres + Traefik TLS on the
home-cluster (Pi 5 / Pi 4, Longhorn, cert-manager `home-ca`).

## How Helm works (30-second tutorial)

Helm is a **templated package** for Kubernetes.

- `Chart.yaml` — package metadata (name, version).
- `values.yaml` — defaults (image, host, storage). Override at install time.
- `templates/*.yaml` — Kubernetes manifests with `{{ .Values.* }}` placeholders. `helm template` renders them to plain YAML.
- **Release** — an installed instance of the chart in a namespace. Same chart can be installed twice with different values/releases.

Flow:

```
values.yaml (defaults) + your overrides → helm template → kubectl apply
```

Helm tracks what it installed, so `helm upgrade` diffs the new render against
the last release and `helm rollback` reverts.

## Install (manual helm)

```bash
# From the tracker repo root
helm lint chart
helm template spotify-tracker chart --values chart/values.yaml | less  # dry-run

# Create secrets outside git (never commit client secrets)
kubectl create namespace spotify-tracker --dry-run=client -o yaml | kubectl apply -f -
kubectl -n spotify-tracker create secret generic spotify-tracker-secrets \
  --from-literal=SPOTIPY_CLIENT_ID=YOUR_ID \
  --from-literal=SPOTIPY_CLIENT_SECRET=YOUR_SECRET \
  --from-literal=FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Install with the external secret
helm upgrade --install spotify-tracker ./chart \
  -n spotify-tracker --create-namespace \
  --set secrets.existingSecret=spotify-tracker-secrets \
  --set postgresql.auth.password=$(openssl rand -hex 16) \
  --set ingress.host=spotify.192.168.0.205.nip.io

# Or let the chart generate the secret (demo only — password changes on each helm template due to randAlphaNum)
# Prefer existingSecret for stable DATABASE_URL.
```

Useful commands:

```bash
helm upgrade --install spotify-tracker ./chart -n spotify-tracker -f my-values.yaml
helm rollback spotify-tracker 1 -n spotify-tracker
helm uninstall spotify-tracker -n spotify-tracker   # leaves PVCs by default
helm get values spotify-tracker -n spotify-tracker
```

## Install (GitOps via ArgoCD — the cluster way)

The cluster does not use `helm install` by hand. ArgoCD syncs git.

1. The chart lives in this repo at `chart/`.
2. `home-cluster/infra/spotify-tracker/application.yaml` points ArgoCD at
   `repoURL: https://github.com/ArthurTolley/spotify-playlist-tracker.git`,
   `path: chart` with inline `helm.values`. ArgoCD's repo-server runs
   `helm template` on every sync (compare interval ~3 min).

To deploy:

```bash
# 1) create secrets in the cluster once (outside git)
ssh ubuntu@192.168.0.15 'kubectl create namespace spotify-tracker --dry-run=client -o yaml | kubectl apply -f -'
ssh ubuntu@192.168.0.15 'kubectl -n spotify-tracker create secret generic spotify-tracker-secrets \
  --from-literal=SPOTIPY_CLIENT_ID=... \
  --from-literal=SPOTIPY_CLIENT_SECRET=... \
  --from-literal=FLASK_SECRET_KEY=$(openssl rand -hex 32)'

# 2) push home-cluster with the new Application — ArgoCD auto-syncs
cd home-cluster && git add infra/spotify-tracker && git commit -m "add spotify-tracker" && git push
# ArgoCD will create the release; watch:
ssh ubuntu@192.168.0.15 'kubectl -n argocd get app spotify-tracker'
ssh ubuntu@192.168.0.15 'kubectl -n spotify-tracker get pods'
```

Secrets are **not** in git. The chart's `secrets.existingSecret` tells it to
reuse the externally-created Secret (so ArgoCD does not overwrite it or show
the placeholder diff).

## Database safety

This chart is **non-destructive**:

- No `pg_restore`, no init SQL, no `DROP`. The backend entrypoint runs
  `SKIP_SCHEDULER=1 python init_db.py` → `db.create_all()` which only
  `CREATE TABLE IF NOT EXISTS`.
- Postgres PVC uses the cluster default `longhorn` StorageClass
  (`ReadWriteOnce`, 2 replicas, `Retain` reclaim). Deleting the Helm release
  does **not** delete the PVC — data survives `helm uninstall`.
- First install starts with an **empty** DB (correct for production). To
  seed from an existing dump, run a one-off manual restore — never an
  automatic initContainer:

```bash
kubectl -n spotify-tracker exec deploy/spotify-tracker-postgres -- \
  pg_restore --no-owner --no-privileges -d spotify_tracker /path/to/dump
```

## Configuration

| Value | Default | Notes |
|-------|---------|-------|
| `image.repository` | `ghcr.io/...-backend` | Push multi-arch (amd64+arm64) — see CI notes below |
| `config.spotifyRedirectUri` | `https://spotify..../callback` | Must match Spotify Dashboard |
| `config.corsOrigins` | nip.io + GitHub Pages | Comma-separated |
| `ingress.host` | `spotify.192.168.0.205.nip.io` | Traefik host rule + cert-manager dnsName |
| `postgresql.enabled` | `true` | Set `false` + `secrets.databaseUrl` for external DB |
| `postgresql.storage.size` | `5Gi` | Longhorn PVC |
| `affinity` | pinned to `node1,node2` | Pi workers; set `{}` to schedule anywhere |

## Raspberry Pi notes

- Image must be **multi-arch**. The GitHub workflow now builds with
  `docker/build-push-action` + `platforms: linux/amd64,linux/arm64`. A
  single-arch amd64 image will `CrashLoopBackOff` on the Pi.
- `python:3.11-slim` is already multi-arch; no Dockerfile change needed.
