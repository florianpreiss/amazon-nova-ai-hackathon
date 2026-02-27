# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in KODA, please report it responsibly
using GitHub's private vulnerability reporting feature:

1. Go to the **Security** tab of this repository
2. Click **"Report a vulnerability"**
3. Provide a description of the vulnerability and steps to reproduce

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅        |

## Security Measures

This project implements the following security practices:

- **No user data stored** — ephemeral sessions, auto-expire after 30 minutes
- **No authentication required** — anonymous by design (GDPR Art. 25)
- **AWS WAF** — rate limiting, bot control, IP reputation, SQLi/XSS protection
- **Secrets Manager** — no credentials in environment variables or container images
- **OIDC authentication** — GitHub Actions uses keyless AWS authentication
- **Container security** — non-root user, read-only filesystem, all capabilities dropped (OWASP CSVS)
- **Dependency scanning** — Dependabot alerts + Trivy container scanning in CI
- **Secret scanning** — enabled on all pushes
- **Code scanning** — CodeQL analysis on all PRs
- **Pre-commit hooks** — bandit (SAST), detect-secrets, hadolint (Dockerfile)
