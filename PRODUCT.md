# Product and deployment contract

RecruitAI is a decision-support workspace for one organization, operated by a
trusted HR team. Extraction and comparison are automated; humans record shortlist,
hold and rejection decisions. No automated applicant rejection or messaging.

## Authorization

One shared workspace password protects all business API routes. Sessions last 8h,
are stored hashed in SQLite, and use HttpOnly SameSite=Strict cookies. Production
requires a password of at least 16 characters and HTTPS. Passwordless development
accepts loopback clients only. No individual roles or tenant boundaries exist;
never offer this deployment as multi-organization SaaS. Audit actor is the HR team.

## Selection policy

Only job-related skills, duration, degree, required certification and language
contribute to scores. Names, photos, gender, age, location and school prestige are
not scoring features. Skill matching is explicit with documented aliases. Legacy
semantic embeddings are not presented as a validated competency classifier.
No model has yet been evaluated against hiring outcomes.

Experience/education meet full credit at the stated minimum. Not-required criteria
yield 1 for every candidate: they do not change ranking but raise absolute scores;
set their weights to zero to exclude them from the percentage. Unknown evidence
is conservatively scored 0 and marked for verification. A missing mention does
not prove a missing competency.

SAW, WP and TOPSIS provide relative ranks; Borda sums their ranks and preserves
ties. Absolute score is weighted requirement fulfillment, never hiring probability.
Rank depends on the comparison pool. Snapshots retain profiles, criteria, engine
version and UTC timestamp. Profile edits, new candidates and criteria edits mark
results stale. Review status alone does not affect ranking.

## Privacy and lifecycle

Original PDFs are processed transiently and not persisted. Structured profiles
and snapshots are personal data. External Groq extraction requires a server key
and explicit upload opt-in. Local extraction never calls external AI. PDF limits:
10 MB, 20 pages. Operator must configure encrypted disks, backups, backup expiration
and organization-approved retention before accepting real candidate data.
No default automatic retention policy or compliance certification is claimed.

## Deployment boundary

Single worker, single persistent SQLite volume, trusted small-team deployment
behind HTTPS. Proxy must impose request limits and timeouts, including chunked
uploads. Before internet release: dependency vulnerability review, load test,
restore test, privacy/retention policy, and extraction/model evaluation on a
representative consented dataset. Scaling requires Postgres and a durable queue;
do not run this SQLite deployment across multiple replicas or a network filesystem.
