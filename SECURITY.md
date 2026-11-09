# Security Policy

## Supported Versions

Only the latest version on the `main` branch is actively supported with security updates.

| Version | Supported |
| :--- | :--- |
| `main` (latest) | :white_check_mark: |
| Older releases | :x: |

## Reporting a Vulnerability

If you discover a security vulnerability, **please DO NOT open a public issue or discussion.**

### How to Report

1. **GitHub Private Vulnerability Reporting (Preferred)**:  
   Navigate to the repository's **Security** tab -> **Report a vulnerability**, or visit:  
   https://github.com/mrgusux/automatic-proxy/security/advisories/new  
   This opens a private disclosure advisory visible only to you and the maintainers.

2. **Email / Private Fallback**:  
   If private reporting is unavailable, please open a blank issue titled `Security: private disclosure inquiry` with no sensitive details. Maintainers will reach out directly.

### What Counts as a Vulnerability (In-Scope)

- SSRF vulnerabilities or internal network probing through proxy validation routines.
- Unsanitized proxy input causing remote code execution or shell escapes in parsing pipelines.
- Cache poisoning or memory exhaustion attacks in the GeoIP and protocol validation engines.
- CI/CD workflow permission escalation or secrets exfiltration.

### Out of Scope

- Offline or unstable public proxies (public proxies are naturally volatile).
- Rate limits imposed by third-party upstream targets.

## Response SLA

- **Initial acknowledgement**: Within 48 hours.
- **Triage & severity assessment**: Within 5 business days.
- **Remediation release**: Coordinated disclosure once a patch is verified.
