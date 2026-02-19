# FluxCD Configuration for SLADK Application

This repository contains FluxCD manifests to deploy the SLADK application to a Kubernetes cluster.

## Overview

The configuration uses a **Kustomize** overlay structure with **Helm** for the application deployment. It follows the GitOps methodology where all Kubernetes resources are defined declaratively in this repository.

## Architecture

```
fluxcd/
├── gitrepository.yaml      # Defines the Git source
├── kustomization.yaml      # Root Kustomization pointing to apps/
├── apps/
│   ├── kustomization.yaml  # Apps-level Kustomization with ConfigMapGenerator
│   ├── defaults.yaml      # Default values for the Helm chart
│   ├── base/
│   │   ├── app.yaml       # Base HelmRelease definition
│   │   └── kustomization.yaml
│   └── overlays/
│       └── main/
│           ├── kustomization.yaml
│           └── patch.yaml  # Overlay patch for main environment
└── helm/
    └── sladk/
        ├── Chart.yaml
        ├── values.yaml    # Helm chart default values
        └── templates/     # Kubernetes templates (deployment, hpa)
```

## Components

### 1. GitRepository (`gitrepository.yaml`)
- **Source**: `https://github.com/rogerdipasquale/sladk-agents`
- **Branch**: `feature/main`
- **Namespace**: `flux-system`
- **Interval**: Syncs every 10 minutes

### 2. Root Kustomization (`kustomization.yaml`)
- **Path**: `/fluxcd/apps/`
- **Target Namespace**: `flux-system`
- **Prune**: Enabled (deletes resources removed from Git)
- **Wait**: Enabled (waits for resources to become ready)

### 3. Helm Chart (`helm/sladk/`)
- **Name**: `sladk`
- **Version**: `0.0.11`
- **Type**: Application

### 4. HelmRelease (`apps/base/app.yaml`)
- **Release Name**: `sladk`
- **Namespace**: `sladk`
- **Interval**: 10 minutes
- **Values Source**: ConfigMap generated from `defaults.yaml`

### 5. Overlay (`apps/overlays/main/`)
- **Name Suffix**: `-main`
- **Namespace**: `sladk`
- **Patch**: Overrides image tag to `initial`

## Application Configuration

### Default Values (`apps/defaults.yaml`)

| Parameter | Value |
|-----------|-------|
| Image Repository | `ghcr.io/rogerdipasquale/sladk-agents` |
| Image Tag | `initial` |
| Pull Policy | `Always` |
| Replica Count | 1 |
| Environment | `stage` |

### Resources

| Resource | Requests | Limits |
|----------|----------|--------|
| CPU | 400m | 1000m |
| Memory | 512M | 1024M |

### Probes

- **Startup Probe**: Checks for `app.py` process, fails if not running
- **Liveness Probe**: Checks for `app.py` process every 60s
- **Timeout**: 2s for liveness, 1s for startup

### HPA (Horizontal Pod Autoscaler)

- **Min Replicas**: 1
- **Max Replicas**: 1
- **CPU Target**: 90% utilization
- **Memory Target**: 90% utilization

### Secrets

- **Secret Reference**: `sladk-secrets`

## Secret Template

The application requires a secret named `sladk-secrets` in the `sladk` namespace. Create a file named `sladk-secrets.yaml` with the following template:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sladk-secrets
  namespace: sladk-agents
type: Opaque
stringData:
  # Add your secret keys and values here
  # Example:
  # API_KEY: your-api-key-here
  # .....
```

Apply the secret before deploying:

```bash
kubectl apply -f sladk-secrets.yaml
```

**Note:** For production, consider using external secrets operators (like ESO or SealedSecrets) to manage secrets securely through GitOps.

## Labels & Selectors

| Key | Value |
|-----|-------|
| `app` | `sladk-agent` |
| `purpose` | `ia` |
| `env` | `test` |

## Deployment Flow

1. **FluxCD** monitors the GitRepository (`sladk-repo`) at the `feature/main` branch
2. The root Kustomization syncs the `apps/` directory every 10 minutes
3. The apps Kustomization generates a ConfigMap (`common-sladk`) with default values
4. The base HelmRelease is applied, using the chart from `fluxcd/helm/sladk`
5. The main overlay applies a patch to override the image tag to `initial`
6. Helm installs/updates the `sladk-main-release` in the `sladk` namespace

## Usage

This configuration is typically deployed using FluxCD's CLI:

```bash
flux bootstrap git \
  --url=https://github.com/rogerdipasquale/sladk-agents \
  --branch=feature/main \
  --path=fluxcd
```

Or the resources can be applied manually:

```bash
kubectl apply -f fluxcd/gitrepository.yaml
kubectl apply -f fluxcd/kustomization.yaml
```

## Requirements

- Kubernetes cluster 1.20+
- FluxCD v2 (source.toolkit.fluxcd.io and kustomize.toolkit.fluxcd.io)
- Helm operator (helm.toolkit.fluxcd.io)

## Namespace

The application is deployed to the `sladk` namespace, which must exist before deployment:

```bash
kubectl create namespace sladk
```
