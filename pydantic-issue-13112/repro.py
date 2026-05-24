"""Reproducer for pydantic issue #13112.

Before the fix, ``AliasPath(0)`` builds successfully but the model class
construction fails with an opaque ``SchemaError`` referencing
``pydantic-core`` internals.

After the fix, ``AliasPath(0)`` itself raises a clear ``TypeError`` that
points at the issue, before any model is built.
"""

from pydantic import AliasPath, BaseModel, Field


def main() -> None:
    try:
        AliasPath(0)
    except TypeError as exc:
        print(f'OK: AliasPath(0) raised TypeError: {exc}')
        return

    try:

        class Row(BaseModel):
            id: int = Field(validation_alias=AliasPath(0))

    except Exception as exc:  # noqa: BLE001
        print(f'BUG (pre-fix): model build failed with: {type(exc).__name__}: {exc}')
        return

    print('UNEXPECTED: model built without error')


if __name__ == '__main__':
    main()
