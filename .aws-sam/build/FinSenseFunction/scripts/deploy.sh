#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-finsense-stack}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-eu-west-2}}"
DDB_TABLE_NAME="${DDB_TABLE_NAME:-agent_sessions}"
ENV="${ENV:-dev}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "Stack: $STACK_NAME | Region: $REGION | Table: $DDB_TABLE_NAME | Env: $ENV | Log: $LOG_LEVEL"

sam build --use-container
sam deploy \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --parameter-overrides \
      DdbTableName="$DDB_TABLE_NAME" \
      Env="$ENV" \
      LogLevel="$LOG_LEVEL"

echo "Deployed. Fetching API URL..."
aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" --output text
