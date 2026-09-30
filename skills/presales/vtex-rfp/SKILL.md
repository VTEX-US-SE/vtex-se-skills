---
name: vtex-rfp
description: >-
  Answers VTEX RFP/RFI requirements from the client's document and VTEX's own
  documentation, with a source URL per factual claim and a coverage value scored
  on the client's matrix. Use when the user pastes RFP requirements, a security
  questionnaire, or a requirements matrix.
version: 1.14.0
---

# VTEX RFP Response

**The input is the client's document, VTEX documentation, and what the SE knows.**

An RFP arrives at the top of the funnel. There is no live account and no architecture document yet. Those
come later, if the deal is won. The job is to read what the client asked and work out **how VTEX can best
serve them**, using what VTEX publishes and what the SE can tell you.

Every rule below exists because a measured run failed without it. No rule was added on principle.

**The SE who owns the opportunity always reviews this.** The output is a draft for that person, never a
client-ready file.

## Tools

**Required:** `vtex-developer`, for `search_documentation` and `fetch_document`. If it is unavailable, say so
and stop. Do not fall back on model memory or general web search. *(An unconnected connector reports no error
and silently degrades every answer. That went unnoticed for 18 days.)*

**Expected, read only:** `Rocketlane` (commercial shape of the opportunity), `Granola` and `Google Drive`
(meetings and notes with this prospect), `atlas-agent: retrieve_context` and `Slack` (**precedent from
comparable VTEX clients**, see Step 0.3).

**Optional, external:** `vtex-architect` and `vtex-expert` from the Ai Atlas plugin (see Step 0.3 and Step 2).
They are not bundled here. If they are not installed, skip the steps that use them and search the
documentation directly.

**Where it runs.** The full workflow (scripts, gates, spreadsheet round-trip) needs file access: Claude Code
in the terminal or the desktop app. In a plain Claude chat without file access, answer in conversation, say
that the gates did not run, and say the answers must be transposed by hand.

**Do not** look up architecture documents or live accounts. At RFP stage they do not exist, and calling them
wastes a turn to be told so.

> ⚠️ **Known bug.** `fetch_document` rejects `developers.vtex.com/vtex-rest-api/docs/<slug>` with
> *"Unrecognized VTEX documentation URL"*, even though the URL is on `developers.vtex.com`. VTEX's own pages
> still link this way. **Rewrite to `/docs/guides/<slug>` and retry.** A failed fetch is a tool bug, never
> evidence that something is undocumented.

## Sources

1. **Official VTEX documentation** via `vtex-developer`, for what the platform does.
2. **Trust Center** (`compliance.vtex.com`), for certifications and attestations.
3. **The client's own document**, for the requirement, their vocabulary, their countries, and often their
   intended architecture.
4. **Nothing.** Say so and flag it.

**Never model memory.** Not when confident, not when correct.

## The nine rules

| # | Rule | The measured failure behind it |
|---|---|---|
| 1 | **One source URL per factual claim** | Two runs produced **0 citations in 13 answers** despite instructions asking for them. An explicit rule fixed it: 0 → **73** |
| 2 | **The source must be VTEX-owned *and published*** (`vtex.com`, `help.vtex.com`, `developers.vtex.com`, `compliance.vtex.com`), **and the page must actually render for the client** | Free web search cited a third-party blog as an authority on VTEX. Separately, **the connector serves unpublished pages** (see below) |
| 3 | **Search before you hedge.** Hedging about a published fact is failure, not prudence. **One empty search is weak evidence.** Retry with other terms, and when you know which page should hold the answer, `fetch_document` the whole page | A run falsely refused on **PCI DSS v4**, which is published. False refusal was the real error mode, not fabrication. Large pages chunk and semantic search misses them |
| 4 | **Flag every jurisdiction-dependent fact.** The client's countries are in their own document | Data residency is the #1 procurement risk for an EU client, and one run omitted region entirely |
| 5 | **Always emit a coverage value, in the client's own vocabulary** | A run emitted none, so nothing could be rolled up |
| 6 | **Cite the Trust Center** on any certification requirement | It is the artefact procurement actually asks for |
| 7 | **Coverage answers "does VTEX meet this?", not "is there a caveat?"** | A run marked `partial` wherever any caveat existed, dropping section coverage from 100% to ~15% |
| 8 | **`n/a` needs as much verification as a claim** (see Step 3) | Rows marked "no caveat" hid documented limits on status, permission and platform |
| 9 | **Before writing "not supported" or `not-found`, run at least two searches with *different* terms, and record both** | Rule 3 already said *"search before you hedge"*, and the false refusal on PCI DSS v4 happened anyway. **Advice does not fire; a gate does.** See "Validation gates" |

> ⚠️ **The connector serves unpublished pages, and search ranks them first.** Measured 2026-08-11:
> `vtex-composable-and-complete` and `overview-of-vtex-io-services` carry `hidden: true` in their
> frontmatter. They return HTTP 200 on `developers.vtex.com`, **render nothing for the client**, and the
> first one comes back as **result #1** for a core composability query, above the published `composability`
> page. `search_documentation` does not expose the flag. Only `fetch_document` does, in
> `documentMetadata.frontmatter.hidden`.
>
> **So citing from a snippet can hand the evaluator a dead link that looks perfect.** This is a second, harder
> reason for rule 3: fetch not only because the snippet may not sustain the sentence, but because **the
> snippet cannot tell you whether the page exists for the client.** Refuse any page with `hidden: true`, and
> verify each cited URL renders the quoted phrase before delivery.

