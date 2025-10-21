#!/usr/bin/env bash
set -euo pipefail
sam build
sam deploy --no-confirm-changeset --stack-name aws-ai-agent --resolve-s3 --capabilities CAPABILITY_IAM
