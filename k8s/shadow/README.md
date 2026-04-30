# Shadow Deployment

The shadow service is internal-only. It receives copied or synthetic traffic while users continue to use the stable service.

Send a health-check request from inside the cluster:

```bash
kubectl -n aceest run shadow-probe --rm -it --restart=Never \
  --image=curlimages/curl -- http://aceest-shadow/health
```

Rollback:

```bash
kubectl -n aceest scale deployment aceest-shadow --replicas=0
```
