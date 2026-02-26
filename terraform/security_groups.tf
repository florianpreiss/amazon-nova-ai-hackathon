# ============================================================
# Security Groups — least-privilege network access
# ============================================================

# ── ALB Security Group ─────────────────────────────
# Accepts HTTPS from anywhere (CloudFront IPs in production)

resource "aws_security_group" "alb" {
  name        = "${local.prefix}-alb-sg"
  description = "Allow inbound HTTPS to ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP for redirect"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.prefix}-alb-sg" }
}

# ── ECS Security Group ─────────────────────────────
# Only accepts traffic from ALB, outbound to Bedrock

resource "aws_security_group" "ecs" {
  name        = "${local.prefix}-ecs-sg"
  description = "ECS tasks — only ALB inbound, Bedrock outbound"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Streamlit from ALB only"
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "HTTPS outbound (Bedrock API, Web Grounding)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "DNS"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.prefix}-ecs-sg" }
}
