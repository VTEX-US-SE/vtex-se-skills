## What it does

`stakeholder-scout` turns scattered deal signals (email threads, deal history, the public web, LinkedIn) into a decision-ready stakeholder map for a commerce deal, account, or RFP. It goes past a plain contact list by profiling each stakeholder on three axes:

- **Career history & prior platform experience** — what each person has built or used before (VTEX or a competitor), which reveals affinity and bias.
- **Convergence points** — where a stakeholder's history intersects the deal: a champion signal, an incumbent-platform bias, a "build-it-ourselves" pattern, or shared history with the VTEX team. A 10-point taxonomy lives in `references/profiling-signals.md`.
- **Warm-intro paths** — connection degree and mutual connections for reaching the right level fast.

Output is both human-readable (stakeholder map, influence × support matrix, warm-path summary, a "Bot Scout" Slack update) and machine-readable (a stakeholder register schema), so it can seed an ops profiling tool or CRM object.

## When to reach for it

Triggers proactively whenever a new deal, RFP/RFI, account, or deal channel appears, when a client email lands, or when asked who the stakeholders/decision-makers/buyers are, who to engage, who owns the budget, who the champion is, or to find a warm intro. Also fires when prepping a client call, discovery, demo, or proposal. Command: `/stakeholder-scout`.

## Prerequisites

None beyond the skill itself. Works best with access to deal email threads and the account's history — internal signals are sourced before the public web.

## The process

Six steps, documented in full in `SKILL.md`:

0. **Frame the deal** — account/brand, deal type, market(s), what's being replaced.
1. **Source scan** — pull every stakeholder actually in play from deal email threads and history, internal truth first.
2. **Enrichment** — research org/ownership structure, current-state stack, and each stakeholder's career history.
3. **LinkedIn verification** — confirm live titles, employer, career history, connection degree.
4. **Profile & score** — apply the convergence-point taxonomy, assign DMU role, influence, support stance, champion score.
5. **Assemble outputs** — stakeholder map, influence × support matrix, warm-path summary, Bot Scout Slack update, ops register rows.
6. **Persist & maintain** — log the register to the deal file or CRM, re-scout as the deal advances.

## Reference files

| File | Purpose |
|---|---|
| `references/profiling-signals.md` | Convergence-point taxonomy, competitor-platform affinity reference, champion/blocker signal lists, DMU role definitions, influence/support/champion-score model |
| `references/output-templates.md` | Copy-paste scaffolds for the stakeholder map, influence × support matrix, warm-path summary, Bot Scout Slack update |
| `references/stakeholder-schema.md` | Ops-ready data model — field definitions, JSON schema, spreadsheet column layout, controlled vocabularies |

## Author

Diego Cione (`github.com/dcionevtex/se-scout-service`).
