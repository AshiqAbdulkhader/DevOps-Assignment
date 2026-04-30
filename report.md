# ACEest Fitness DevOps CI/CD Report

## Project And Deployment Details

This project containerizes and deploys the ACEest Fitness Flask application using Docker, Docker Hub, GitHub Actions, SonarQube, and Azure Kubernetes Service.

GitHub repository: `https://github.com/AshiqAbdulkhader/DevOps-Assignment`

Docker Hub image repository: `docker.io/ashiqabdulkhader/aceest-fitness`

Published image tags: `v1`, `v2`, `stable`, and `latest`

Azure resource group: `rg-aceest-devops`

AKS cluster: `aks-aceest-devops`

Live application endpoint: `http://4.188.65.141`

Health endpoint: `http://4.188.65.141/health`

Local SonarQube dashboard: `http://localhost:9000/dashboard?id=aceest-fitness`

## Architecture Overview

The application follows a simple cloud-native delivery architecture. Source code is stored in GitHub, container images are built from the repository Dockerfile, versioned images are pushed to Docker Hub, and Kubernetes manifests deploy the selected image tag to Azure Kubernetes Service.

The Flask app is exposed through Gunicorn on container port `8000`. Kubernetes publishes the service using an Azure LoadBalancer, which creates the public endpoint. The `/health` route is used by Docker and Kubernetes health checks to confirm that the application is responding correctly.

The Dockerfile uses a multi-stage build:

- `builder` installs production dependencies into a virtual environment.
- `ci-test` installs full test dependencies and runs `pytest` inside the container build.
- `runtime` creates the production image with Gunicorn, a non-root Linux user, and health checks.

This separates testing concerns from the production runtime image and keeps the final image smaller and safer.

## CI Pipeline With GitHub Actions

The continuous integration workflow is defined in `.github/workflows/ci.yml`. It runs automatically on pushes and pull requests to `main` or `master`.

The CI pipeline has three main jobs:

1. `build-and-lint`

This job checks out the repository, installs Python 3.12 dependencies, and runs byte-compilation against the application and test files. This catches syntax errors early before Docker image work starts.

2. `docker-image`

This job builds the production Docker runtime image using Docker Buildx. It does not push the image, but it validates that the runtime Dockerfile stage can be built successfully.

3. `test-in-docker`

This job builds the Dockerfile `ci-test` stage. During that image build, `pytest -q` runs inside the container. This confirms that tests pass in a containerized environment rather than only on the developer machine.

The workflow also uses GitHub Actions concurrency, so newer commits cancel older in-progress workflow runs on the same branch.

## CD Pipeline To AKS

The continuous delivery workflow is defined in `.github/workflows/cd-aks.yml`. It is currently configured as a manual `workflow_dispatch` pipeline so a specific image tag can be selected during deployment.

The CD workflow performs these steps:

1. Checkout source code from GitHub.
2. Build the Docker `ci-test` stage, which runs the Pytest suite inside the container.
3. Run the SonarQube scan using the project configuration in `sonar-project.properties`.
4. Authenticate to Docker Hub using GitHub repository secrets.
5. Build and push the production runtime image for `linux/amd64`, which matches the AKS node architecture.
6. Authenticate to Azure using a service principal stored in GitHub secrets.
7. Fetch AKS credentials with `az aks get-credentials`.
8. Apply the Kubernetes namespace, secret, deployment, and service manifests.
9. Update the Kubernetes deployment image tag.
10. Wait for the rollout to complete using `kubectl rollout status`.

The Azure service principal is used for deployment automation, which avoids using a personal Azure login in the pipeline.

## Container Registry And Image Versioning

Docker Hub is used as the central container registry. The main image repository is:

`docker.io/ashiqabdulkhader/aceest-fitness`

The image was pushed with multiple tags:

