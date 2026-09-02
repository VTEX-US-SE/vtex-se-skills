# VAMS cheat sheet (for this skill)

VAMS (VTEX Architecture Modeling Specification) is a JSON DSL for VTEX solution
architectures — not a diagramming format itself. This skill turns a VAMS
document into an actual Miro board. Full spec: the `vams` repo's
`VTEX-Architecture-Modeling-Specification-VAMS.md` and
`schemas/solution-architecture.schema.json` (a copy of the schema is bundled
here as `solution-architecture.schema.json` for reference).

## Document shape

```json
{
  "name": "string",
  "level": "Highlevel | Detail | Sequence",
  "domain": "string (optional)",
  "metadata": { "...": "optional governance/commerce fields" },
  "architecture": {
    "nodes": [ ... ],
    "flows": [ ... ],
    "dataEntities": [ ... ],
    "environments": [ ... ]
  }
}
```

Only `name`, `level`, and `architecture` are required at the root.

## Nodes (`architecture.nodes[]`)

| Field            | Notes                                                                 |
| ---------------- | ---------------------------------------------------------------------|
| `id`             | Unique within the document.                                          |
| `name`           | Human label. **This skill matches nodes to template regions by this field** (case/whitespace/punctuation-insensitive). |
| `type`           | `Group`, `Platform`, `System`, `Application`, `Middleware`, `Component`. |
| `parent`         | Optional — id of the containing node. Nodes without `parent` are roots. |
| `environment`    | Free-form string (e.g. `vtex`, `vtex-io`, `external`, `merchant`). Drives shape styling together with `type`/`implementation`. |
| `implementation` | `Native` or `Custom`. Also drives shape styling.                      |

Hierarchy rules (informational — this skill does not re-validate them):

| Parent      | Allowed Children                                     |
| ----------- | ------------------------------------------------------|
| Group       | Platform, System, Application, Middleware, Component  |
| Platform    | Application, Component                                |
| System      | Application, Component                                |
| Application | Component                                              |
| Middleware  | Component                                              |

`Component` never has children.

## Flows (`architecture.flows[]`)

| Field         | Notes                                                    |
| ------------- | --------------------------------------------------------|
| `id`          | Unique within the document.                              |
| `type`        | `Data` or `Event`.                                       |
| `origin`      | Source node id.                                          |
| `destination` | Target node id.                                          |
| `timing`      | `Async` or `Real-Time` (defaults to `Async` if absent).  |
| `data`        | Array of `dataEntities` ids exchanged (optional).        |

## Data entities (`architecture.dataEntities[]`)

`{ "id": "...", "name": "..." }` — referenced by `flows[].data`. Rendered as a
connector caption `[Entity One, Entity Two]`.

## What this skill does NOT do

- It does not validate the document against the JSON Schema (bundled here for
  reference only). If strict validation matters, check the document against
  `solution-architecture.schema.json` separately (e.g. with the `ajv` CLI, or
  by eye for the required fields above) before generating a diagram.
- It does not interpret `metadata.commerce` (business context) — that's for
  Atlas validation, not for drawing the board.
