# Deploy the Kaizen Sandbox

Auditable infrastructure-as-code to run the in-tenant Kaizen Sandbox in your own cloud. The
detector decides locally with your own model and sends out only the verdict.

- `aws/kaizen-sandbox.cfn.yaml` — CloudFormation, deploys the sidecar as a Fargate task
  (Firecracker microVM) in your VPC, reasoning with Claude on Bedrock through IAM.
- `aws/terraform/` — the same as a Terraform module.
- `azure/main.bicep` — the Azure Container Apps equivalent.

All three run the published `kaizen-sandbox` image; they never contain the detection logic.
Point your agent's egress at the task on `:8080` and post its reasoning trace to `:8081`.