- `v1`: stable version used by the live AKS deployment.
- `v2`: second version tag for canary, blue-green, and A/B testing examples.
- `stable`: alias for the current stable release.
- `latest`: convenience tag for the most recent build.

Because the development machine uses Apple Silicon, Docker initially built an ARM image. The AKS node pool uses AMD64, so the final image was rebuilt and pushed with Docker Buildx using the `linux/amd64` platform.

## Kubernetes Deployment

The base Kubernetes deployment is stored in `k8s/base/`. It contains:

- `namespace.yaml`
- `secret.yaml`
- `deployment.yaml`
- `service.yaml`

The deployment runs two replicas of the Flask application. It uses readiness and liveness probes against `/health`. The service type is `LoadBalancer`, which Azure maps to the public application IP.

Current live endpoint:

`http://4.188.65.141`

Verified health response:

`{"status":"healthy"}`

The application can be redeployed with:

```bash
kubectl apply -f k8s/base/
kubectl -n aceest rollout status deployment/aceest-fitness
```

Rollback is available with:

```bash
kubectl -n aceest rollout undo deployment/aceest-fitness
```

## Deployment Strategies

The repository includes manifests and instructions for several deployment strategies under `k8s/`.

Rolling update is implemented through the base Kubernetes `Deployment`. It uses `maxUnavailable: 0` and `maxSurge: 1`, so new pods become ready before old pods are removed.

Blue-green deployment is stored in `k8s/blue-green/`. It creates separate blue and green deployments. Traffic is switched by changing the service selector from `color: blue` to `color: green`. Rollback is done by switching the selector back.

Canary release is stored in `k8s/canary/`. It runs stable and canary deployments behind one service. Traffic distribution is controlled by changing replica counts, for example four stable pods and one canary pod.

Shadow deployment is stored in `k8s/shadow/`. The shadow version runs behind an internal ClusterIP service. It can receive synthetic or copied traffic without affecting live users.

A/B testing is stored in `k8s/ab-testing/`. Variant A and variant B are deployed as separate services so reviewers can compare versions directly.

## Automated Testing And SonarQube

Automated tests are written with Pytest under the `tests/` directory. The Dockerfile `ci-test` stage runs these tests during the image build. The verified result was:

`19 passed`

SonarQube was hosted locally with Docker:

```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:lts-community
```

The project is configured through `sonar-project.properties` with project key `aceest-fitness`. The completed local SonarQube scan returned quality gate status:

`OK`

Dashboard:

`http://localhost:9000/dashboard?id=aceest-fitness`

## Key Automation Outcomes

The project now has a complete non-Jenkins DevOps path:

- CI validation using GitHub Actions.
- Docker image build validation.
- Pytest execution inside a containerized build stage.
- Docker Hub image publishing with versioned tags.
- AKS deployment using Kubernetes manifests.
- Service-principal based Azure deployment.
- SonarQube static analysis with quality gate validation.
- Multiple Kubernetes deployment strategies with rollback instructions.

The live deployment is currently running in AKS with two healthy pods behind an Azure LoadBalancer.

## Challenges And Mitigation

The first AKS rollout failed because the Docker image was built on Apple Silicon as `linux/arm64`, while the AKS node pool required `linux/amd64`. This was fixed by rebuilding and pushing the image with Docker Buildx using the `linux/amd64` platform.

The first Kubernetes apply also hit a namespace timing race when applying the whole base folder at once. The namespace was created, but the deployment was submitted before the API server fully recognized the namespace. The mitigation was to apply the namespace first, wait until it became Active, and then apply the secret, deployment, and service.

Docker Hub authentication briefly rejected a public image pull for SonarQube because of stale local credentials. Logging out allowed Docker to pull the public SonarQube image anonymously.

Local SonarQube works well for assignment evidence and screenshots, but GitHub Actions cannot access `localhost` on the developer laptop. For fully automated cloud-based quality gates, SonarCloud or a publicly reachable SonarQube server would be required.
