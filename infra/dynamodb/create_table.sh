#!/usr/bin/env bash
# PURPOSE: Creates a DynamoDB table (default: 'agent_sessions') if it doesn’t already exist.
# CONTEXT: Used to initialise AWS resources for the FinSense backend.
# CREDITS: Original work — no external code reuse.

set -euo pipefail   # exit on error (-e), treat unset variables as errors (-u), fail on pipe errors (-o pipefail)

# Takes the table name as the first argument, or defaults to 'agent_sessions' if not provided.
TABLE_NAME="${1:-agent_sessions}"

# Detect AWS region from environment, defaulting to 'eu-west-2' if none is set.
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-eu-west-2}}"

# Notify the user what the script is doing.
echo "Ensuring DynamoDB table '$TABLE_NAME' exists in region '$REGION'..."

# Check if the table already exists by describing it; if it exists, skip creation.
if aws dynamodb describe-table --region "$REGION" --table-name "$TABLE_NAME" >/dev/null 2>&1; then
  echo "Table already exists."
  exit 0
fi

# If not found, create a new table with a single partition key: 'session_id' (string).
# The PAY_PER_REQUEST billing mode means costs scale automatically with usage.
aws dynamodb create-table \
  --region "$REGION" \
  --table-name "$TABLE_NAME" \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable automatic expiry (TTL) on the 'ttl_epoch' attribute if present.
# This step is optional and ignored if TTL can’t be enabled (hence '|| true').
aws dynamodb update-time-to-live \
  --region "$REGION" \
  --table-name "$TABLE_NAME" \
  --time-to-live-specification "Enabled=true, AttributeName=ttl_epoch" >/dev/null 2>&1 || true

# Confirmation message for successful setup.
echo "Done."