> 🔒 **Write what the platform does, not how we found out.** An SE reported on 2026-08-12 that answers saying
> *"VTEX publicly documented…"* made the draft *"look really AI generated"*. The diagnosis generalises: **the
> evidence mechanism leaked into the answer voice.** The URL already proves the source is public. Saying so in
> the prose narrates our process to the client.
>
> Cut every phrase that describes where the answer came from: *"According to VTEX documentation"* · *"The
> documentation states"* · *"As publicly documented"* · *"It is documented that"*. Write the claim directly:
> **"VTEX allows…"**, **"The platform supports…"**, **"Orders can be…"**.
>
> Same family as the rule that prose must not restate the coverage value. **The prose says what the platform
> does. Provenance lives in the Evidence column, the verdict lives in the coverage column, and neither belongs
> in the sentence.**
>
> Register for a row: short, declarative, no em dashes, no *additionally* / *it is important to note* /
> *seamless* / *robust* / *leverage*, no stacked hedging, and no bold scattered through the sentence. Copulas
> beat constructions: *is*, *has*, *allows*, not *serves as* or *provides the ability to*.
>
> **Structure it for a reviewer's eyes, not as one dense block.** A reviewing SE asked for line breaks and
> spacing to make responses easier to read. A row's `Implementation` and multi-sentence `Response` read like
> one run-on paragraph otherwise. A person scanning 800 rows needs line breaks between distinct points (what
> it does / how it is implemented / the caveat). This is layout, not content, and it doesn't relax any of the
> register rules above. Below roughly 250 characters, a single paragraph is the right shape. Don't pad a
> short answer into three blocks.

> 🔒 **`integrator-build` means the CAPABILITY is missing, never that the front-end renders it.** In a
> headless architecture the front-end is always built, because that is what headless means. If "the client's
> front-end renders it" counts as integrator-build, every row in a headless RFP becomes integrator-build and
> the class collapses into noise, dragging real coverage down with it.
>
> | class | means |
> |---|---|
> | `platform` | capability is native and exposed through the API/BFF; the front-end renders it, as it renders everything |
> | `integrator-build` | the capability does not exist and must be built |
>
> Caught on a FastStore RFP where VTEX IO **backend** apps are reusable through the BFF while only **Store
> Framework frontend** blocks need rebuilding. Classifying the rebuild as a capability gap understated the
> platform across dozens of rows.

> 🔒 **Declare the solution set at Step 0, and answer only from it.** Use an allowlist, not a denylist. A
> denylist is unbounded (CMS Portal, Store Framework, Site Editor, legacy B2B, legacy checkout, each
> discovered one incident at a time). An allowlist is decidable: if the answer does not rest on a solution in
> the set, it does not ship.
>
> **The default, confirmed 2026-08-14 by SE leadership (regional lead and global director):** storefront →
> **FastStore**, B2B → **Buyer Portal**. This is global, not regional.
>
> Two consequences that are easy to miss: **Site Editor is the CMS for Store Framework, so it leaves with
> it**; and any capability whose only documented path is a Store Framework app or block must be re-answered
> from its native API path or downgraded. Record the set as a standing decision every worker reads, and state
> it in the SE document. A reader six months later must know the answer was scoped by POLICY, not by platform
> capability.
>
> **A deal may leave the default, and then the deviation is the thing to record.** On one 800-row RFP both
> reviewing SEs converged on external headless and removed FastStore, because the client specified 52
> front-end modules and a mixed answer would blur the line between VTEX as commerce backbone and the front end
> as a separate layer. That is a good reason. What made it expensive was that the agent had already chosen
> headless silently, inferring it from a mention of a mobile app, so the decision surfaced on day two as a
> disagreement instead of on day one as a choice.
>
> So: **propose the architecture from the document, with the evidence and the consequences it forces, and
> have the SE confirm it before the first row is written.** A filled-in proposal takes two minutes to confirm.
> A blank question takes half an hour to answer and gets skipped.

> 🔒 **The architecture is a registry entry, not a paragraph in the prompt.** Once chosen, it governs every
> row, and prose injected into a worker prompt does not govern anything. It is read with varying attention,
> and a worker writing about front-end modules will reach for the native storefront because for *rendering*
> that is the obvious answer.
>
> Give it the same mechanism as the capability registry: one canonical value on disk, and a check that
> rejects a row whose text contradicts it. `architecture: headless-external` in the registry and `FastStore`
> in the prose is a rejection, whatever the row and whichever worker wrote it.
>
> When drift is reported, **measure where it actually is before treating it.** A reviewer saw the native
> storefront reappear "in the last 100 questions" and proposed re-reading the context every 80 rows. The
> distribution said otherwise: 44 mentions spread from row 20 to row 767, only 17 in the final 200, and the
> cluster was in the section about front-end modules, so it followed subject, not position. A periodic context
> reload would have treated a symptom that was not there and spent tokens on every run. **The registry
> detects; a prompt only hopes.**

> ⚠️ **Published is not the same as available to this client.** Reported by an SE on 2026-08-12: a run
> answered using **CMS Portal (Legacy)** documentation, the pre-IO stack that is *"no longer available for new
> accounts"* and was never implemented or supported in that SE's region. The page is real, published,
> VTEX-owned and was quoted correctly, so **it passed every check**: rule 2 (domain and published), rules 3
> and 9 (search discipline), and the provenance quote (the page was genuinely opened). None of them ask whether
> the documentation describes the platform generation the client would actually receive.
>
> This is worse than a dead link, because a dead link is visible. Refuse by marker: slug or `filePath`
> containing `legacy`, `cms-portal-legacy`, `legacy-cms`; a title carrying `(Legacy)`; or body text with
> *"stores using the Legacy Portal technology"* or *"no longer available for new accounts"*. **The legacy
> page names its own replacement** (CMS for FastStore, or Site Editor for Store Framework), so route to that
> instead of stopping.
>
> **Step 3.3 already has the mechanism.** The `Region` class asks *"available in their country, on their
> plan?"* Run it against the platform generation, not only against connectors and certifications.

