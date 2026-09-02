# Stakeholder Register — Ops Data Model

This is the machine-readable side of the scout. Use it in Step 5 to emit one record per stakeholder, and hand this file to whoever builds the ops profiling tool (spreadsheet, Airtable/Notion, CRM object, or a small app). The schema is intentionally flat where it can be and nested only for the repeating structures (career history, convergence points).

## Table of contents
1. Field definitions
2. JSON schema (per stakeholder)
3. Spreadsheet column layout (flat version for ops)
4. Controlled vocabularies

---

## 1. Field definitions

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable key, e.g. `kfc-th-natcha` |
| `deal` | string | Deal/account name |
| `name` | string | Full name |
| `preferred_name` | string | Nickname used in-market (e.g. "May") |
| `email` | string | Business email |
| `company_entity` | string | The *legal entity* they belong to (matters for franchise/holding structures) |
| `title` | string | Current title |
| `title_confidence` | enum | `confirmed` / `inferred` |
| `title_source` | string | Where confirmed (LinkedIn URL, email signature, press) |
| `location` | string | City/region |
| `scope` | enum | `regional` / `local` / `global` — where they sit in the org |
| `linkedin_url` | string | Direct profile URL |
| `connection_degree` | enum | `1st` / `2nd` / `3rd+` / `unknown` |
| `mutual_connections` | array<string> | VTEX-side people who can warm-intro |
| `dmu_role` | enum | See vocab; one primary (secondary allowed in notes) |
| `influence_level` | enum | `high` / `medium` / `low` |
| `support_stance` | enum | `champion` / `supporter` / `neutral` / `skeptic` / `blocker` |
| `champion_score` | integer | 0–5 (see profiling-signals §5) |
| `tenure` | string | Time in current role (drives CP-9) |
| `career_history` | array<object> | Prior roles + platform experience (see nested schema) |
| `convergence_points` | array<object> | Tagged CPs (see nested schema) |
| `risk_flags` | array<string> | e.g. `incumbent-owner`, `competitor-loyalty`, `governance-veto` |
| `engagement_recommendation` | string | One line: what to do with this person |
| `overall_confidence` | enum | `confirmed` / `partial` / `unconfirmed` |
| `last_updated` | date | ISO date of last scout |
| `source_refs` | array<string> | URLs / thread IDs backing the record |

**Nested — career_history item:**
| Field | Type | Notes |
|---|---|---|
| `employer` | string | Company |
| `role` | string | Title held |
| `years` | string | e.g. `2019–2022` |
| `platform_experience` | array<string> | Commerce platforms touched (VTEX, SFCC, commercetools, Shopify, Magento, Hybris, Mirakl, custom…) |

**Nested — convergence_point item:**
| Field | Type | Notes |
|---|---|---|
| `type` | enum | `CP-1`…`CP-10` (see profiling-signals §1) |
| `description` | string | Plain-language statement |
| `evidence` | string | Source/quote/URL |
| `implication` | string | The play it implies |
| `confidence` | enum | `confirmed` / `inferred` |

---

## 2. JSON schema (per stakeholder)

```json
{
  "id": "kfc-th-natcha",
  "deal": "KFC Thailand — Ecommerce Platform",
  "name": "Natcha Chittavimongkon",
  "preferred_name": "May",
  "email": "natcha.chittavimongkon@yum.com",
  "company_entity": "Yum! Restaurants International (Thailand)",
  "title": "E-Commerce Manager, Digital",
  "title_confidence": "confirmed",
  "title_source": "https://www.linkedin.com/in/...",
  "location": "Bangkok / Samut Prakan, TH",
  "scope": "local",
  "linkedin_url": "https://www.linkedin.com/in/...",
  "connection_degree": "3rd+",
  "mutual_connections": [],
  "dmu_role": "champion",
  "influence_level": "medium",
  "support_stance": "supporter",
  "champion_score": 4,
  "tenure": "~1 year",
  "career_history": [
    {
      "employer": "Prior retailer",
      "role": "Head of Ecommerce",
      "years": "2020–2023",
      "platform_experience": ["VTEX"]
    }
  ],
  "convergence_points": [
    {
      "type": "CP-8",
      "description": "Hired to lead the digital/ecommerce replatform",
      "evidence": "Role scope + initiated outreach",
      "implication": "Personal win tied to project success — cultivate as champion",
      "confidence": "inferred"
    }
  ],
  "risk_flags": [],
  "engagement_recommendation": "Primary working champion — arm with internal business case",
  "overall_confidence": "confirmed",
  "last_updated": "2026-08-19",
  "source_refs": ["gmail-thread-id", "linkedin-url"]
}
```

A full register is just `{ "deal": "...", "generated": "ISO", "stakeholders": [ {…}, {…} ] }`.

---

## 3. Spreadsheet column layout (flat version for ops)

For a spreadsheet/CRM, flatten the nested fields into delimited cells:

```
id | deal | name | preferred_name | email | company_entity | title | title_confidence |
location | scope | linkedin_url | connection_degree | mutual_connections | dmu_role |
influence_level | support_stance | champion_score | tenure | platforms_worked |
convergence_points | risk_flags | engagement_recommendation | overall_confidence |
last_updated | source_refs
```

- `platforms_worked` = comma-joined union of `career_history[].platform_experience`
- `convergence_points` = `CP-x: description` per line within the cell
- `mutual_connections`, `risk_flags`, `source_refs` = comma-joined

This flat layout is what an SE can paste into Sheets/Airtable immediately; the JSON is the source of truth for a tool.

---

## 4. Controlled vocabularies

- **scope**: `global` | `regional` | `local`
- **dmu_role**: `economic-buyer` | `technical-decision-maker` | `champion` | `coach` | `influencer` | `end-user` | `blocker` | `procurement`
- **influence_level**: `high` | `medium` | `low`
- **support_stance**: `champion` | `supporter` | `neutral` | `skeptic` | `blocker`
- **connection_degree**: `1st` | `2nd` | `3rd+` | `unknown`
- **convergence type**: `CP-1`…`CP-10` (profiling-signals §1)
- **confidence**: `confirmed` | `inferred` (per fact); `confirmed` | `partial` | `unconfirmed` (per person)

Keep vocabularies fixed so the register stays filterable and the ops tool can aggregate (e.g., "show all high-influence skeptics", "everyone with competitor incumbency", "all warm-path 2nd-degree buyers").
