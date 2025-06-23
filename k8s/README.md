# Kubernetes Deployment for Google Chat MCP Server

This directory contains Kubernetes manifests for deploying the Google Chat MCP Server to the pue-madrid cluster in the qry namespace.

## Prerequisites

1. **GCP Authentication**: Ensure you're authenticated with GCP
   ```bash
   gcloud auth login
   gcloud config set project pue-madrid
   ```

2. **Kubernetes Context**: Set the correct kubectl context
   ```bash
   kubectl config get-contexts
   kubectl config use-context pue-madrid
   ```

3. **Service Account Key**: Have the Google Chat service account JSON key file ready

## Deployment Steps

### 1. Create the Secret with Service Account Credentials

```bash
# Create the secret from your service account key file
kubectl create secret generic google-chat-mcp-credentials \
  --from-file=google-chat-mcp-server-key.json=./credentials/google-chat-mcp-server-key.json \
  --namespace=qry

# Verify the secret was created
kubectl get secrets -n qry | grep google-chat-mcp
```

### 2. Deploy the Application

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/networkpolicy.yaml
```

### 3. Verify Deployment

```bash
# Check deployment status
kubectl get deployments -n qry google-chat-mcp-server

# Check pods
kubectl get pods -n qry -l app=google-chat-mcp-server

# Check service
kubectl get svc -n qry google-chat-mcp-server

# View logs
kubectl logs -n qry -l app=google-chat-mcp-server --tail=50
```

### 4. Test Connectivity

```bash
# Port forward to test locally
kubectl port-forward -n qry svc/google-chat-mcp-server 8004:8004

# Test MCP server (in another terminal)
curl -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8004/mcp \
     -d '{"jsonrpc":"2.0","id":"health","method":"ping","params":{}}'
```

## Configuration

### Environment Variables (ConfigMap)

- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `GOOGLE_CHAT_DEFAULT_SPACE`: Default space for operations (optional)

### Resources

- **Requests**: 128Mi memory, 100m CPU
- **Limits**: 512Mi memory, 500m CPU
- **Replicas**: 2 for high availability

### Security

- **Non-root user**: Runs as user ID 1000
- **Read-only filesystem**: Enhanced security
- **Network policies**: Restricts traffic to necessary ports
- **Secret mounting**: Service account key mounted securely

## Integration with Qry Backend

The MCP server will be accessible within the cluster at:
- **Internal URL**: `http://google-chat-mcp-server.qry.svc.cluster.local:8004/mcp`
- **Service**: `google-chat-mcp-server:8004`

Update your Qry MCP configuration to use:
```json
{
  "name": "google_chat_mcp_server",
  "endpoint": "http://google-chat-mcp-server.qry.svc.cluster.local:8004/mcp",
  "transport_type": "http",
  "enabled": true,
  "auth_type": "none"
}
```

## Troubleshooting

### Pod Issues
```bash
# Describe pod for events
kubectl describe pod -n qry -l app=google-chat-mcp-server

# Check logs
kubectl logs -n qry -l app=google-chat-mcp-server --previous
```

### Service Issues
```bash
# Check endpoints
kubectl get endpoints -n qry google-chat-mcp-server

# Test service connectivity from another pod
kubectl run -it --rm debug --image=busybox --restart=Never -n qry -- sh
# wget -qO- http://google-chat-mcp-server:8004/mcp
```

### Secret Issues
```bash
# Verify secret exists and has correct data
kubectl get secret google-chat-mcp-credentials -n qry -o yaml

# Check if secret is properly mounted
kubectl exec -n qry deployment/google-chat-mcp-server -- ls -la /app/credentials/
```

## Scaling

```bash
# Scale deployment
kubectl scale deployment google-chat-mcp-server --replicas=3 -n qry

# Horizontal Pod Autoscaler (optional)
kubectl autoscale deployment google-chat-mcp-server --cpu-percent=70 --min=2 --max=5 -n qry
```

## Updates

```bash
# Update image (after building new version)
kubectl set image deployment/google-chat-mcp-server \
  google-chat-mcp-server=europe-southwest1-docker.pkg.dev/pue-madrid/puedata/google-chat-mcp-server:latest \
  -n qry

# Check rollout status
kubectl rollout status deployment/google-chat-mcp-server -n qry

# Rollback if needed
kubectl rollout undo deployment/google-chat-mcp-server -n qry
```