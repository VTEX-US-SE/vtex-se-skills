---
name: stakeholder-scout
description: |
  Scout, profile, and map the stakeholders / decision-making unit of any commerce deal, account, RFP, or opportunity — for VTEX Solution Engineers and Architects. Goes beyond names: per-person profiles with career history, prior platform experience, convergence points (VTEX affinity vs. competitor/incumbent bias, champion signals), decision role, influence, support stance, and warm-intro paths — outputting a stakeholder map, influence×support matrix, ops-ready register, and a "Bot Scout" Slack update.

  ALWAYS trigger proactively when a new deal, RFP/RFI, account, or deal channel appears; a client email lands; the user asks who the stakeholders/decision-makers/buyers are, to map the org, who to engage, who owns the budget, who's the champion, to check contacts on LinkedIn, or find a warm intro; when prepping a client call, discovery, demo, or proposal; or building a profiling tool for ops. Don't skip the profiling layer — convergence points and champion/blocker detection are the value.
version: 1.0.0
---

# Stakeholder Scout

## Purpose

Winning a commerce deal depends on knowing the people as well as the platform: who signs, who evaluates, who champions, who blocks, and who to counter-position against. This skill turns scattered signals (email threads, deal history, public web, LinkedIn) into a **decision-ready stakeholder map** with three things a plain contact list never gives you:

1. **Career history & prior platform experience** — what each person has built or used before (VTEX, or a competitor), which reveals affinity and bias.
2. **Convergence points** — the moments where a stakeholder's history intersects with our deal: a champion signal, an incumbent-platform bias, a "build-it-ourselves" pattern, or a shared history with the VTEX team.
3. **Warm-intro paths** — connection degree and mutual connections that let us reach the right level fast.

Output is both human-readable (map, matrix, Slack post) and machine-readable (a register schema) so it can seed an ops profiling tool.

## The Scout Protocol (run in order)

### Step 0 — Frame the deal
Establish: account/brand, deal type (B2C / B2B / D2C / marketplace / omnichannel), market(s), and what's being sold/replaced. Note the incumbent platform if known — it drives the convergence-point analysis later. If the account has a franchise, holding, or multi-entity structure (common in QSR, retail groups, distributors), flag it: **the entity that owns the e-commerce contract and budget is often not the one operating stores.**

