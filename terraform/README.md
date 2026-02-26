# KODA Infrastructure (Terraform)

## What gets created

| Resource | Purpose | Cost |
|----------|---------|------|
| IAM User + Access Key | API credentials for Bedrock | Free |
| IAM Policies | Bedrock invoke, Code Interpreter, Web Grounding, Marketplace | Free |
| DynamoDB Table | Ephemeral session storage with TTL auto-delete | Pay-per-request (~$0) |
| S3 Bucket | Knowledge base storage for RAG (optional) | ~$0.023/GB |
| CloudWatch Log Group | Application logging (7-day retention) | ~$0.50/GB |
| IAM Role for Bedrock KB | Allows Bedrock to read S3 for RAG | Free |

**Estimated cost: < $1/month** (most usage is Bedrock inference, billed separately)

## Usage

```bash
cd infra
terraform init
terraform plan
terraform apply

# Get your .env credentials:
terraform output -raw env_file_content > ../.env
```

## What Bedrock permissions are granted

The IAM policy grants exactly what KODA needs:

1. **`bedrock:Converse` / `bedrock:ConverseStream`** — Core chat API
2. **`bedrock:InvokeModel`** — Direct model invocation
3. **`bedrock:InvokeTool`** — Required for Code Interpreter and Web Grounding
4. **`aws-marketplace:Subscribe`** — One-time model enablement

All scoped to Nova 2 Lite and Nova Multimodal Embeddings only.

## Important: Code Interpreter regions

Code Interpreter (`nova_code_interpreter`) is only available in:
- **us-east-1** (IAD)
- **us-west-2** (PDX)
- **ap-northeast-1** (NRT)

Use Global CRIS (`global.amazon.nova-2-lite-v1:0`) to auto-route, or set `us-east-1` explicitly.

## Destroying resources

```bash
terraform destroy
```
