# Rolling Update

Kubernetes `Deployment` rolling updates are configured in `../base/deployment.yaml`.

Deploy version `v2`:

```bash
kubectl -n aceest set image deployment/aceest-fitness \
  aceest-fitness=docker.io/ashiqabdulkhader/aceest-fitness:v2
kubectl -n aceest rollout status deployment/aceest-fitness
```

Rollback to the last stable ReplicaSet:

```bash
kubectl -n aceest rollout undo deployment/aceest-fitness
kubectl -n aceest rollout status deployment/aceest-fitness
```