### Step 1 — Source scan (internal truth first)
Pull every stakeholder actually in play before touching the public web:
- **Email**: search the deal threads (`from:` client domain, brand keywords). Extract each client-side person's name, email, and role from their signature. Note who initiates vs. who is cc'd (initiators are usually working-level; senior cc's are sponsors/approvers).
- **Deal history**: search past conversations and older mail for prior rounds with this account or brand. Re-activations, prior RFIs, and past shortlists are gold — they tell you who was already engaged and what was promised.
- Record the **email domain**. A corporate/global domain vs. a local/franchisee domain is itself a signal about who holds the contract.

### Step 2 — Enrichment (research pass)
Research the account and each named stakeholder to establish:
- **Org & ownership structure** — who operates vs. who owns the brand/digital assets; which legal entity holds the contract and budget.
- **Current-state digital** — incumbent commerce platform, apps, aggregator vs. own-channel strategy.
- **Competitive/governance context** — global vs. local platform standards, any preferred/mandated vendor, in-house platform programs.
- **Per-person background** — role, seniority, tenure, and career history (prior employers and, critically, **which commerce platforms they have worked with or implemented**).

Prefer LinkedIn, company sources, and reputable press. For a deep multi-source pass, a research/extended-search tool is ideal. Label every fact **confirmed vs. inferred**, and never invent a role or history.

### Step 3 — LinkedIn verification (live titles + warm paths)
Third-party data brokers lag reality — verify live. LinkedIn access runs through the user's browser and needs their approval; when possible, navigate directly to profile URLs captured in Step 2. For each stakeholder confirm:
- **Current title, employer entity, location** (correct any stale research).
- **Career history** — prior roles/employers and platform experience (feeds convergence points).
- **Connection degree and mutual connections** — map each 2nd-degree contact to the VTEX colleague who can open the door. This is the warm-intro layer.
- If a name **cannot be confirmed**, say so and leave it as a gap — do not attach an unrelated namesake. (A common trap: a senior namesake at a *different* company. Confirm the employer entity, not just the name.)

### Step 4 — Profile & score (the convergence engine)
For each stakeholder, apply the profiling model in `references/profiling-signals.md`:
- Assign a **DMU role** (Economic Buyer / Technical Decision-Maker / Champion / Coach / Influencer / End-User / Blocker / Procurement).
- Assign an **influence level** (High / Medium / Low) and a **support stance** (Champion / Supporter / Neutral / Skeptic / Blocker).
- Detect **convergence points** — tag each with type, evidence, and implication (see the signal library). Examples: prior VTEX success (champion candidate), deep tenure on a competitor platform (bias/counter-position), built the incumbent being replaced (political risk), history of in-house builds (build-vs-buy risk), shared history with a VTEX team member (warm path).
- Compute a lightweight **champion score** and note **risk flags**.

### Step 5 — Assemble outputs
Produce, using the templates in `references/output-templates.md`:
1. **Stakeholder map** — grouped regional vs. local (or by function), each person tagged with role, influence, stance, and a one-line engagement recommendation.
2. **Influence × Support matrix** — the classic grid: who to invest in (high influence + supportive), who to neutralize/convert (high influence + skeptic/blocker), who to keep warm.
3. **Warm-path summary** — the shortest route to the economic buyer/technical gatekeeper via mutual connections.
4. **Bot Scout Slack update** — the fun, scannable channel post (see template). Always show it to the user for review before posting.
5. **Ops register row(s)** — the machine-readable record per `references/stakeholder-schema.md`, so the profile can be tracked and updated over the deal lifecycle.

### Step 6 — Persist & maintain
A stakeholder map is a living asset, not a one-off. Recommend logging the register to the deal file / CRM (e.g., Rocketlane) and re-scouting when new people appear, titles change, or the deal advances a stage. Convergence points and stances should be updated as you learn more from live meetings.

## Convergence Points — the core idea

A **convergence point** is any place where a stakeholder's history or posture intersects with our deal in a way that changes strategy. Always ask, per person:

- **Have they touched VTEX before?** → likely champion / lower education cost / reference internally.
- **Are they deep on a competitor platform?** → probable bias; know what they'll compare us to and pre-empt it.
- **Did they build the system we're replacing?** → replatforming threatens their work; engage with care, give them a win.
- **Do they have a build-it-ourselves track record?** (ex-engineering-heavy orgs, in-house platform programs) → the real competitor may be "do nothing / build internally," not another vendor.
- **Do they share history with anyone on the VTEX side?** → warm path; use it.
- **Does their domain experience match the deal?** (QSR, marketplace, B2B, cross-border) → tailor proof points to what they already value.

The full signal library, competitor-platform reference, and scoring live in `references/profiling-signals.md` — read it in Step 4.

## Reference files

- `references/profiling-signals.md` — Convergence-point taxonomy, champion vs. blocker signals, competitor-platform affinity reference, DMU role definitions, influence/support scoring. **Read in Step 4** (and Step 2 to know what background to look for).
- `references/stakeholder-schema.md` — The ops-ready data model: field definitions + JSON schema for a stakeholder register, so another SE can build a profiling tool or spreadsheet from it. **Read in Step 5** (and whenever building/feeding the register).
- `references/output-templates.md` — Copy-paste templates for the stakeholder map, influence×support matrix, warm-path summary, and the 🕵️ Bot Scout Slack post. **Read in Step 5.**

## Guardrails

1. **Professional/business information only.** Scout roles, career history, and public professional signals relevant to the deal. Do not compile sensitive personal data (home life, health, protected attributes) or anything unrelated to the business relationship.
2. **Confirmed vs. inferred, always.** Every title, history item, and convergence point is labeled by confidence. Never fabricate a role, employer, or connection. If unsure, mark it a gap.
3. **Verify the entity, not just the name.** Same-name people at different companies are the most common error. Confirm the employer before profiling.
4. **LinkedIn/browser access is the user's.** It requires their approval and runs in their session. Read profiles; never send connection requests, messages, or take any action on their behalf without explicit permission.
5. **Nothing gets posted or sent without review.** Slack updates, intro-request drafts, and any client-facing output are shown to the user first.
6. **Bias detection is a hypothesis, not a verdict.** A competitor background flags a likely lens to counter-position — it does not brand someone a blocker. Keep it fair and evidence-based.

## Communication style

Match the SE register: direct, structured, evidence-based. Lead with the net read (who to engage and why), then the map. Use tables for the map and matrix. The Slack update is casual and fun (🕵️ "Bot Scout services update"); the register and map are precise and terse. Separate fact from inference visibly.
