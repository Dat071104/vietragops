# Gate 21 — External Register Structural Survey

Status: C2 complete. This is a structural survey only; no auditor classification is used here.

## Source and unit definition

The four pinned files are the `evolution.json` files at commit
`888c779a0fe735f612ca62bdd1fdd7c9e6bf8701` in
`Octobrist/MCPEvol-Bench`.

The counting unit called a **tool-level record** below is one tool key under one
top-level server object. A **server entry** is one top-level server object in one
stage file. A **(server, tool) pair** is the pair of those two keys, deduplicated
across all four files. The four files are cumulative stage snapshots, so the
same pair can occur in more than one file.

## Exact top-level schema

Each file is a JSON object. Its keys are server/package identifiers. Each server
value is an object containing:

```text
server_name -> {
  <tool_name>: <evolution record or tool-level summary>,
  ...,
  "mutation_type": "TOOL" | "PARAM" | "DESC",
  "task_idx": integer
}
```

The metadata keys are at the same level as one or more tool keys; the file is
not a list of normalized evolution records. The four stage counts are:

| Stage file | Top-level server entries | Tool-level records |
|---|---:|---:|
| `HYBRID/evolution.json` | 89 | 92 |
| `HYBRID/HYBRID/evolution.json` | 86 | 160 |
| `HYBRID/HYBRID/HYBRID/evolution.json` | 85 | 125 |
| `HYBRID/HYBRID/HYBRID/HYBRID/evolution.json` | 87 | 110 |
| **Total across files** | **347** | **487** |

Across the four files there are **298 distinct (server, tool) pairs**. There are
**189 duplicate pair observations**, derived as `487 tool-level records - 298
distinct pairs`; this is expected from cumulative stages and is not a count of
unique mutations.

## Mutation types

The full observed set is exactly `PARAM`, `DESC`, and `TOOL`.

| `mutation_type` | Tool-level records |
|---|---:|
| `PARAM` | 141 |
| `DESC` | 152 |
| `TOOL` | 194 |
| **Total** | **487** |

Per-stage mutation counts, with the unit still **tool-level records**, are:

| Stage | `PARAM` | `DESC` | `TOOL` | Total records |
|---|---:|---:|---:|---:|
| 1 | 47 | 41 | 4 | 92 |
| 2 | 21 | 34 | 105 | 160 |
| 3 | 43 | 28 | 54 | 125 |
| 4 | 30 | 49 | 31 | 110 |

## Parameter surfaces

### Parameter additions

`parameter_additions` occurs in **110 PARAM records** and contains **312
parameter items**. Every one of those **312 parameter items** has
`required: false`; **0 parameter items** have `required: true`.

This is the most decision-relevant result for the required-field defect class:
the explicit `parameter_additions` surface contains no required addition. The
register therefore does not expose the same added-required-field surface that
Gate 19 measured.

The addition item keys are consistently:

```text
name, type, required, description
```

The `type` field is descriptive text rather than one normalized type enum. Its
observed values include `string`, `boolean`, `bool`, `int`, `number`, `object`,
array descriptions, and enum descriptions.

### Other PARAM fields

Across **141 PARAM records**:

- all **141 records** have `evolution_summary` and `diff_hunks`;
- **25 records** have `parameter_changes`, containing **61 parameter items**;
- **6 records** have `parameter_removals`, containing **11 parameter items**;
- **19 records** have `tool_description_change`.

Within the **61 parameter-change items**, the action/change values are:

- `action: add`: **27 items**;
- `action: remove`: **18 items**;
- `change_type: constraint`: **7 items**;
- `change_type: required`: **6 items**;
- `change_type: type`: **3 items**.

The `required` boolean appears on **45 parameter-change items**: **4 true** and
**41 false**. This is a different surface from `parameter_additions`; the two
required `action: add` items are `scope` and `priority`, while the two required
removal items are not additions. The 312-item `parameter_additions` count above
remains the primary count for that field.

## Shape by mutation type and audit-relevant sufficiency

### `PARAM` — partial contract-change description, not a normalized pair

The register explicitly names added parameters and, on subsets, changed or
removed parameters. It does not provide a normalized `old_argument_set` and
`new_argument_set` object, nor a target value from an expected tool call. Some
named change items provide a local correspondence for that named parameter, but
the complete old/new argument sets still require reading code or a live server.

