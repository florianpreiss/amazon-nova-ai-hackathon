# ============================================================
# AWS WAF — Web Application Firewall
# Attached to CloudFront distribution
# No CAPTCHA — preserves zero-friction UX for vulnerable users
# ============================================================

resource "aws_wafv2_web_acl" "koda" {
  name        = "${local.prefix}-waf"
  scope       = "CLOUDFRONT"
  description = "KODA WAF — rate limiting, bot control, attack protection"

  default_action {
    allow {}
  }

  # ── Rule 1: Rate limiting ────────────────────────
  rule {
    name     = "rate-limit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 100
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-rate-limit"
    }
  }

  # ── Rule 2: Bot Control ──────────────────────────
  rule {
    name     = "bot-control"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesBotControlRuleSet"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-bot-control"
    }
  }

  # ── Rule 3: IP Reputation ────────────────────────
  rule {
    name     = "ip-reputation"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesAmazonIpReputationList"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-ip-reputation"
    }
  }

  # ── Rule 4: Common attacks (SQLi, XSS) ──────────
  rule {
    name     = "common-attacks"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-common-attacks"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.prefix}-waf"
  }

  tags = { Name = "${local.prefix}-waf" }
}
