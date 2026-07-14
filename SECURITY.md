# Security Policy

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security
vulnerability, please do **not** open a public issue. Instead, report it
privately so we can address it before disclosure.

**To report a vulnerability:**

- Open a GitHub Security Advisory at:
  https://github.com/YOUR-REPO/advanced-care-planning/security/advisories/new
- Or email the maintainers directly (see repository profile for contact info)

Please include the following details in your report:
- Type of vulnerability
- Full description of the issue
- Steps to reproduce
- Affected versions
- Any potential mitigations you've identified

## What to Expect

- **Acknowledgment:** We'll acknowledge receipt within 48 hours.
- **Assessment:** We'll assess the severity and impact within 5 business days.
- **Fix:** We'll work on a fix and release it as soon as possible, depending
  on severity.
- **Disclosure:** We'll coordinate disclosure with you and credit you
  if you wish.

## Security Best Practices for This Project

### Local Deployment
- Keep your `.env` file private — never commit it to version control
- Use strong, unique LiveKit API keys for production deployments
- Change the default `devkey`/`devsecret` in production

### Production Deployment
- Use HTTPS (not HTTP) for all services
- Restrict network access to the agent API (port 8082) and token server
  (port 8081) — they have no built-in authentication
- Set up ingress with proper TLS certificates
- Use a secrets manager (e.g., Kubernetes Secrets, HashiCorp Vault) rather
  than environment variables for API keys

### Azure OpenAI & Deepgram
- Rotate API keys regularly
- Use the minimum required permissions for each key
- Monitor API usage for unexpected activity

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |

## Known Security Considerations

- The HTTP API (`/close`, `/email`, `/send-plan`) has **no authentication**
  in the current version. In production, restrict access via network policies
  or ingress rules.
- The token server generates LiveKit tokens for **any room or identity**
  without validation. In production, add authentication or rate limiting.
- CORS is configured with `Access-Control-Allow-Origin: *` — restrict this
  to your frontend domain in production.