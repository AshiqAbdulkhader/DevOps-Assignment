# Kubernetes Deployment Strategies

Target cluster: Azure Kubernetes Service.

Container image:

```text
docker.io/ashiqabdulkhader/aceest-fitness:v1
```

Folders:

- `base/`: normal production deployment with Kubernetes rolling update and a public LoadBalancer service.
- `rolling/`: commands for Kubernetes rolling update and rollback.
- `blue-green/`: blue and green deployments with service-selector traffic switching.
- `canary/`: stable and canary deployments behind one service.
- `shadow/`: internal-only shadow deployment for copied/synthetic traffic.
- `ab-testing/`: variant A and B deployments exposed separately for review.

Apply base:

```bash
kubectl apply -f k8s/base/
kubectl -n aceest rollout status deployment/aceest-fitness
kubectl -n aceest get service aceest-fitness
```

Get the public endpoint:

```bash
kubectl -n aceest get service aceest-fitness \
  -o jsonpath='http://{.status.loadBalancer.ingress[0].ip}{"\n"}'
```
