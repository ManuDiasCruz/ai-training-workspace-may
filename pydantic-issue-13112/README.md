# pydantic issue #13112 — `AliasPath` with `int` first segment

Upstream issue: https://github.com/pydantic/pydantic/issues/13112

## Problem

`AliasPath` is documented (via type hints) to take a `str` as the first
segment and `str | int` for subsequent segments, but the constructor does
not validate the first segment at runtime. Passing an `int` as the first
arg — e.g. `Field(validation_alias=AliasPath(0))` — succeeds, and the
breakage surfaces much later as an opaque `SchemaError` when the model
class is being built:

```
pydantic_core._pydantic_core.SchemaError: Error building "model" validator:
  SchemaError: Error building "model-fields" validator:
  TypeError: failed to extract enum ValidationAlias ('Str | AliasPath | AliasChoices')
- variant AliasPath (AliasPath): TypeError: failed to extract field
  ValidationAlias::AliasPath.0, caused by TypeError: The first item in an
  alias path should be a string
```

The user has no signal that the problem is the `0` they passed several
lines earlier.

## Fix in this branch

Validate `first_arg` at `AliasPath.__init__` time. If it isn't a `str`,
raise a `TypeError` that names the offending value type and links to the
issue. This is the fallback the issue author explicitly asked for:

> If full implementation isn't feasible, a clear `TypeError` raised
> during `AliasPath` initialization rather than during model definition
> would still be an improvement.

Full integer-as-first-segment indexing (so a model can validate from a
top-level `list` input) requires changes in `pydantic-core` (Rust):
`LookupPath::from_list` in `pydantic-core/src/lookup_key.rs` hard-codes
the first item to `PathItemString`, and the lookup helpers assume a dict
at the top level. That work is out of scope for a Python-only patch.

## Layout

- `fix.patch` — the diff to apply on a `pydantic/pydantic` checkout.
- `aliases.py` — the modified `pydantic/aliases.py` (for easy review).
- `test_regression.py` — the new regression test (also added upstream in
  `tests/test_aliases.py`).
- `repro.py` — a small script that exercises the before/after behavior.

## Applying

```
git clone https://github.com/pydantic/pydantic.git
cd pydantic
git checkout main
git apply /path/to/fix.patch
pytest tests/test_aliases.py
```

## Compatibility / regression risk

- Existing code that constructed `AliasPath` with an integer first
  segment was already broken — it failed at model definition. Such code
  now fails at `AliasPath` construction with a clearer message.
- No behavior change for any valid call (`AliasPath('a')`,
  `AliasPath('a', 1)`, `AliasPath('a', 'b', 'c')`).
- 483 tests pass across `tests/test_aliases.py`,
  `tests/test_construction.py`, `tests/test_fields.py`, and
  `tests/test_main.py` after applying the patch.