> 🔒 **A gap belongs to the capability where it was proved, and cannot leave it.** Measured 2026-08-12 on 496
> drafted rows: **55 rows carried a gap that was a pointer to another row's gap. All 55 were `Partially
> compliant`. Not one was `Compliant`.** 17 of them inherited from a *different* `capability_slug`. One row
> said it outright in Polish, *"dziedziczy ją przez odwołanie"* (inherits it by reference), importing a
> price-tier-matrix gap from one section into a requirement in another section about the local menu after
> address selection, a capability that is native.
>
> **A form of inheritance that only ever moves downward is not inheritance, it is contamination.** If the
> mechanism never once produces the favourable verdict, it is propagating a keyword rather than knowledge, and
> that asymmetry is the cheapest thing to test for.
>
> The cause was one of this skill's own rules. *"One capability holds one verdict"* was generalised from
> **same slug** to **same topic**. The registry blocks contradiction *inside* a slug, but nothing stopped a gap
> from crossing slugs. **Every consistency mechanism needs its scope named, or it becomes a propagation
> mechanism.**
>
> Check: reject a row whose `gap` both matches an inheritance marker (`dziedziczy`, `inherit`, *"ten sam
> brak"*, *"the same gap"*, *"jak w wierszu"*, *"see row"*, *"patrz RFP"*, and the equivalent in the client's
> language) **and** references a row whose `capability_slug` differs. Raise a hard failure when the set of
> inheriting rows contains zero `Compliant`. Before writing a row, restate the requirement in one sentence
> and name the capability it exercises. A gap belonging to another capability does not enter.
>
> The commercial framing an SE gave for the same defect: **present the platform in its best true light.**
> Answer the requirement verbatim, in its strongest true reading. Where we genuinely do not cover something,
> say so once, where it is true. Restating a gap in rows that never had it is not caution, it is a factual
> error, and on a scored document it costs points.

> 🔒 **The prose must not carry the coverage value, and saying so in prose was not enough.** Measured
> 2026-08-12: **228 of 496 answers (45%) opened with the verdict**, e.g. *"Compliant. Delivery vs pickup
> selection is native…"*. This skill already told the writer not to do that (see the register rule above).
> **The instruction existed and was violated in nearly half the rows**, which is rule 9's lesson arriving a
> second time: advice does not fire, a gate does.
>
> Redundancy is the small reason. The real one: **it goes stale silently.** When a reviewer flips Coverage
> from `Partially` to `Compliant` in the dropdown, the prose still reads *"Partially compliant."* and the cell
> now contradicts the sentence inside one row. One row went further, *"Compliant, reclassified 2026-08-12:
> …"*, putting our own audit trail in front of the client.
>
> Two companion measurements from the same sweep change the remedy: **em dashes in 287 rows (57%)**, but
> classic AI vocabulary (*additionally*, *seamless*, *robust*, *leverage*) in **3**. The prose was not
> inflated, it was terse and correct with three mechanical tells. So the fix is three find-and-replace passes,
> not a rewrite. **Do not run a humanising pass over hundreds of terse technical rows**, because it flattens a
> register that is already right. Reserve it for the executive summary and prose read end to end.
>
> Check: reject any answer opening with a value from the coverage enum, containing an em dash, or narrating
> our process.

> 🔒 **Retiring a field leaves orphans, and nothing announces them.** When a field stops being the one that
> ships, every script keyed on "the answer" has to be repointed by hand. Three incidents in a single day, all
> from retiring a client-language answer field in favour of English-only:
>
> | What broke | How it looked |
> |---|---|
> | The delivered column was renamed and the old name was left in place | A second prose column with a plausible name, which the agent filled with internal notes. 19 rows of our vocabulary sat one column away from 111 client answers |
> | The validator still required the retired field | 111 new warnings that were not defects, in a gate people had just started trusting |
> | A prose-structuring pass ran on the retired field | 770 fields beautifully restructured, and the delivered column untouched at 0% |
>
> None of the three raised an error. Each one *worked*, on the wrong field.
>
> **Delete the retired column rather than repurposing it.** The repurposing is what makes it dangerous: an
> empty column beside a full one is a column someone will fill. And when a decision changes which field
> ships, grep for the old field name across every script before running anything, because the scripts will
> keep succeeding.

> 🔒 **Technical depth follows who does the work: native rows go deep, custom rows stay in business
> language.** Decided 2026-09-30, following the reviewing SE's position.
>
> | The row is | Write |
> |---|---|
> | native (`platform`) | **technical depth.** How the platform does it: the module, the configuration, the API or setting involved, the limits. The product exists and is documented, so every detail is verifiable against the cited page, and depth is what makes a native answer credible to a technical evaluator |
> | custom (`integrator-build`, or the SI's part of a `shared` row) | **business language.** What the client gets, which VTEX surface it rests on, and that the integrator builds it. Nothing about how |
>
> Why the custom half stays shallow: a detailed answer on custom work reads as a commitment to a specific
> implementation, written before anyone sized it. Six months later the real implementation is different and the
> RFP is the thing the client holds up. Sequences of steps, data models, field mappings and estimates belong in
> a Solution Design, not an RFP.
>
> Silence is also a promise, which is why the custom half still names the surface and who builds. A row that
> needs SI work and only says "VTEX supports this" reads as native.
>
> Depth on native rows is still bounded by the citation rules: every technical detail must be on the cited
> page (rule 1), and depth never means narrating our process.
>
> This is not a hard gate, because depth is judgment. `validate_draft.py` does **warn** on the measurable
> proxy on custom rows: endpoint paths, numbered steps, ordered procedures.

---

## Two lessons about gates

> 🔒 **A gate you have not seen reject anything is not a gate.** Measured 2026-08-11, three times in one day,
> all the same shape. Each check passed for a reason unrelated to what it checked: a citation verified
> against the local corpus while the client's page was unpublished; a quote verified against *any* cited
> document while the Evidence URL pointed at a different page (**8 rows in 63**); and a newly added rule keyed
> on a field name the drafts did not use, which reported **50/50 clean including the three known violations**.
>
> **Before trusting a clean pass, write a row that violates the rule and confirm it is rejected**, per rule
> added, not per artefact. And every verification must end at **the artefact the recipient opens**. Corpus,
> cache and rendition are not what the client sees.

> **Why 9 exists when 3 says the same thing.** The same lesson is written into Step 3.3: *"a rule read after
> the decision does not fire."* Rule 3 is guidance at drafting time; rule 9 is a condition on the row. The
> distinction matters because **the measured error mode is refusing too much, not claiming too much**, and on
> an RFP, denying something that is published costs the whole line.

### Rule 7, and the invariant that keeps it honest

Downgrade **only** when the caveat *disqualifies*. Never when it merely *qualifies*.

| Caveat | Example | Coverage |
|---|---|---|
| **Qualifies**: exists, but version, config or paid add-on differs | Client asks TLS 1.3; VTEX documents TLS 1.2 | **Keep the high value** |
| **Disqualifies**: the capability does not exist | Behavioural fraud detection at login | **Downgrade** |
| **Not a product requirement**: a service or contract obligation | Quarterly reviews with the client's InfoSec team | **Outside the product scale, say so** |

> 🔒 **INVARIANT, every row: if coverage keeps the high value AND a caveat exists, the caveat MUST be in the
> answer prose.** Rule 7 is the only rule pushing toward claiming more, and this is what binds it. Read the
> row back and confirm the sentence is there. If not, write it or downgrade. Never neither.

### Whose vocabulary

**The scale belongs to the client.** If their matrix defines values, use them verbatim.

If it does not, use this and **say explicitly that it is ours**, so the SE can remap: `OOTB` · `Add-on`
(exists, paid VTEX product) · `Configuration` · `Partial` · `Contractual` · `Gap`.

> **If the client's scale has no way to say "no"** (several do not), a clean 100% is an artefact of the
> vocabulary, not a result. **Say that out loud in the roll-up** rather than letting the number speak.

### Which language

**Answer in the language of the client's document, confirmed with the SE at Step 0.3, not assumed.** A
Spanish RFP defaults to Spanish, a Portuguese one to Portuguese. This is not a preference: the prose is
transposed verbatim into their matrix and read by their evaluation committee. Step 0.3 is where the SE confirms
or overrides that default, and where they say whether they review before delivery. The answer to that second
question decides the mechanics below.

Split what is theirs from what is ours:

| Goes to the client, **in their language** | Stays internal, **in the SE's language** |
|---|---|
| The answer prose · the coverage value · anything typed into their file | Review flags · the Step 6 queue · notes to the SE |

**Prefer the source page in their language when it exists.** `help.vtex.com` publishes `/en/`, `/es/` and
`/pt/` renditions of the same article. Citing an English URL in a Spanish RFP hands the evaluator a link they
may not read. If only English exists, cite it. A real English source beats a Spanish one you invented.

> 🔒 **When SEs review before delivery, draft in one language and translate once, at the end.** The rule above
> describes the *delivered* artefact. It does not describe the review copy, and conflating the two costs real
> money. Decided 2026-08-12 on a 700-requirement Polish RFP: the agent was writing every row in both English
> and Polish, and the SEs were editing only the English. **Every Polish cell went stale the moment its English
> twin was corrected**, and we paid tokens to generate all of it twice.
>
> Draft in the SEs' working language. Translate in a single pass **after review closes**, into a new file, as
> the last step before the client document. Two conditions make this safe: the translation pass is mechanical
> and reviewable in one sitting, and nothing translated is ever edited afterwards, because an edit after
> translation reopens the same drift.
>
> When the client's language has no documentation rendition (no `/pl/` on `help.vtex.com`), say so in the
> roll-up. The evaluation committee gets prose in their language and URLs in another, and that is a caveat to
> declare rather than a detail to bury.

## Workflow

### Step 0: Everything we already have on this prospect

**0.1: The client's document.** Read the **originals** (`.docx`, `.xlsx`, `.pptx`, `.pdf`). A folder may also
hold `.md` files derived from them. Those are **ours**: they mix our analysis with the client's content, and
they may condense. *(Measured: 2.47 MB of originals rendered to 28 KB. Answering from those means answering a
paraphrase and counting requirements that were already summarised away.)* Use them to navigate, **never as the
source of a requirement, a count, or a quote.**

Then state what the document tells you:

- **The language it is written in.** That is the language of the answer. State it before drafting anything
- **Countries and jurisdiction.** These drive data residency, fiscal and certification answers
- **Architecture intent, if stated.** Many RFPs say plainly that they want headless, or name their IdP, ERP
  or POS. **That changes the honest answer**: a native app can exist and still not be their path
- **Their coverage vocabulary**, if the matrix defines one
- **Business context**: stores, brands, channels

**Classify each section, not the document.** A large RFP often mixes kinds of question, and each kind needs
different handling. Propose a profile per section and confirm it at Step 0.3:

| Profile | Typical content | How it is handled |
|---|---|---|
| `full` | Functional and technical requirements | The whole workflow, including the architecture proposal and the solution set |
| `security` | InfoSec and privacy questionnaires (SIG, CAIQ, the client's own) | No architecture step. Sources: the Trust Center first, then VTEX's security and privacy documentation. **Every row goes to SE review.** Process questions (pen-test cadence, insurance, background checks, review meetings) are usually "not a product requirement" (rule 7) |
| `rfi` | "Describe your platform", capability overviews | Cited answers as usual. If the client does not score, leave coverage empty. Architecture only if they ask for it |
| `commercial` | Pricing, contract terms, liability, penalties, legal | **Not answered.** Leave the client's fields empty, write what they're asking in `se_question`, and flag the row `commercial`. The SE decides where it goes |

A security-only questionnaire is simply a document whose sections are all `security`: skip the
architecture questions at Step 0.3 and the precedent search, and go straight to the requirements.

Record the profiles in `rfp.config.json` (`"profiles": {"13": "security", "14": "commercial"}`). A key covers
its subsections. The gates follow the profile.

**Also check whether they dictate the answer format.** Some RFPs define the coverage values, the wording, or
how they want each item scored. **If they do, that wins over any default of ours.** Say you found it and use
it verbatim.

**0.2: What we already have on them.** An RFP rarely arrives cold.

| Where | What for |
|---|---|
| **Rocketlane** | Commercial shape of the opportunity: ACV, GMV, region, stage, how it was registered in Salesforce. Useful for **sizing and seriousness**, not for architecture |
| **Granola** | Discovery calls, onsite meetings, intro calls |
| **Drive**, the prospect's folder | Decks delivered to them, meeting notes, prior questionnaires |

From meetings, what matters, in order: **what they said they want** · **what we already told them** (an RFP
answer must not contradict a demo given or a deck sent) · **constraints they mentioned** · **who decides** on
their side.

**If there is nothing, say so and move on.** *"No prior contact found"* is a good Step 0 output. It means the
`solution-design` flags below are genuinely open rather than something we could have looked up.

> **Why these and not account systems:** a call, a deck and a CRM record exist **before or during** the RFP.
> An architecture document and a live account only exist **after the deal is won**. The first is context we
> already have; the second is information from the future.

**0.3: Ask the SE. Do this after reading the document, not before.**

Reading first means asking **specific** questions instead of generic ones. Put them in one short block and
**offer to proceed either way**, since the SE may not be available and the work should not stall. **Ask only
what the document's profiles need**: questions 1 and 2 apply only when there is a `full` section.

1. **Architecture.** Do you already have a direction in mind for this client (headless, native storefront,
   composable)? *This changes the honest answer on any requirement a native app would otherwise cover.* Arrive
   with a proposal and its evidence, not a blank question (see "Ground the architecture proposal" below).
2. **Fit.** Which VTEX capabilities do you already see landing here? Anything you would deliberately keep out
   of scope?
3. **Constraints.** Incumbent vendor, existing systems, deadlines, anything already promised to them?
4. **The specific ones this document raised**, listed by requirement number. *(For example: "item 4 mentions
   POS but names no acquirer. Do you know which one?")*
5. **Language.** The document is written in [language detected at Step 0.1]. Is that the language you want
   the final answer delivered in, and will you review the draft before it reaches the client? *The second half
   is not a formality: it decides the mechanics, not just the target (see "Which language").*
6. **Review mode.** Where do you want to review: here in chat, in the spreadsheet (Google Sheets or Excel), or
   both? **Always ask. Never pick a default for the SE.** See "Reviewing in chat" and "SE review round-trip".
7. **Section profiles.** Confirm the proposed profile per section, especially anything proposed as
   `commercial`, since those rows will not be answered.

Then say: *"I can proceed on stated assumptions and flag every one of them, or wait for your answers."*
**Never block silently, and never guess silently.**

> The SE reviews the output anyway. **Bringing them in before the work is cheaper than correcting after it**,
> and the questions are better once the document has been read.

**Bring precedent to that conversation.** Questions alone put the whole load on the SE. Pull the profile out
of the document (vertical, number of brands, countries, channel model, physical-store footprint, scale) and
search for **VTEX clients that look like this one**:

| Where | What it gives |
|---|---|
| **Atlas** `retrieve_context` | Architecture cases with decisions, drawbacks and risks already written up |
| **Slack** | What the team actually hit on comparable accounts, usually the part no document records |

Report two or three, each with **why it resembles this prospect**, **what was decided**, and **what bit them**.
That last one is the valuable half.

> 🔒 **Precedent informs the conversation. It never becomes an answer.** Another client's architecture is not
> this client's design, and a requirement row must still be answered from documentation. Keep precedent in the
> block for the SE, never in the coverage table.
>
> *Worth the search: an in-store case for a European retailer in Atlas recorded that fiscal-printer
> integration and the legal standing of e-mail receipts were unresolved in the EU. No VTEX product page says
> that, and for a prospect in another EU market it is the thing that decides the answer on in-store payments.*

**Ground the architecture proposal in current capability data.** Precedent tells you what happened on a
similar deal. What the platform can and can't do today, per architecture option, is a separate question. If
the team maintains capability matrices per module (storefront, checkout, seller portal, B2B/Buyer Portal),
read the ones this document's architecture intent touches: a headless RFP reads storefront and checkout at
minimum, a marketplace deal adds seller portal, a B2B deal adds Buyer Portal. Note the prerequisite chain:
**Buyer Portal requires FastStore**, so a storefront decision that rules out FastStore rules out Buyer Portal
too, whatever the B2B fit signals say. If no matrix exists, build the proposal from documentation and say so.

> 🔒 **The most recent source wins, always.** A matrix is a starting point for the architecture
> conversation, never the answer. Re-check every capability against the live documentation (`fetch_document`)
> at the moment you answer. When the matrix and the documentation disagree, the documentation wins and you tell
> the SE which matrix row is out of date.
>
> **A row citing a matrix entry still needs its own fresh check, not a copy-paste.** Capability status
> moves: Apple Pay's cross-browser support and FastCheckout's regional coverage both changed within a single
> month during this skill's own research. Treat any matrix row older than a few weeks as *to confirm*, and
> never quote one into the client-facing answer without the same search-and-cite discipline (rules 1–3).

**For architecture questions a lookup can't settle** (data architecture, personalization, analytics,
multi-tenancy, franchise-account topology, migration planning, or any trade-off that needs a reasoned
recommendation rather than a covered/not-covered answer), consult the `vtex-architect` skill if it is
installed. It runs its own reasoning protocol (identify layer and domain, check accepted decisions via Atlas,
ask the SE when a load-bearing constraint is missing, apply the matching decision framework) before
recommending anything. **Use it for the reasoning, not as a replacement for capability data.**

> ⚠️ **Confirmed live, 2026-08-18: `vtex-architect`'s own written rule doesn't always fire as written.** Its
> skill file says *"for multi-tenancy questions, always ask about fulfillment model and catalog ownership
> before recommending an account structure."* Tested with a 3-brand, single-account multi-tenancy question, it
> answered with a full, well-grounded recommendation first and only surfaced the two expensive-to-reverse
> questions at the end. **This is rule 9's lesson again: a rule stated in prose is not a guarantee.** The
> behavior matches this skill's own propose-then-confirm philosophy, so it isn't wrong, but don't assume
> `vtex-architect` blocks on missing constraints. Read its answer for whether the caveat actually appears.

### Step 1: Enumerate

List the requirements one per row and **state the count** before answering.

When one requirement bundles several asks, **split it but keep the client's numbering**, suffixed (`3a`,
`3b`). Then report both readings: rows scored, and coverage against their original numbering. Their matrix has
their numbers in it, and an answer that silently renumbers cannot be transposed back.

*(Extraction on a 109-requirement RFP took five attempts, and four produced plausible wrong counts (100%, 85,
61, 227) before the correct 109. A count never stated is a count never checked.)*

### Step 1b: Large RFPs, split by section, not by row count

**For RFPs above roughly 150–200 requirements**, answering sequentially either runs out of context
mid-document or takes too long to be useful. Split the work, but split by **document section**, never by an
arbitrary row-count chunk. Sections keep shared context together (rows in one section usually share sources)
and keep the split legible to a human reviewing it later. Reconstructed from the one 800-row run that actually
happened:

1. **One orchestrating session runs the whole RFP, with sections running inside it as subagents**, not as
   separate restarted sessions. Each subagent is a "worker" assigned one or more sections (e.g. `sections:
   ["24.3", "24.4"]`), and it reports its rows back to the orchestrating session rather than writing the
   client-facing output directly.
2. **Give each worker the architecture registry entries and a short decisions digest, never the full executive
   summary.** (See Step 6: a full summary injected as start-up context cost a worker 20 minutes.)
3. **Each worker returns a manifest, not just prose**: `{worker, sections, count, rows}`, with one object per
   requirement carrying every field Step 5 needs (coverage, line_class, capability_slug, response,
   evidence_url, provenance_quote), not reconstructed later from free text.
4. **Run the validation checks per worker's output before compiling**, not only once at the very end. A
   rejection caught early is cheaper than one caught after five workers' output has been merged.
5. **Compile in waves, and name them** (e.g. WAVE2, WAVE3, GAPFILL, FINAL). A large RFP is answered and
   reviewed incrementally, and an SE needs to know which wave they're looking at and what's still open. Never
   silently merge a new wave into a file already under SE review.
6. **Run the gap-scope check across the combined output, not per worker.** Two workers answering the same
   `capability_slug` from different sections is exactly the scenario it exists for. A single worker's rows are
   internally consistent by construction, but two workers' outputs together might not be.

### Step 2: Per requirement, search, then draft

1. `search_documentation` with terms from the requirement; `fetch_document` when the snippet is not enough to
   support the sentence you intend to write.
2. **For requirements about logistics, catalog structure, promotions/pricing, or OMS/order lifecycle**, if
   `vtex-expert` is installed, load its matching reference first (`logistics`, `catalog`, `promotions`,
   `oms`). It's curated platform mechanics with known quirks already flagged, faster than a cold search and
   more likely to name non-obvious behavior. **It never replaces the citation requirement.** Every fact still
   needs its own source URL (rule 1). `vtex-expert` tells you where to look, not what to cite.

   > ⚠️ **Confirmed live, 2026-08-18: `vtex-expert` cited its own internal reference file in the answer's
   > source list**, next to two real VTEX doc URLs. **An internal skill reference file is never a citable
   > source.** Strip it from the source list before the answer ships.
3. Draft from what the document says, **in the agreed language** (check it, do not default to English). Attach
   the URL (rule 1), on a VTEX domain (rule 2), in their language where that rendition exists.
4. Certification requirement → cite the Trust Center too (rule 6).
5. Found nothing? **Search again with different terms** before concluding it is undocumented (rules 3 and 9).
6. **Sources contradict? Say so, never pick one silently.** *(Real case: the ISO 27001 page says data is
   processed in Brazil; the Data privacy page says Northern Virginia.)*

> **Tip that saves most of the run time:** requirements in one section usually share sources. Fetch the two or
> three pages the section depends on **once**, then answer the rows against material already in context. It is
> faster, and it makes answers inside a section consistent with each other.

### Step 3: Classify, then run both checks, per row

**3.0: Read who does the work off the answer you just wrote.** Set `line_class` after the prose, never
beside it. *(A Business Impact Analysis row came back `platform` / VTEX while its own text said the
integrator builds it: the two were set independently.)*

| `line_class` | When the answer says | Owner in the client's file |
|---|---|---|
| `platform` | VTEX does it natively or by configuration | VTEX |
| `integrator-build` | the capability must be built by the SI | Integrator |
| `shared` | the work splits between VTEX, the SI and/or the client; list them in `owners` | e.g. VTEX + Integrator + Client |
| `not-deliverable` | there is no path at all (the only class allowed with a `none` coverage) | none |

The owner is **derived** from this, never typed separately, so the two cannot disagree. The validator rejects
a `platform` row whose answer says someone else builds it.

**3.1: Assign coverage** by rule 7, in the client's vocabulary.

**3.2: Invariant.** High value + caveat → the caveat is in the prose. Read the row back.

**3.3: Before writing `n/a`, check four classes.** You are claiming the capability has **no limit**, and that
is a factual claim.

| Class | Ask | Catches |
|---|---|---|
| **Status** | Only in a certain state? | Order editing works only in `Handling shipping` |
| **Permission** | Needs a specific role? | Returns need an OMS-permissioned user |
| **Platform** | One device, one OS, one app? | The flow is Admin-only, not in the app the requirement is about |
| **Region** | Available in their country, on their plan, on their platform generation? | Connector certified only elsewhere; legacy-only feature |

Found a limit → **`yes`**, and it goes in the prose. Ran all four and found none → **`n/a`**. Did not run them
→ **`unchecked`**, and say so.

*This is a numbered step because it did not work as a note elsewhere: when the same rule sat further down the
document, `n/a` went up and `unchecked` was never used once. **A rule read after the decision does not fire.***

**3.4: Review flag, when the answer depends on something the documentation cannot tell you:**

| Reason | When |
|---|---|
| `solution-design` | The client's intended architecture changes the answer, whether stated in their document or still unknown |
| `local-compliance` | Fiscal or legal requirement outside documented VTEX scope *(e.g. a national e-invoicing mandate, fiscal receipts for in-store sales)* |
| `client-prerequisite` | A documented VTEX prerequisite may not be met *(pickup point, ERP billing integration, account topology)* |
| `sources-conflict` | VTEX sources disagree |
| `not-found` | No documentation located |
| `commercial` | Pricing, contract or legal. Not answered; the question goes to the SE in `se_question` |

> **The SE always reviews, so the useful output is not just a verdict. It is a verdict plus where to look
> hard.** A flagged row costs the SE two minutes. The same row answered confidently and wrongly costs a
> correction in front of the client.

### Step 4: Roll-up

Compute **Gross** and **Net**, and **show the arithmetic**: numerator, denominator, excluded items by number.

If the client's scale cannot express "not supported", say so here. **A number that only looks good because the
vocabulary has no failure state is not a result.**

### Step 5: Output

| # | Requirement | Coverage | Answer | Caveat in prose? | Review | Source URL |
|---|---|---|---|---|---|---|

`Caveat in prose?` carries the Step 3.3 outcome: `yes` · `n/a` · `unchecked`. **Never `no`**, because `no`
means the invariant was violated and the row is unfinished.

Keep each row as a structured record too (one JSON object per
requirement) carrying `capability_slug`, `line_class`, `evidence_url` and a verbatim `provenance_quote` from
the cited page, alongside the columns above.

### Step 6: The SE's queue

**Group the flagged rows by reason.** That is the work queue, ordered by where judgment is actually needed.
Then list: requirements with no documented answer · **compliance, security, pricing and SLA, always** ·
contradictions between sources · anything jurisdiction-dependent.

List the `commercial` rows on their own, with each `se_question`, and let the SE decide what happens to
them. Don't route them to a team, and don't draft an answer.

Do not ask the SE to review what was answered from a cited source with no open question.

> 🔒 **One executive summary, not a per-row `SE note` column.** An SE reported the per-row note as **double
> work**: a note beside every row means the reviewer reads the requirement, the answer and a third field, row
> by row, and still never sees why the answer took the shape it did. Reasoning does not decompose by row. The
> expensive decisions are architectural, each one governing dozens of rows, so a per-row field forces you to
> either repeat the same paragraph or fragment it until no fragment carries the argument. **This is the same
> defect as gap bleed, arriving through the layout instead of the prose.**
>
> Write one document instead. It carries every decision and the reasoning behind it, with the architecture
> decisions first, since those are what a reviewer cannot reconstruct from a row and what they most need
> before they start editing. The SE arrives at the rows with the context already loaded.
>
> What belongs in it, beyond the decisions: the coverage roll-up with its arithmetic visible; any verdict that
> changed after a workbook was handed over, flagged explicitly rather than corrected quietly; the solution-set
> policy and its date, so a reader months later can tell *"VTEX cannot do this"* from *"we chose not to answer
> with the product that does it"*; and the open questions that need a human, with the context needed to answer
> them.
>
> Two constraints, both learned the same day. **The summary is a deliverable, not a worker prompt.** One grew
> to 8152 words and cost a worker twenty minutes when it was injected as start-up context. Extract a short
> decisions digest for workers and cap what they receive. And **this is the one artefact to run a humanising
> pass over**, because a person reads it end to end, unlike the rows.

## Validation gates

The rules above that say "advice does not fire, a gate does" are enforced by the scripts in `scripts/`
(Python 3, stdlib only, plus `curl`). Run them **from the opportunity folder**, where they read and write:

```
rfp.config.json      the client's scale, field names, row IDs, language, write-back mapping
                     (copy templates/rfp.config.example.json; every key is optional)
