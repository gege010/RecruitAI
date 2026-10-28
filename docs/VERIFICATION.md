# Verification evidence

Verified locally for the v2 implementation using an isolated Python 3.11 environment.

| Check | Result |
|---|---|
| Fresh install requirements-dev.txt | Passed, no Streamlit dependency |
| pip check in .venv | Passed, no broken requirements |
| pytest | 17 passed; dependency deprecation warnings only |
| Ruff lint and formatting | Passed for server, tests, core/mcdm |
| JavaScript syntax and Prettier | Passed |
| Real text PDF extraction | Passed, including unreadable-PDF failure |
| Browser workflow | Passed; artifacts/browser-report.json |
| Desktop 1440x1080 and mobile 390x844 | Passed; screenshots in artifacts |
| Keyboard Escape and focus restoration | Passed |
| Network failure and retry | Passed |
| Axe WCAG A/AA automated checks | No violations in four tested states |
| Runtime action bindings | All visible non-submit buttons bound in four states |
| Runtime dependency audit | No known vulnerabilities; artifacts/dependency-audit.json |
| npm dependency audit | No known vulnerabilities |
| DESIGN.md official lint | Zero errors; eight unused-in-component metadata warnings |
| Premium skill static audit | Ten actionless-button reports; see adjudication below |
| Docker image build/run | Not verified: Docker engine unavailable on this machine |
| Live Groq extraction | Not exercised; no real CV sent to an external provider |

## Static audit adjudication

The premium skill's static detector recognizes only inline onclick/@click handlers
and form submission. This project uses externally bound `.onclick` properties and
does not permit inline handlers under its Content Security Policy. It consequently
reports ten false positives: dynamic filter/profile/job/review/upload actions and
the two shared shell buttons. Source bindings are in web/app.js; browser checks
assert every enabled visible non-submit button has a real runtime onclick handler.
The raw strict audit is preserved as premium-audit.json; it has not been edited to
claim a clean result. It is not a substitute for the successful browser checks.

## Scope of evidence

Automated accessibility checks do not prove full WCAG conformance. Manual keyboard
checks covered the changed workflow, not an exhaustive assistive-technology matrix.
Security auditing does not constitute a penetration test. Representative model
evaluation, organizational retention/erasure, TLS deployment, load/restore tests,
individual-user authorization and multi-tenant isolation remain separate production
release considerations described in PRODUCT.md and OPERATIONS.md.
