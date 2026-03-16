# ============================================================
# AWS WAF — Web Application Firewall
# Attached to CloudFront distribution
# No CAPTCHA — preserves zero-friction UX for vulnerable users
# ============================================================

resource "aws_wafv2_web_acl" "koda" {
  name        = "${local.prefix}-waf"
  scope       = "CLOUDFRONT"
  description = "KODA WAF - rate limiting, bot control, attack protection"

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
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-rate-limit"
    }
  }

  # ── Rule 2: IP Reputation ────────────────────────
  # Evaluated early so known-bad IPs are blocked before any ALLOW rules.
  rule {
    name     = "ip-reputation"
    priority = 2

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

  # ── Rule 3: Bot Control ──────────────────────────
  rule {
    name     = "bot-control"
    priority = 3

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

  # ── Rule 4: Common attacks (SQLi, XSS) ──────────
  # Streamlit's /_stcore/upload_file endpoint handles multipart file
  # uploads (st.file_uploader, st.chat_input with accept_file).
  # The SizeRestrictions_BODY rule false-positives on valid payloads
  # that exceed the 8 KB WAF inspection window.
  #
  # Security posture retained for upload requests:
  #   • Rate limiting  (rule 1) — blocks excessive request rates.
  #   • IP reputation  (rule 2) — blocks known-bad IPs.
  #   • Bot control    (rule 3) — blocks automated tools.
  #   • Application-level validation in src/core/documents.py:
  #       – Extension allowlist (pdf, docx, txt, md, csv, xlsx)
  #       – Per-type size caps (4.5 MB text, 25 MB media)
  #       – Non-empty content check & safe-filename sanitisation
  #       – Encrypted-file detection (OOXML markers)
  #   • Streamlit server rejects unknown paths with 404.
  #
  # Ref: OWASP File Upload Cheat Sheet — validate at the application layer.
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

        # Exclude upload paths from body-inspection rules that
        # false-positive on multipart payloads > 8 KB.
        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string         = "/_stcore/upload_file"
                positional_constraint = "STARTS_WITH"
                field_to_match {
                  uri_path {}
                }
                text_transformation {
                  priority = 0
                  type     = "URL_DECODE"
                }
                text_transformation {
                  priority = 1
                  type     = "LOWERCASE"
                }
              }
            }
          }
        }
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
