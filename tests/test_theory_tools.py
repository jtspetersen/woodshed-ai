# Woodshed AI — Theory Tool Schema Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the tool schemas and dispatch mapping."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.theory.tools import MUSIC_TOOLS, TOOL_FUNCTIONS


def test_tool_schemas_valid():
    """All tool schemas have required fields."""
    for tool in MUSIC_TOOLS:
        assert tool["type"] == "function", f"Tool type must be 'function'"
        fn = tool["function"]
        assert "name" in fn, "Tool must have a name"
        assert "description" in fn, f"Tool {fn['name']} must have a description"
        assert "parameters" in fn, f"Tool {fn['name']} must have parameters"
        params = fn["parameters"]
        assert params["type"] == "object", f"Tool {fn['name']} params must be type 'object'"
        assert "properties" in params, f"Tool {fn['name']} must have properties"
        assert "required" in params, f"Tool {fn['name']} must have required fields"
        print(f"  {fn['name']}: OK ({len(params['properties'])} params)")


def test_all_tools_have_functions():
    """Every tool schema has a matching function in TOOL_FUNCTIONS."""
    for tool in MUSIC_TOOLS:
        name = tool["function"]["name"]
        assert name in TOOL_FUNCTIONS, f"Tool '{name}' has no matching function"
        assert callable(TOOL_FUNCTIONS[name]), f"Tool '{name}' function is not callable"
        print(f"  {name}: mapped to {TOOL_FUNCTIONS[name].__name__}")


def test_all_functions_have_schemas():
    """Every function in TOOL_FUNCTIONS has a matching tool schema."""
    schema_names = {t["function"]["name"] for t in MUSIC_TOOLS}
    for name in TOOL_FUNCTIONS:
        assert name in schema_names, f"Function '{name}' has no matching tool schema"


def test_dispatch_works():
    """Test that dispatching a tool call actually works."""
    result = TOOL_FUNCTIONS["analyze_chord"](chord_symbol="C")
    assert "error" not in result
    assert result["root"] == "C"
    print(f"  dispatch analyze_chord('C') -> root={result['root']}, notes={result['notes']}")


if __name__ == "__main__":
    tests = [
        ("Tool schemas valid", test_tool_schemas_valid),
        ("All tools have functions", test_all_tools_have_functions),
        ("All functions have schemas", test_all_functions_have_schemas),
        ("Dispatch works", test_dispatch_works),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            print(f"  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
