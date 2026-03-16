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

  # ── Rule 3: Allow Streamlit file uploads ─────────
  # Streamlit's internal upload mechanism (st.file_uploader, st.chat_input
  # with accept_file) sends multipart POST requests to the path
  # /_stcore/upload_file/{session_id}/{widget_id}.
  #
  # Managed rule-group body-inspection rules (SizeRestrictions_BODY,
  # CrossSiteScripting_BODY, SQLi_BODY) produce false positives on valid
  # binary and multipart payloads that exceed the 8 KB inspection limit.
  #
  # Security posture retained for upload requests:
  #   • Rate limiting  (rule 1) — evaluated before this rule.
  #   • IP reputation  (rule 2) — evaluated before this rule.
  #   • Application-level validation in src/core/documents.py:
  #       – Extension allowlist (pdf, docx, txt, md, csv, xlsx)
  #       – Per-type size caps (4.5 MB text, 25 MB media)
  #       – Non-empty content check & safe-filename sanitisation
  #       – Encrypted-file detection (OOXML markers)
  #   • Streamlit server rejects unknown paths with 404.
  #
  # Ref: OWASP File Upload Cheat Sheet — validate at the application layer;
  #      WAF body-inspection bypass for upload endpoints is accepted practice.
  rule {
    name     = "allow-streamlit-uploads"
    priority = 3

    action {
      allow {}
    }

    statement {
      and_statement {
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
        statement {
          byte_match_statement {
            search_string         = "POST"
            positional_constraint = "EXACTLY"
            field_to_match {
              method {}
            }
            text_transformation {
              priority = 0
              type     = "NONE"
            }
          }
        }
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.prefix}-allow-streamlit-uploads"
    }
  }

  # ── Rule 4: Bot Control ──────────────────────────
  rule {
    name     = "bot-control"
    priority = 4

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

  # ── Rule 5: Common attacks (SQLi, XSS) ──────────
  rule {
    name     = "common-attacks"
    priority = 5

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
