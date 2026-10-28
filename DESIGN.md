---
version: alpha
name: RecruitAI Workspace
description: A considered recruiting desk for reading evidence and making accountable decisions.
colors:
  primary: '#172b42'
  text: '#263b50'
  muted: '#596c7d'
  background: '#f6f8fa'
  surface: '#ffffff'
  border: '#e4e9ee'
  accent: '#285e80'
  tint: '#eaf2f7'
  success: '#286449'
  warning: '#865b20'
  danger: '#a3343c'
typography:
  display:
    fontFamily: 'Manrope, Segoe UI, sans-serif'
  body:
    fontFamily: 'DM Sans, Segoe UI, sans-serif'
  utility:
    fontFamily: 'Consolas, monospace'
rounded:
  DEFAULT: '10px'
  control: '7px'
  dialog: '15px'
spacing:
  page: '42px'
  panel: '20px'
  column: '20px'
components:
  button:
    height: '38px'
    backgroundColor: '{colors.primary}'
    textColor: '{colors.surface}'
  sidebar:
    width: '238px'
  dialog:
    width: '660px'
---

# RecruitAI Workspace Design System

## Overview

The reference world is a recruiter's organized assessment desk: a quiet navy
cabinet, white dossiers, restrained index tabs, and legible evidence. This is a
product workspace for Indonesian HR teams, not a marketing landing page.
The signature is a segmented evidence meter alongside a transparent criteria rail.

User references inform restraint, hierarchy, useful motion and component detail:
Impeccable, Taste Skill, Emil Kowalski, Apple Design, UI UX Pro Max. Avoid purple
gradients, glass cards, ornamental dashboards, and unsupported AI confidence claims.

Runtime CSS in `web/styles.css` is the canonical token owner (model B).
This document mirrors it; update both in the same change. `tests/test_design.py`
checks the color mapping. Locale: id-ID, Asia/Jakarta dates. Primary use: desktop
recruiting; narrow screens preserve the workflow with table scrolling.

## Colors

Primary maps to `--ink`, text to `--text`, muted to `--muted`, background to `--paper`,
surface to `--surface`, border to `--line`, accent to `--accent`, tint to `--tint`,
and semantic tones to identically named variables. Green indicates completion;
amber signals incomplete evidence or stale results. Red means rejection/error.
Color never carries meaning alone. Only light theme is supported; forced colors
defer to system contrast.

## Typography

Manrope supplies titles and numeric emphasis; DM Sans supplies body, controls,
and data. Fonts are self-hosted with OFL licenses. Main titles 32px, dialog titles
23px, form/body 12–14px, compact table utility text. Segoe UI is the fallback.
Metrics use tabular numbers. Keep candidate names intact; secondary headlines may
truncate because full detail is available in the profile.

## Layout

238px sidebar, 73px topbar, 42px content padding. At 1200px the sidebar becomes
210px. At 1000px the assessment rail moves beneath the table. At 760px navigation
becomes a horizontal strip. The table owns horizontal overflow; forms never
inherit its height. Main content grows naturally; dialogs scroll within 90dvh.

## Elevation & Depth

Borders and tonal differences establish hierarchy. Shadows belong to primary
buttons and dialogs. Modal backdrop dims the workspace. No ornamental glow.

## Shapes

Panels use 10px corners, buttons 7px, dialogs 15px. Candidate monograms use rounded
squares resembling dossier labels. Icons share a 1.5px outline stroke.

## Components

Shared owners in `web/app.js`: `field`, `area`, `selectField`, `formError`,
`showModal`, `confirmDiscard`, `notify`, `api`, `candidateTable`, `heading`,
`jobStrip`, and `navigate`. Shared CSS: `.button`, `.icon-button`, `.badge`,
`.panel`, `.search`, `.field`, and global scrollbar baseline.

Buttons have hover, focus-visible, pressed, disabled and busy states. Forms retain
values after errors. Search has explicit clear, IME-safe debounce and stale-request
cancellation. One polite live region reports status. Form errors persist inline.
Native HTML dialog provides focus containment, inert background and Escape; focus
returns to the trigger. Native select popup geometry is intentionally OS-owned.

One short dialog entrance communicates the new layer. Reduced motion removes
transforms and animation. Spinners indicate actual work, never decoration.

## Do's and Don'ts

- Show evidence and uncertainty together; never label a score as hiring probability.
- Use practical Indonesian copy and consistent verbs throughout.
- Keep sample profiles explicitly fictional and opt-in.
- Keep candidate names and searches out of browser history.
- Preserve space for long names and notes; use few visual accents.
