# Kaizen Sandbox for Amazon Bedrock, Terraform module.
# Deploys the in-tenant detector as a Fargate task (Firecracker microVM) in your VPC.
# It watches your Bedrock agents' reasoning traces and real egress, decides with Claude on
# Bedrock through IAM, and sends out only the verdict.

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0" }
  }
}

variable "kaizen_api_key" {
  type      = string
  sensitive = true
}
variable "agent_name" {
  type    = string
  default = "bedrock-agent"
}
variable "model_id" {
  type    = string
  default = "us.anthropic.claude-sonnet-4-6"
}
variable "image_uri" {
  type    = string
  default = "public.ecr.aws/kaizen/kaizen-sandbox:latest"
}
variable "kaizen_api_url" {
  type    = string
  default = "https://api.getkaizen.io"
}
variable "subnet_id" { type = string }
variable "vpc_id" { type = string }
variable "region" {
  type    = string
  default = "us-east-1"
}

resource "aws_ecs_cluster" "this" {
  name = "kaizen-sandbox"
  tags = { project = "kaizen-sandbox" }
}

resource "aws_iam_role" "task" {
  name = "kaizen-sandbox-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
  inline_policy {
    name = "bedrock-invoke"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{ Effect = "Allow", Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"], Resource = "*" }]
    })
  }
}

resource "aws_iam_role" "exec" {
  name = "kaizen-sandbox-exec"
  assume_role_policy = aws_iam_role.task.assume_role_policy
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"]
}

resource "aws_security_group" "this" {
  name        = "kaizen-sandbox"
  description = "Kaizen Sandbox egress proxy + trace receiver"
  vpc_id      = var.vpc_id
  ingress {
    from_port   = 8080
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { project = "kaizen-sandbox" }
}

resource "aws_ecs_task_definition" "this" {
  family                   = "kaizen-sandbox"
  cpu                      = "512"
  memory                   = "1024"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn            = aws_iam_role.task.arn
  execution_role_arn       = aws_iam_role.exec.arn
  container_definitions = jsonencode([{
    name         = "kaizen-sandbox"
    image        = var.image_uri
    portMappings = [{ containerPort = 8080 }, { containerPort = 8081 }]
    environment = [
      { name = "KZ_AGENT", value = var.agent_name },
      { name = "KZ_MODEL_BACKEND", value = "bedrock" },
      { name = "KZ_MODEL", value = var.model_id },
      { name = "KAIZEN_API_URL", value = var.kaizen_api_url },
      { name = "KAIZEN_API_KEY", value = var.kaizen_api_key },
      { name = "AWS_REGION", value = var.region },
    ]
  }])
}

resource "aws_ecs_service" "this" {
  name            = "kaizen-sandbox"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = [var.subnet_id]
    security_groups  = [aws_security_group.this.id]
    assign_public_ip = true
  }
}
