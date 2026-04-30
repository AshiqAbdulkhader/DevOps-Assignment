# A/B Testing

This simple assignment-friendly setup exposes variant A and variant B with separate services, so reviewers can test both versions directly.

Rollback variant B:

```bash
kubectl -n aceest scale deployment aceest-b --replicas=0
```

Promote B by repointing variant A traffic to B's image:

```bash
kubectl -n aceest set image deployment/aceest-a \
  aceest-fitness=docker.io/ashiqabdulkhader/aceest-fitness:v2
kubectl -n aceest rollout status deployment/aceest-a
```
