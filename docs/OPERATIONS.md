# Operations and release boundary

## Deployment

One organization, one trusted HR team, one worker, one persistent SQLite volume.
Terminate TLS at an HTTPS reverse proxy and set RECRUITAI_ORIGIN to the exact
public origin. Forward only trusted proxy headers. Set a long random workspace
password through a secret manager. Never expose a passwordless development server
on 0.0.0.0. Rotate a workspace password with a session purge during a maintenance
window. There are no individual user accounts or roles in this release.

Configure proxy body limit 12 MB, request/header timeouts, upload rate limits,
login rate limits, connection limits and a bounded upstream timeout. App upload
limit is 10 MB and 20 pages. Parse jobs run in the worker thread pool, not a durable
queue; long jobs should move to isolated workers before higher load deployment.
Health is /health. Containers run as UID 10001, no Linux capabilities, read-only
filesystem with a writable named volume and bounded /tmp.

## Backup and restore

Use SQLite's online backup API rather than copying only the main database while
WAL writes are active. For example, from a trusted maintenance context:

```python
import sqlite3
with sqlite3.connect('var/recruitai.sqlite3') as source:
    with sqlite3.connect('backup/recruitai.sqlite3') as destination:
        source.backup(destination)
```

Encrypt backups and source disks. Restrict filesystem access to the operator.
Store backups outside the web-served tree. Test restoration in an isolated
environment, verify integrity_check and candidate/run counts, and ensure the
restored service is authenticated before routing traffic. Backups contain profiles,
notes, sessions and snapshot PII. Their retention must match organizational policy.

## Retention and erasure

No automatic retention deadline is invented by the application. Before real CV
processing, establish a retention policy and an operator erasure procedure covering
candidates.data, runs.snapshot, backups and any external AI provider. Merely deleting
a candidate row does not erase their historical snapshots. This is a release gate,
not a claim of compliance. Original PDF bytes are not persisted by the application,
but framework temporary uploads exist transiently on disk/in memory.

## AI evaluation

No live Groq call is required by the tests and no real CV was sent for verification.
Before enabling it for production, evaluate a consented CV dataset across text
layouts/languages, compare extracted fields to human-labeled evidence, measure
skill precision/recall and duration errors, and review prompt-injection cases.
Keep low-quality extraction under human verification. Version the model alongside
an evaluation report when changing GROQ_MODEL. Missing data is not evidence of
missing ability. Scores are decision support, not autonomous hiring decisions.

## Scaling and security review

Do not use this SQLite design across replicas, network volumes or multiple tenants.
Introduce organization-scoped Postgres access, individual authentication/RBAC,
durable idempotent job workers, per-user audit identity, object-storage lifecycle
and observability before SaaS deployment. Review dependency advisories, apply
updates, load test, restore test and obtain employer privacy approval before a
public production release. Current verification artifacts cover application
behavior, not a penetration test or certification.

## Legacy separation

The original Supabase project is not called by the v2 runtime. No migration or
deletion was performed on that service. Legacy modules remain reference material.
The previous Git history is recoverable locally from .git-history and is excluded
from commits. Existing DOCUMENTATION.md changes were preserved.