_drafts/*.jsonl      one JSON object per requirement (fields below)
_corpus/             local copy of the cited VTEX pages (corpus.py)
_registry/           canonical verdict per capability (sync_registry.py)
```

**Fill in the config at Step 0**, right after reading the client's document. The config is where the
client's own coverage vocabulary lives: each of their values maps to a role (`full`, `partial`, `none`, `na`,
`clarification`), so the gates reason about roles and never about one client's words. Record the confirmed
architecture there too (`architecture.forbidden_terms`), which makes it a registry entry rather than a
paragraph in a prompt.

Each draft row carries, besides the client's fields: `capability_slug`, `line_class` (`platform` ·
`integrator-build` · `shared` · `not-deliverable`, see Step 3.0), `owners` (on `shared` rows), `caveat_in_prose`, `evidence_url`, `evidence_urls` (extra
sources, e.g. the Trust Center), a verbatim `provenance_quote` of at least 40 characters, `searches` (for rule
9), `review_flag`, `se_review_required`, and `se_question` on `commercial` rows.

| Order | Script | What it does |
|---|---|---|
| 1 | `corpus.py index`, then `corpus.py add <slug> …` | Downloads the pages you cite from VTEX's public docs repos. Refuses `hidden: true`, unpublished and legacy / out-of-solution-set pages at entry, trying the next candidate with the same slug. Use `--worker <id>` for parallel workers |
| 2 | `derive_evidence.py _drafts/*.jsonl` | Sets `evidence_url` from whichever page contains the quote, in the client's locale when that rendition exists. Refuses quotes on zero pages (written from a snippet) or on several articles (ambiguous) |
| 3 | `validate_draft.py _drafts/*.jsonl` | The main gate: scale and required fields, intra-row consistency, `none` ⇔ `not-deliverable`, rule 9, VTEX domain, quote on the cited page, fact tokens, prose (verdict prefix, em dash, process narration, our vocabulary, paid product without disclosure), architecture, registry and cross-row contradictions |
| 4 | `gap_scope.py _drafts/*.jsonl` | Gaps inherited across capabilities, pointer-only gaps, and the asymmetry hard failure. Run across the combined output of every worker |
| 5 | `sync_registry.py _drafts/<section>.jsonl` | After a section passes, records its verdicts so later rows cannot contradict them. `--worker <id>` writes a shard |
| 6 | `verify_quotes.py _drafts/*.jsonl` | Checks each quote on the **live** page the evaluator will open. Reports `UNVERIFIABLE` (not `FAILED`) when the environment serves one cached body for every URL |
| 7 | `rollup.py _drafts/*.jsonl` | Step 4 numbers per section, with the arithmetic and excluded rows shown |
| 8 | `write_back.py <client.xlsx> <new.xlsx> _drafts/*.jsonl` | Transposes into a copy of the client's file (see below). An `owner` column is derived from `line_class` |
| – | `edit_row.py <row> field=value …` | Applies an edit the SE asked for in chat, logs it and re-checks the row (see "Reviewing in chat") |
| 9 | `handoff.py freeze` / `handoff.py reconcile` | Hands the review workbook to the SE and reads their edits back (see "SE review round-trip") |

Every script exits non-zero when it rejects something. **Nothing reaches the client's file until 3 and 4 exit
0.** Report every rejection to the SE with its row ID. Don't fix a row just to make the gate pass.

`scripts/tests/test_gates.py` seeds one bad row per check and asserts it is rejected (`python3 -m unittest
discover -s scripts/tests`). **When you add a check, add its seeded row in the same change** (see "A gate you
have not seen reject anything is not a gate").

**If the session cannot run scripts**, run the same checks by reading the rows and report each one's result to
the SE.

## Reviewing in chat

When the SE chose to review in chat (Step 0.3, question 6):

1. Walk the SE through the Step 6 queue **in batches of about 10 rows**, flagged rows first. For each row,
   show the requirement, the answer, the coverage, who does the work, and the source.
2. The SE answers in their own words ("approve", "make it Partial, the gap is X", "shorter", "wrong
   source"). Turn each change into `edit_row.py <row> field=value …`, with `--by` set to the SE's name.
3. Show the SE what `edit_row.py` printed. If a gate rejects the edit, the edit is still saved, and the SE
   decides whether to adjust it. Never quietly rewrite the SE's text to satisfy a gate.
4. Every edit is logged in `_review/edit_log.jsonl` with the same verdict / source / fact / style classes as
   the spreadsheet round-trip, so the delta report reads the same whichever way the SE reviewed.

Chat and spreadsheet can be combined: fix the hard rows in chat and polish in the sheet. An edit made in chat
counts as ours, so if the same cell is also changed in the returned workbook, reconcile reports a conflict
instead of overwriting either one.

## SE review round-trip

When the SE reviews in the workbook itself:

1. `write_back.py` produces the review workbook, and then `handoff.py freeze review.xlsx` keeps a read-only
   copy of **exactly what was sent**. Send the workbook to the SE.
2. Keep working if you need to. Your drafts may move on while the SE reviews.
3. When the copy comes back, run `handoff.py reconcile _handoff/<name> returned.xlsx _drafts/*.jsonl`. It
   compares three versions of every cell: what was sent, what the SE returned, and your drafts now.
   - The SE changed it and you didn't: their edit wins (applied with `--apply`).
   - You changed it and the SE didn't: yours stays. A two-sided diff would revert it.
   - Both of you changed it: **conflict**. Nothing is applied for that cell, and the SE decides.
4. Read the report: edits are split into verdict, source, fact and style changes, so "the SE rewrote 40
   rows" becomes "3 facts corrected, 37 reworded". Re-run the gates, then update the registry for any
   verdict the SE changed.

**One workbook, one owner at a time.** Never merge a new wave into a workbook while an SE has it.

## Transposing into the client's file

The output of this skill is a **table**. Getting it into the client's spreadsheet is a separate step.

> 🔒 **Never write the answer into the file the client sent.** A new file, always, with a name that cannot
> collide. On shared storage there is no undo, and the original is the only reference left to compare against.

**Edit the `.xlsx` XML in place rather than rewriting the workbook** with a library like `openpyxl`. A rewrite
silently drops the drawings, images and Excel Tables the client embedded. *(Measured: a first attempt filled
all 140 cells correctly and destroyed 5 drawings and 1 image without raising anything. The only signal was the
file dropping from 185 KB to 80 KB.)*

`write_back.py` does exactly this. It finds each row by the ID in the client's key column, writes the mapped
fields (`write_back` in the config) and copies every other zip entry byte for byte. It refuses to write to the
input path or to an existing file, and it compares drawing/media/table counts before and after. Run it with
`--check` first: that lists draft rows with no matching ID and client rows left unanswered, and writes nothing.

**If the session cannot run scripts or reach the file:** output the table and say plainly that it must be
transposed by hand.

## Not in this version

- **A coverage summary tab in the client's workbook.** `rollup.py` prints the numbers; adding them as a tab
  depends on each client's layout.
- **Historical response corpus.** It belongs as a *verification* layer (checking a draft against what VTEX has
  promised before), not as a source for generating answers.
- **Document parsing.** The RFP arrives as text; extraction happens before this skill runs.

## Version history

- **1.14.0 (2026-09-30).** Section profiles (`full` · `security` · `rfi` · `commercial`) decided at Step 0:
  security questionnaires skip the architecture step and require SE review on every row, and commercial rows
  are left to the SE. Rule 6 (Trust Center on certification rows) is now a gate. Review in chat with
  `edit_row.py`, and the review mode is always asked. Every question is still researched fresh; there is no
  answer library.
- **1.13.0 (2026-09-30).** Technical depth now follows the reviewing SE's direction: native rows go deep,
  custom rows stay in business language. Step 3.0 (A1): `line_class` is read off the answer, a `shared`
  class carries a VTEX + SI + client split, and the owner is derived. SE review round-trip (A3): `handoff.py`
  freezes what was sent and reconciles with a three-sided diff. Capability matrices stay optional; the
  latest documentation always wins.
- **1.12.0 (2026-09-30).** The validation and write-back scripts are back, generalized: `rfp.config.json`
  now carries the client's scale, field names, row IDs, language and column mapping. Seeded-bad-row tests
  cover every gate. Added `rollup.py` for Step 4.
- **1.11.0 (2026-09-30).** Migrated into `vtex-se-skills`. Client and colleague names removed. The capability
  matrices are no longer bundled or referenced by file. `vtex-architect` and `vtex-expert` became optional
  external dependencies. The validation scripts were pulled pending generalization, so their checks are now
  listed under "Validation gates" to run by hand.
- **1.10 (2026-08-18).** Audited a full review thread against this file. Added row formatting for reviewers.
  Wrote up open questions A1 and A3. Marked the technical-depth rule as open.
- **1.9 (2026-08-18).** Step 1b: how large RFPs are split by section into subagent workers.
- **1.8 (2026-08-18).** Live QA of `vtex-architect` / `vtex-expert`. Internal reference files are never
  citable.
- **1.7 (2026-08-18).** Wired in `vtex-architect` (architecture reasoning) and `vtex-expert` (platform
  mechanics).
- **1.6 (2026-08-18).** Step 0.3 grounds the architecture proposal in capability matrices.
- **1.5 (2026-08-18).** Step 0.3 asks for the target language and whether the SE reviews before delivery.
- **1.4 (2026-08-11).** Rule 9 (two distinct searches before "not supported") and the validation gate.
- **1.3 (2026-08-05).** Answer in the client's language, and cite the doc rendition in that language.
- **1.2 (2026-08-05).** Precedent from comparable clients, Rocketlane scoped to commercial context, client
  may dictate the answer format, ask the SE after reading.
- **1.1 (2026-08-05).** Step 0.2: prior contact (Granola, Drive).
- **1.0 (2026-08-05).** Cut back to the actual job. Removed opportunity lookup, architecture documents and
  account inspection, which don't exist at RFP stage.
