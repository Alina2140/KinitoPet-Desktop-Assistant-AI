"""Tests for multi-value fact splitting and formatting."""

from kinito.memory.fact_values import (
    compact_fact_storage,
    format_fact_values,
    normalize_fact_value_list,
    split_fact_values,
)


def test_split_fact_values_comma_list():
    assert split_fact_values("Drawing, Reading, Crochet") == [
        "Drawing",
        "Reading",
        "Crochet",
    ]


def test_split_fact_values_oxford_comma_and():
    assert split_fact_values("Drawing, Reading, and Crochet") == [
        "Drawing",
        "Reading",
        "Crochet",
    ]


def test_split_fact_values_and_without_commas():
    assert split_fact_values("Lola and Mae") == ["Lola", "Mae"]


def test_split_fact_values_dedupes_case_insensitive():
    assert split_fact_values("Drawing, drawing, READING") == ["Drawing", "READING"]


def test_format_fact_values_joins_naturally():
    assert format_fact_values(["Drawing"]) == "Drawing"
    assert format_fact_values(["Drawing", "Reading"]) == "Drawing and Reading"
    assert format_fact_values(["Drawing", "Reading", "Crochet"]) == (
        "Drawing, Reading, and Crochet"
    )


def test_compact_fact_storage_single_vs_list():
    assert compact_fact_storage(["Drawing"]) == "Drawing"
    assert compact_fact_storage(["Drawing", "Reading"]) == ["Drawing", "Reading"]


def test_normalize_fact_value_list_from_mixed_input():
    assert normalize_fact_value_list(["Drawing, Reading", "Crochet"]) == [
        "Drawing",
        "Reading",
        "Crochet",
    ]
