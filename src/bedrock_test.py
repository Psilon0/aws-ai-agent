# src/bedrock_test.py
import boto3

REGION = "eu-west-2"
MODEL_ID = "deepseek.v3-v1:0"  # or try "qwen.qwen3-coder-30b-a3b-v1:0"

client = boto3.client("bedrock-runtime", region_name=REGION)

def ask(prompt: str) -> str:
    resp = client.converse(
        modelId=MODEL_ID,
        messages=[
            {"role": "user", "content": [{"text": prompt}]}
        ],
        inferenceConfig={"maxTokens": 256, "temperature": 0.2},
    )
    # Bedrock returns an output message with content parts (usually one 'text' part)
    parts = resp["output"]["message"]["content"]
    return "".join(p.get("text", "") for p in parts)

if __name__ == "__main__":
    print(ask("Say hello in one short sentence."))
