# The Boundary Table Pattern

This is the recurring structural device that did the most persuasive work in past successful Solution Designs. Use it by default whenever a section describes how VTEX communicates with an external system of record — a wallet, a loyalty/eligibility engine, a CRM, an ERP, a partner management platform, a payment gateway.

## Why it works

Enterprise technical buyers (especially regulated ones like banks) are evaluating not just "can VTEX do X" but "will VTEX try to become the system of record for something that isn't VTEX's to own." A table that states the boundary explicitly — in both directions — answers that anxiety directly and looks architecturally honest rather than evasive about gaps.

## Template

| [External System] | VTEX's Role (Consumes / Publishes) | Customer Owns |
|---|---|---|
| [System name] | [What VTEX reads from it, what VTEX writes to it, via which protocol/API] | [What stays exclusively in the customer's system — the logic, the ledger, the rules VTEX never touches] |

Follow the table with a short "Architectural Guarantee" callout that states the boundary is enforced by architecture, not configuration — this is the sentence that turns a table into a commitment.

## Worked example (from a past Solution Design)

| Santander System | VTEX's Role (Consumes / Publishes) | Santander Owns |
|---|---|---|
| Wallet | Reads balance and expiry via approved interface. Posts debit reservation, settlement, and cancellation instructions through the Gift Card Provider Protocol middleware. Never stores a points balance. | Points ledger, liability, earn rules, balance accuracy, conversion rates, expiry enforcement. |
| CRM / CIP | Receives CRM segment identifiers and campaign assignments at session start. Publishes order and behavior events outbound. | Customer profile, segmentation logic, lifetime history, consent management. |

## When to reuse vs. when to build a new one

- **Reuse the pattern structurally** for every external-system integration point in the document.
- **Don't reuse the same table** across sections once a boundary has been established — reference it ("as established in Section 2...") instead of repeating it verbatim. Repetition is where past drafts got padded without adding value.
- If a system genuinely has multiple integration layers with different persistence characteristics (e.g. a permanent profile-bound layer vs. a session-scoped layer), it's worth building one table per layer rather than collapsing them — the distinction itself is often the most technically valuable content in the section.
