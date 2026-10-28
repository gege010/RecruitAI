# RecruitAI observable interaction contract

Business authority: PRODUCT.md, server/models.py validation and server/main.py
authorization, concurrency and snapshot contracts.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | selectField, jobStrip | DESIGN.md | native OS-owned popup | tests/browser.cjs |
| Form | field, area, formError, watchDirty | server/models.py | create/edit/review | tests/browser.cjs |
| Scrollbar | global web/styles.css | DESIGN.md | table geometry only | tests/browser.cjs |
| Toast | notify, notification live region | UX-CONTRACT.md | polite status | tests/browser.cjs |
| CRUD | api, navigate, showModal | PRODUCT.md | list return, criteria stay | tests/test_workspace.py |

No table selection or date picker. Lists show ten candidates per page with
server-side filtering and page clamping. URL stores job, view, status and page.
Candidate names/search are transient PII and excluded from browser history.

## Flow ledger

| Intent | Pending | Success | Error | Source |
|---|---|---|---|---|
| Create/edit job | disabled save | owning list + status | retained form | JobInput, JobUpdate |
| Save criteria | disabled save | same page + stale notice | retained values | PRODUCT.md |
| Add/edit profile | disabled save | candidate list + status | retained form | ProfileInput |
| Review | disabled save | list + status | note/conflict message | ReviewInput |
| Analyze | busy action | list + timestamp + snapshot | explicit retry | PRODUCT.md |
| Upload | per-file result | list refresh, modal stays | per-file error | PRODUCT.md |
| Cancel | dirty discard guard | origin + trigger focus | continue editing | shared modal |

## Safety and recovery

- Forms disable native validation bubbles and use labeled fields.
- Selects intentionally accept OS popup geometry and keyboard behavior.
- Dialogs provide focus trapping, inert background, Escape and focus return.
- Rejection is a human action requiring a note, with no external side effect.
- Stale rankings display a persistent rerun notice.
- Concurrency returns 409 instead of overwriting newer revisions.
- Search is IME-safe, 300ms debounced, cancellation and sequence-guarded.
- Network failure offers retry. Upload cancellation can race with completion;
  refresh and duplicate detection reconcile the actual state.
- All candidate text is escaped before insertion into HTML.

## Soft-delete vs hard-delete policy

No destructive UI is exposed. Retention and erasure remain operator responsibilities
and release gates for real candidate data (PRODUCT.md). Never imply hiding a UI row
erases snapshots. No billing, public sharing, or legal consent flow exists.
