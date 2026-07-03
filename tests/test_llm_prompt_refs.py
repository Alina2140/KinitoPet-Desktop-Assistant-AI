"""Ensure every prompts.* reference in kinito/ resolves in content.llm_prompts."""

from __future__ import annotations

import ast
from pathlib import Path

from content import llm_prompts as prompts


def _prompt_attribute_refs(package_dir: Path) -> set[str]:
    refs: set[str] = set()
    for path in package_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "prompts"
            ):
                refs.add(node.attr)
    return refs


def test_all_referenced_llm_prompts_exist():
    repo_root = Path(__file__).resolve().parents[1]
    missing = sorted(
        name
        for name in _prompt_attribute_refs(repo_root / "kinito")
        if not hasattr(prompts, name)
    )
    assert not missing, f"Missing llm_prompts attributes: {missing}"


def test_core_ai_hint_prompts_are_non_empty_strings():
    for name in (
        "POEM_PROMPT",
        "FUN_FACT_PROMPT",
        "HUG_PROMPT",
        "JOKE_PROMPT",
        "IDLE_PROMPT",
        "RANDOM_QUESTION_PROMPT",
        "SYSTEM_PROMPT",
    ):
        value = getattr(prompts, name)
        assert isinstance(value, str) and value.strip(), name
