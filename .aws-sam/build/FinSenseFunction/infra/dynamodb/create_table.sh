#!/usr/bin/env bash
set -euo pipefail
TABLE_NAME="${1:-agent_sessions}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-eu-west-2}}"

echo "Ensuring DynamoDB table '$TABLE_NAME' exists in region '$REGION'..."
if aws dynamodb describe-table --region "$REGION" --table-name "$TABLE_NAME" >/dev/null 2>&1; then
  echo "Table already exists."
  exit 0
fi

aws dynamodb create-table \
  --region "$REGION" \
  --table-name "$TABLE_NAME" \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Optionally enable TTL on 'ttl_epoch' if you plan expiries
aws dynamodb update-time-to-live \
  --region "$REGION" \
  --table-name "$TABLE_NAME" \
  --time-to-live-specification "Enabled=true, AttributeName=ttl_epoch" >/dev/null 2>&1 || true

echo "Done."
