# PURPOSE: Simple standalone test script for verifying Bedrock model connectivity.
# CONTEXT: Allows quick testing of the AWS Bedrock runtime locally before integrating
#          into the main FinSense pipeline.
# CREDITS: Original work — no external code reuse.
# NOTE: Function unchanged; comments/docstrings only.

import boto3

# Region and model ID used for testing; can be swapped to any available Bedrock model.
REGION = "eu-west-2"
MODEL_ID = "deepseek.v3-v1:0"  # alternative example: "qwen.qwen3-coder-30b-a3b-v1:0"

# Create Bedrock runtime client. Uses local AWS credentials and permissions.
client = boto3.client("bedrock-runtime", region_name=REGION)

def ask(prompt: str) -> str:
    """
    Send a simple user prompt to the Bedrock model and return its textual response.

    parameters:
    - prompt: str – user input text to send to the model.

    returns:
    - str – plain text output returned by the model.

    notes:
    - Uses Bedrock’s 'converse' API which expects a message-based format.
    - Limits response length (maxTokens) and controls creativity via temperature.
    """
    resp = client.converse(
        modelId=MODEL_ID,
        messages=[
            {"role": "user", "content": [{"text": prompt}]}
        ],
        inferenceConfig={"maxTokens": 256, "temperature": 0.2},
    )

    # Bedrock responses include a structured message list; most return a single text block.
    parts = resp["output"]["message"]["content"]

    # Extract and concatenate any 'text' fields into one string.
    return "".join(p.get("text", "") for p in parts)


if __name__ == "__main__":
    # Quick command-line test: verifies that the model responds correctly.
    print(ask("Say hello in one short sentence."))
