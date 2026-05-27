"""Regression test added in ``tests/test_aliases.py`` upstream.

Mirrored here for easy review of the patch in this repo. Run against a
pydantic checkout that has the ``aliases.py`` change applied:

    pytest pydantic-issue-13112/test_regression.py
"""

import pytest

from pydantic import AliasPath


def test_alias_path_int_first_segment_raises_type_error():
    with pytest.raises(TypeError, match=r'first argument.*must be a `str`'):
        AliasPath(0)
    with pytest.raises(TypeError, match=r'first argument.*must be a `str`'):
        AliasPath(0, 'name')
