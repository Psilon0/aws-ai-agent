Goal: AWS-native agent that plans, tools, and responds via API Gateway + Lambda using Bedrock.

## Principles
- Minimal deps, strict JSON Schemas, observable traces.
- Cost-aware inference (temperature, maxTokens, streaming where useful).
- Finance-safe prompts and disclaimers; avoid personalised advice without constraints.

## Components
- API: API Gateway + Lambda (`src/handlers/lambda_handler.handler`)
- Agent Core: Python + boto3 Bedrock Runtime (`src/agent_core.py`)
- Tools: HTTP / S3 / DynamoDB (future)
- State: DynamoDB sessions (future)
- Observability: CloudWatch (logs), X-Ray (optional)

## Sequence (happy path)
1. Client → API Gateway → Lambda validates `AgentInput`.
2. `agent_core.plan()` decides tool vs. direct reasoning.
3. If no tool, call Bedrock via `converse`.
4. Validate `AgentOutput` → return.

## Prompt contract
- Always produce valid `AgentOutput` JSON.
- Include `advice_metadata.disclaimers` in finance responses.
- Ask for missing constraints (horizon, risk, liquidity) before allocations.

## Security
- Least-privilege IAM; no secrets in logs; redact PII.
- Bedrock permissions limited to required models.

## Deployment targets
- MVP: Lambda + API Gateway.
- Stretch: Step Functions for multi-tool runs, Guardrails, VPC endpoints.

## Bedrock invocation pattern
- Use `converse(modelId=..., messages=[...], inferenceConfig=...)`.
- Expect JSON text; validate against `AgentOutput`.
