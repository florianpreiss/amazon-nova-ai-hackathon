# ============================================================
# ECS — Fargate cluster, task definition, and service
# ============================================================

resource "aws_ecs_cluster" "koda" {
  name = "${local.prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = "${local.prefix}-cluster" }
}

resource "aws_ecs_task_definition" "koda" {
  family                   = "${local.prefix}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "koda"
    image     = "${aws_ecr_repository.koda.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 8501
      protocol      = "tcp"
    }]

    secrets = [
      {
        name      = "AWS_ACCESS_KEY_ID"
        valueFrom = "${aws_secretsmanager_secret.bedrock_credentials.arn}:access_key::"
      },
      {
        name      = "AWS_SECRET_ACCESS_KEY"
        valueFrom = "${aws_secretsmanager_secret.bedrock_credentials.arn}:secret_key::"
      },
    ]

    environment = [
      { name = "AWS_REGION", value = var.aws_region },
      { name = "NOVA_MODEL_ID", value = "us.amazon.nova-2-lite-v1:0" },
      { name = "SESSION_TIMEOUT_MINUTES", value = tostring(var.session_ttl_seconds / 60) },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.koda.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
      interval    = 30
      timeout     = 10
      retries     = 3
      startPeriod = 15
    }
  }])

  tags = { Name = "${local.prefix}-task" }
}

resource "aws_ecs_service" "koda" {
  name            = "${local.prefix}-service"
  cluster         = aws_ecs_cluster.koda.id
  task_definition = aws_ecs_task_definition.koda.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.koda.arn
    container_name   = "koda"
    container_port   = 8501
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.https]

  tags = { Name = "${local.prefix}-service" }
}
