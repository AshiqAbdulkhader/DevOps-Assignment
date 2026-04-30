# ACEest Fitness CI/CD Report

## Architecture Overview

The Flask application is packaged as a multi-stage Docker image. The `ci-test` stage installs test dependencies and runs `pytest`, while the `runtime` stage runs the app with Gunicorn as a non-root user on port `8000`.

Images are versioned in Docker Hub under `ashiqabdulkhader/aceest-fitness` with tags such as `v1`, `v2`, `stable`, and `latest`. The live deployment runs on Azure Kubernetes Service in resource group `rg-aceest-devops`, cluster `aks-aceest-devops`.

The non-Jenkins CI/CD path is implemented with GitHub Actions in `.github/workflows/cd-aks.yml`: build test image, run SonarQube scan, build/push Docker Hub image, authenticate to Azure using a service principal, and deploy to AKS with `kubectl`.

## Deployment Strategies

Rolling updates are handled by the base Kubernetes `Deployment` using `maxUnavailable: 0` and `maxSurge: 1`. Rollback is available with `kubectl rollout undo deployment/aceest-fitness`.

Blue-green deployment uses separate blue and green deployments. Traffic switches by patching the service selector from `color: blue` to `color: green`. Rollback is the reverse selector patch.

Canary deployment runs stable and canary deployments behind one service. Traffic percentage is controlled by replica counts. Rollback scales the canary deployment to zero.

Shadow deployment runs an internal-only shadow service for synthetic or copied traffic without exposing it to users. Rollback scales the shadow deployment to zero.

A/B testing exposes variant A and variant B as separate services, allowing reviewers to compare versions directly and promote the preferred version.

## Challenges And Mitigation

The first AKS rollout failed because the image was built on Apple Silicon as `linux/arm64`, while the AKS node pool required `linux/amd64`. This was fixed by rebuilding and pushing the image with Docker Buildx using `--platform linux/amd64`.

The first Kubernetes apply also hit a namespace timing race when applying a whole folder at once. The mitigation was to apply the namespace first, wait until it is Active, then apply the secret, deployment, and service.

## Automation Outcomes

Pytest passed inside the container build stage with `19 passed`. The Docker Hub image was pushed with versioned tags, and the AKS deployment completed successfully. The live health endpoint returned `{"status":"healthy"}`.

SonarQube was hosted locally using Docker at `http://localhost:9000`. The project key is `aceest-fitness`, and the local dashboard is available at `http://localhost:9000/dashboard?id=aceest-fitness`. The completed analysis returned quality gate status `OK`.
