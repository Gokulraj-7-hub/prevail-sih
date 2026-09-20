"""Scenario-safe, leakage-aware splitting (master prompt Sec 2.4, Phase 20).

Never randomly splits adjacent temporal windows from the same scenario across
train/test. Splits at the scenario level, stratified by whether the scenario
contains an attack, so both splits see a comparable benign/attack mix without
ever sharing a scenario's windows across the boundary.
"""
from __future__ import annotations

import random

import pandas as pd


def scenario_train_test_split(
    scenario_meta: pd.DataFrame,
    test_fraction: float = 0.25,
    seed: int = 42,
) -> tuple[list[str], list[str]]:
    rng = random.Random(seed)
    train_ids: list[str] = []
    test_ids: list[str] = []
    for has_attack, group in scenario_meta.groupby("has_attack"):
        ids = list(group["scenario_id"])
        rng.shuffle(ids)
        n_test = max(1, round(len(ids) * test_fraction))
        test_ids.extend(ids[:n_test])
        train_ids.extend(ids[n_test:])
    return sorted(train_ids), sorted(test_ids)


def assert_no_scenario_overlap(train_ids: list[str], test_ids: list[str]) -> None:
    overlap = set(train_ids) & set(test_ids)
    if overlap:
        raise ValueError(f"Scenario leakage detected: {overlap} present in both train and test")
