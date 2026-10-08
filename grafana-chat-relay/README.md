# Grafana Alert → Google Chat Relay

Forwards Grafana Webhook contact point notifications to Google Chat (`spaces/AAQAD9vqp48`, "Bazel CI Health Check") as the **Bazel CI Bot** Chat app (`bazel-untrusted`).

## How it works

1. **Inbound auth**: Grafana sends `Authorization: Bearer <secret>`. The function compares the header against `WEBHOOK_SECRET` (mounted from Secret Manager) using `hmac.compare_digest`.
2. **Keyless bot auth**: The Cloud Run service runs as `bazel-ci-skill-reader@bazel-untrusted.iam.gserviceaccount.com` and requests an OAuth2 access token with scope `https://www.googleapis.com/auth/chat.bot` directly from the Cloud Run container metadata server (`?scopes=https://www.googleapis.com/auth/chat.bot`). No service account key or self-impersonation binding is required.
3. **Outbound delivery**: Formats all alerts in the notification into a single Chat message and POSTs to `https://chat.googleapis.com/v1/{space}/messages`.

## Deployment

### 1. Create the shared secret in Secret Manager

```bash
openssl rand -hex 32 | gcloud secrets create grafana-chat-webhook-secret \
  --project=bazel-untrusted \
  --replication-policy=automatic \
  --data-file=-
```

### 2. Grant secret read access to the bot service account

```bash
gcloud secrets add-iam-policy-binding grafana-chat-webhook-secret \
  --project=bazel-untrusted \
  --member="serviceAccount:bazel-ci-skill-reader@bazel-untrusted.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Deploy the Cloud Run function

Run from the root of the repository:

```bash
gcloud run deploy grafana-chat-relay \
  --project=bazel-untrusted \
  --region=us-central1 \
  --source=grafana-chat-relay \
  --function=relay \
  --base-image=python312 \
  --build-service-account=projects/bazel-untrusted/serviceAccounts/572389441833@cloudbuild.gserviceaccount.com \
  --service-account=bazel-ci-skill-reader@bazel-untrusted.iam.gserviceaccount.com \
  --set-secrets=WEBHOOK_SECRET=grafana-chat-webhook-secret:latest \
  --set-env-vars=CHAT_SPACE=spaces/AAQAD9vqp48 \
  --max-instances=2 \
  --allow-unauthenticated
```

## Grafana contact point setup

In Grafana (`https://ci-metrics.bazel.build`) → **Alerting** → **Contact points** → **+ Add contact point**:

- **Name**: `Google Chat (Bazel CI Health Check)`
- **Integration**: `Webhook`
- **URL**: `https://grafana-chat-relay-572389441833.us-central1.run.app` (use the URL printed by `gcloud run deploy`)
- **Optional Webhook settings** → **HTTP Method**: `POST`
- **Optional Webhook settings** → **Authentication Header Scheme**: `Bearer`
- **Optional Webhook settings** → **Authentication Header Credentials**: `<secret value from step 1>`

## Test with `curl`

```bash
RELAY_URL="https://grafana-chat-relay-572389441833.us-central1.run.app"
SECRET="$(gcloud secrets versions access latest --secret=grafana-chat-webhook-secret --project=bazel-untrusted)"

curl -i -X POST "$RELAY_URL" \
  -H "Authorization: Bearer $SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "firing",
    "commonLabels": {"team": "bazel-ci"},
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "VM pool below 25%",
          "org": "bazel",
          "platform": "linux"
        },
        "annotations": {
          "summary": "bazel/linux pool at 18% of expected size"
        },
        "values": {"A": 18.0, "B": 1},
        "generatorURL": "https://ci-metrics.bazel.build/alerting/grafana/pool25/view"
      }
    ]
  }'
```
