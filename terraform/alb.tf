# ============================================================
# ALB — Application Load Balancer for Streamlit
# ============================================================

resource "aws_lb" "koda" {
  name               = "${local.prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  drop_invalid_header_fields = true

  tags = { Name = "${local.prefix}-alb" }
}

resource "aws_lb_target_group" "koda" {
  name        = "${local.prefix}-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/_stcore/health"
    port                = "8501"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  # Required for Streamlit WebSocket connections
  stickiness {
    type            = "lb_cookie"
    enabled         = true
    cookie_duration = 86400
  }

  tags = { Name = "${local.prefix}-tg" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.koda.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.koda.arn
  }
}

# HTTPS listener requires an ACM certificate.
# Uncomment and set var.acm_certificate_arn once a custom domain is available.
# resource "aws_lb_listener" "https" {
#   load_balancer_arn = aws_lb.koda.arn
#   port              = 443
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
#   certificate_arn   = var.acm_certificate_arn
#
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.koda.arn
#   }
# }
