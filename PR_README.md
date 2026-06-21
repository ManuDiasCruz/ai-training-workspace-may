# Pydantic issue #13112 — `AliasPath` with an integer first segment

Upstream issue: https://github.com/pydantic/pydantic/issues/13112

Upstream base: `pydantic/pydantic@363728f` (latest `main` at the time of the
fix — "Recognise `WindowsPath` as a schema type (#13326)").

## What this PR contains

This branch (`v1-t1-pydantic`) is opened against `v1-t1-pydantic-base`, which
holds pristine copies of the upstream files this fix touches. The diff in
this PR therefore reads as a clean, minimal pydantic-style contribution.

Files changed in this PR:

| File | Purpose |
|------|---------|
| `pydantic/aliases.py` | Relax `AliasPath.__init__` signature to accept `int \| str` for the first argument. Tiny typing nit on `search_dict_for_path`. |
| `tests/test_aliases.py` | Two new regression tests: the happy path (`AliasPath(0)` indexing into a list/tuple) and the short-list missing-index error path. |
| `patches/issue-13112-pydantic.patch` | Captures the diff in `pydantic/_internal/_generate_schema.py` (see below). Apply with `git apply` to the corresponding upstream commit. |

`pydantic/_internal/_generate_schema.py` is ~140 KB and lives outside the
base branch on purpose — including it here would dwarf the meaningful diff.
The schema-side change is small (≈10 lines + three short helpers) and is
included verbatim in `patches/issue-13112-pydantic.patch`, which is what a
pydantic maintainer would actually review.

## The bug (#13112)

```python
from pydantic import BaseModel, Field, AliasPath

class Row(BaseModel):
    id: int = Field(validation_alias=AliasPath(0))
    name: str = Field(validation_alias=AliasPath(1))

Row.model_validate([42, "alice"])
```

On unpatched `main`, the class definition fails at schema-build time with
an opaque error from pydantic-core:

```
SchemaError: Error building "model" validator:
  SchemaError: Error building "model-fields" validator:
  TypeError: failed to extract enum ValidationAlias ('Str | AliasPath | AliasChoices')
    - variant AliasPath: TypeError: The first item in an alias path should be a string
```

pydantic-core's `LookupPath` requires the first item of an alias path to be
a string (it's used to look up a key in a dict-like input). That makes
`AliasPath(0)` impossible to express directly as a pydantic-core lookup
path, even though the public docs/typing already document `AliasPath` as
accepting integer segments.

## The fix

Keep the public `AliasPath(int, ...)` surface and translate it into
something pydantic-core can handle, entirely in the pydantic Python
package. No pydantic-core (Rust) changes are required.

The translation has two halves:

1. **Stringify the integer first segment** when converting an `AliasPath`
   (or an `AliasPath` nested inside `AliasChoices`) to a pydantic-core
   lookup path. `AliasPath(0)` becomes the lookup path `['0']` for the
   core-schema, which pydantic-core's `LookupPath` accepts.

2. **Wrap the model-fields schema** with a `no_info_before_validator_function`
   when at least one field in the model uses an int-first `AliasPath`. The
   wrapper converts a top-level `list`/`tuple` input to a dict keyed by
   stringified indices (`['a', 'b']` → `{'0': 'a', '1': 'b'}`). The fields
   validator then runs against this dict and resolves the `AliasPath(0)`
   lookups as `'0'` → `'a'`, etc.

The wrapper is only applied when needed (no overhead for models that
don't use int-first `AliasPath`), and it leaves dict inputs untouched
(so existing validation paths continue to work without changes).

## Compatibility & regression risk

* **No public API changes** other than relaxing `AliasPath.__init__`'s
  first-arg annotation from `str` to `str | int` — which matches what the
  docstring already advertises ("a list of string or integer aliases")
  and what pydantic-core already accepts for non-first segments.
* **No pydantic-core (Rust) changes.** The fix is fully contained in the
  pydantic Python package, so it doesn't need a coordinated release.
* **Targeted scope.** The before-validator wrapper is only attached to
  models that actually declare an int-first `AliasPath`. Models that
  don't use this feature get exactly the same core-schema as before.
* **Existing tests.** The relevant slice of the upstream test suite still
  passes locally (`tests/test_aliases.py`, `tests/test_construction.py`,
  `tests/test_fields.py`, `tests/test_main.py`, `tests/test_dataclasses.py`,
  `tests/test_root_model.py`, `tests/test_create_model.py`,
  `tests/test_edge_cases.py`, `tests/test_typing.py`: 1082 passed, 61
  skipped, 2 xfailed).
* **Out of scope (for now).** The same shape would be useful for
  `@pydantic.dataclasses.dataclass` and `TypedDict`, but their schema
  generators are separate and weren't part of the reproducer in #13112.
  Easy follow-up if maintainers want it — the helper functions are
  reusable.

## Tests added

Both in `tests/test_aliases.py`:

* `test_validation_alias_path_with_integer_first_segment` — happy paths:
  list input, tuple input, and `AliasPath(int)` inside `AliasChoices`
  alongside a string alias.
* `test_validation_alias_path_integer_first_segment_missing_index` — the
  short-list case raises a `ValidationError` with `type=='missing'`.

Run locally with:

```bash
pytest tests/test_aliases.py -k integer_first_segment
```

## Notes for the reviewer

This PR is opened on a personal training repo because session
authorization is scoped to `manudiascruz/ai-training-workspace-may`. The
intended target for a real upstream contribution would be a PR against
`pydantic/pydantic`'s default branch with the same three files modified
as described above.
