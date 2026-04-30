# Blue-Green Deployment

Apply both environments:

```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/secret.yaml
kubectl apply -f k8s/blue-green/
```

Promote green:

```bash
kubectl -n aceest patch service aceest-blue-green \
  -p '{"spec":{"selector":{"app":"aceest-fitness","color":"green"}}}'
```

Rollback to blue:

```bash
kubectl -n aceest patch service aceest-blue-green \
  -p '{"spec":{"selector":{"app":"aceest-fitness","color":"blue"}}}'
```
