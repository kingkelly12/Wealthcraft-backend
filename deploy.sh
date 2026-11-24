#!/bin/bash
# Adulting backend: deploy to Google Cloud Run.
#
#   ./deploy.sh secrets   copy the secret settings from my_flask_app/.env into Secret Manager
#   ./deploy.sh deploy    build the image in the cloud from the Dockerfile and deploy it
#   ./deploy.sh all       secrets, then deploy (first time)
#   ./deploy.sh url       print the live address
#   ./deploy.sh logs      show recent logs
#
# Needs: gcloud logged in to an account with access to the project, and billing enabled on it.
# Secrets are read with python-dotenv (so quotes and stray spaces in .env are removed, which
# plain `docker --env-file` does not do) and are never printed.
set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${GCP_PROJECT_ID:-adulting-515620}"
REGION="${GCP_REGION:-europe-west1}"   # next to the Supabase database (eu-west-1, Ireland)
SERVICE="adulting-api"                 # Cloud Run names must be lowercase
ENV_FILE="my_flask_app/.env"
PY=".venv/bin/python"

# Read from Secret Manager at runtime. Anything empty in .env is skipped.
SECRETS=(SUPABASE_KEY SUPABASE_SERVICE_ROLE_KEY SUPABASE_JWT_SECRET DATABASE_URL SECRET_KEY CRON_SECRET EXPO_ACCESS_TOKEN QWEN_API_KEY)

gc() { gcloud "$@" --project "$PROJECT" --quiet; }

secrets() {
  echo "==> Storing secrets in project $PROJECT"
  ENV_FILE="$ENV_FILE" PROJECT="$PROJECT" SECRETS="${SECRETS[*]}" "$PY" - <<'PYEOF'
import os, subprocess
from dotenv import dotenv_values
env = {k: (v or '').strip() for k, v in dotenv_values(os.environ['ENV_FILE']).items()}
project = os.environ['PROJECT']
def gcloud(*args, data=None):
    r = subprocess.run(['gcloud', *args, '--project', project, '--quiet'], input=data, capture_output=True, text=True)
    return r.returncode, (r.stderr or r.stdout).strip()
for name in os.environ['SECRETS'].split():
    value = env.get(name, '')
    if not value:
        print(f'  {name:27} skipped (empty in .env)'); continue
    exists = gcloud('secrets', 'describe', name)[0] == 0
    rc, msg = gcloud('secrets', 'versions', 'add', name, '--data-file=-', data=value) if exists else \
              gcloud('secrets', 'create', name, '--replication-policy=automatic', '--data-file=-', data=value)
    print(f'  {name:27} {("updated" if exists else "created") if rc == 0 else "FAILED: " + msg.splitlines()[-1]}')
    if rc != 0: raise SystemExit(1)
PYEOF

  # The service runs as the project's default compute account: let it read the secrets.
  NUM="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
  gc projects add-iam-policy-binding "$PROJECT" \
    --member "serviceAccount:${NUM}-compute@developer.gserviceaccount.com" \
    --role roles/secretmanager.secretAccessor >/dev/null
  echo "  runtime account can read secrets"
}

deploy() {
  SUPABASE_URL="$("$PY" -c "from dotenv import dotenv_values as d; print((d('$ENV_FILE').get('SUPABASE_URL') or '').strip())")"
  [ -n "$SUPABASE_URL" ] || { echo "SUPABASE_URL missing in $ENV_FILE"; exit 1; }

  # Only wire up the secrets that exist in Secret Manager.
  SET=""
  for s in "${SECRETS[@]}"; do
    if gcloud secrets describe "$s" --project "$PROJECT" >/dev/null 2>&1; then SET="${SET:+$SET,}$s=$s:latest"; fi
  done

  echo "==> Deploying $SERVICE to $REGION (the image is built in the cloud from ./Dockerfile)"
  # --no-cpu-throttling: the app sends push notifications from background threads after replying;
  #   with the default setting Cloud Run slows the CPU once the reply is sent and they can stall.
  # --allow-unauthenticated: the phone app calls it directly; every route checks its own login token
  #   (and the cron routes check CRON_SECRET).
  gc run deploy "$SERVICE" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --no-cpu-throttling \
    --cpu 1 --memory 1Gi \
    --timeout 300 \
    --min-instances 0 --max-instances 5 \
    --set-env-vars "FLASK_CONFIG=production,SUPABASE_URL=$SUPABASE_URL" \
    --set-secrets "$SET"
  url
}

url()  { gc run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'; }
logs() { gc run services logs read "$SERVICE" --region "$REGION" --limit 50; }

case "${1:-}" in
  secrets) secrets ;;
  deploy)  deploy ;;
  all)     secrets; deploy ;;
  url)     url ;;
  logs)    logs ;;
  *) echo "Usage: $0 {secrets|deploy|all|url|logs}"; exit 1 ;;
esac
