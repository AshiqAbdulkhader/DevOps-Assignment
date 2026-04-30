# Canary Release

This setup sends about 20% of traffic to `v2`: one canary pod and four stable pods.

Increase canary traffic:

```bash
kubectl -n aceest scale deployment aceest-canary --replicas=2
kubectl -n aceest scale deployment aceest-stable --replicas=3
```

Rollback:

```bash
kubectl -n aceest scale deployment aceest-canary --replicas=0
kubectl -n aceest scale deployment aceest-stable --replicas=4
```