`diff_hunks` occur in all **141 PARAM records**. The **357 diff hunks** have
`old_code`, `new_code`, and `file_name`; **6 hunks** also have `anchor_code`.
These are source-code snippets. A representative `old_code` is a JavaScript
validator/registration/handler fragment and `new_code` is the changed fragment.
They are not full, normalized JSON Schema declarations.

Conclusion for `PARAM`: **(a) old argument set: not fully declared; (b) new
argument set: only named additions/changes are declared; (c) correspondence:
partial for named changes, not a complete contract correspondence.** A target
argument value is not present in the PARAM record.

### `DESC` — description correspondence only

There are **152 DESC records**. **138 records** contain a nested `tool` object
with `original_description` and `modified_description`; **14 records** contain
those two fields at the record root. **94 records** contain `parameters`, with
**425 parameter-description items** keyed by `parameter_name`,
`original_description`, and `modified_description`.

DESC therefore gives before/after description pairs for the affected prose, but
it does not declare an old/new argument set or an expected argument value.

Conclusion for `DESC`: **(a) old argument set: no; (b) new argument set: no;
(c) correspondence: description-field correspondence only, outside the
argument-target schema of the frozen auditor.**

### `TOOL` — mixed summaries and a small full-new-tool subset

There are **194 TOOL records**. Their tool-level values are **89 strings**, **83
lists**, and **22 objects**. The **22 object records** contain a full-looking
`name`, `description`, and `input_schema` configuration; only **1** also has an
`output_schema`, and **1** has `annotations`. The other **172 TOOL records** are
summary/list surfaces rather than full tool contracts.

The TOOL records do not declare the old tool contract or a complete
old-to-new correspondence. Some summary records identify a new tool or a
migration target in prose/data, but that is not a normalized argument-pair
register.

Conclusion for `TOOL`: **(a) old argument set: no; (b) new argument set: only
22 records provide a full-looking new configuration; (c) correspondence: no
complete old/new correspondence.** TOOL is not expressible as an argument
target item for the frozen auditor without additional source or oracle data.

## `old_code` / `new_code` status

`old_code` and `new_code` are source-code diffs, not full schema declarations.
They show local implementation/registration fragments such as validators,
`server.tool` registrations, or handlers. A schema must therefore be inferred
from implementation snippets when those fields are used to recover all
arguments. That inference is weaker than a declared contract and is not silently
performed by this gate. The separate `TOOL.new_tool_config.input_schema` subset
is a declared new configuration, but it still does not supply the corresponding
old configuration.

## `task_idx` and expected calls

The register contains `task_idx` on each server entry. Across the **347 server
entries**, there are **73 distinct task_idx values**, ranging from **0 through
84**. Because a server entry can contain multiple tool keys, the same
`task_idx` is repeated across tool-level records; it is not a unique record id.

The four downloaded files contain no `expected_tool_call`, target argument
value, or old trace field. Gate 19's previously frozen public-release
observation records that the separate `test_cases.json` file has **393 records**
and includes `idx`, `tool_calls`, `question`, and trajectory/evaluation fields.
However, C2 did not re-download that 15.8 MB file under Gate 21's approximately
2 MB acquisition budget, and the pinned runner reads test cases by their
`idx` while selecting mutation-involved cases by server/tool membership; it does
not evidence a `task_idx -> idx` join.

Therefore the answer is **UNVERIFIED**: an expected call could be recovered
without the 3.4 GB archive only if a separate, declared join from `task_idx` to
the small `test_cases.json` records is established. The current four-file
register and runner do not establish that join. The 3.4 GB archive is not a
substitute for a declared expected-call join; it would provide versioned server
implementations and runtime context.

## C2 conclusion

The register is structurally rich and does expose real before/after source
fragments, named parameter changes, description pairs, and some full new tool
configurations. It is not, by itself, a normalized old/new contract-pair plus
expected-call register consumable by the frozen argument-level auditor. The
explicit `parameter_additions` surface contains **312 optional parameter items
and 0 required parameter items**, so it does not provide the central required
added-field defect class. C3 must use the separately declared external rights
object rather than reusing the local Gate 19 rights.
