#!/usr/bin/env python
"""Milestone 9: defensive what-if simulator demo -- baseline vs. counterfactual
K-step forecast on the same held-out scenario/window used in Milestone 7-8's
demos (docs/experiments/attack-stage.md Case B)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from prevail.attack_stage.model import load_stage_model, predict_stage_probs  # noqa: E402
from prevail.common.schema import ATTACK_STAGES  # noqa: E402
from prevail.intervention.interventions import block_destination_port, isolate_host  # noqa: E402
from prevail.intervention.simulator import (  # noqa: E402
    build_counterfactual_history, compute_modified_current_state, out_of_distribution_score, is_out_of_distribution,
)
from prevail.rollout.rollout import k_step_rollout_batch  # noqa: E402
from prevail.world_model.model import PrevailWorldModel  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEQ_LEN = 10
K = 5
VULN_PORT = 8080  # matches prevail.ingestion.synthetic.VULN_PORT, the port initial_access targets


def main():
    packets = pd.read_csv(ROOT / "data" / "raw" / "synthetic_packets.csv")
    states = pd.read_parquet(ROOT / "data" / "processed" / "states_w5s.parquet")
    with open(ROOT / "data" / "processed" / "scenario_split.txt") as f:
        test_ids = f.read().splitlines()[1].split(":", 1)[1].split(",")

    bundle = joblib.load(ROOT / "artifacts" / "world_model" / "scaler.joblib")
    feature_columns = bundle["feature_columns"]
    wm_scaler = bundle["scaler"]

    demo_scenario = next(sid for sid in test_ids if "attack" in sid)
    scenario_packets = packets[packets["scenario_id"] == demo_scenario]
    scenario_states = states[states["scenario_id"] == demo_scenario].sort_values("window_id").reset_index(drop=True)

    first_attack_idx = int(scenario_states[scenario_states["attack_stage"] != "benign"].index.min())
    start_t = min(first_attack_idx, max(0, len(scenario_states) - SEQ_LEN))
    target_window_id = start_t + SEQ_LEN - 1  # the "current" state = last history window

    baseline_history = scenario_states.loc[start_t:start_t + SEQ_LEN - 1, feature_columns].to_numpy(dtype=float)

    # Identify the attacker IP for this window from ground truth (in a real
    # deployment this would come from analyst investigation / the
    # explainability evidence, not from the label -- using the label here is
    # a demo convenience for picking WHICH host to isolate, not something the
    # model itself infers).
    win_start = float(scenario_packets["timestamp"].min()) + target_window_id * 5.0
    win_end = win_start + 5.0
    window_pkts = scenario_packets[(scenario_packets["timestamp"] >= win_start) & (scenario_packets["timestamp"] < win_end)]
    attack_pkts = window_pkts[window_pkts["attack_stage"] != "benign"]
    attacker_ip = attack_pkts["src_ip"].mode().iloc[0] if len(attack_pkts) else None

    model = PrevailWorldModel(n_features=len(feature_columns))
    model.load_state_dict(torch.load(ROOT / "artifacts" / "world_model" / "world_model_v1.pt"))
    model.eval()
    stage_scaler, stage_clf = load_stage_model(ROOT / "artifacts" / "attack_stage")

    def rollout_and_score(history):
        out = k_step_rollout_batch(model, wm_scaler, history[None, :, :], K=K)
        return predict_stage_probs(stage_scaler, stage_clf, out["states"][0])

    baseline_probs = rollout_and_score(baseline_history)
    benign_idx = ATTACK_STAGES.index("benign")

    specs = [block_destination_port(VULN_PORT)]
    if attacker_ip:
        specs.append(isolate_host(attacker_ip))

    print(f"Scenario: {demo_scenario}\n")
    print(f"{'Step':<6}{'Stage':<22}{'Baseline P(attack)':<20}")
    for k in range(K):
        base_stage = ATTACK_STAGES[baseline_probs[k].argmax()]
        print(f"T+{k+1:<4}{base_stage:<22}{1.0 - baseline_probs[k, benign_idx]:<20.3f}")

    for spec in specs:
        modified_current = compute_modified_current_state(
            scenario_packets, scenario_states, target_window_id, window_size_s=5.0,
            spec=spec, feature_columns=feature_columns,
        )
        counterfactual_history = build_counterfactual_history(baseline_history, modified_current)
        cf_probs = rollout_and_score(counterfactual_history)
        ood = out_of_distribution_score(modified_current, wm_scaler.mean_, wm_scaler.std_)
        flagged = is_out_of_distribution(modified_current, wm_scaler.mean_, wm_scaler.std_)

        print(f"\n--- Intervention: {spec.name} ---")
        print(f"({spec.description})")
        print(f"Modified-state OOD score: {ood:.3f} {'[FLAGGED: unusual relative to training distribution]' if flagged else '[within normal range]'}")
        print(f"{'Step':<6}{'Counterfactual P(attack)':<26}Delta vs baseline")
        for k in range(K):
            p_base = 1.0 - baseline_probs[k, benign_idx]
            p_cf = 1.0 - cf_probs[k, benign_idx]
            print(f"T+{k+1:<4}{p_cf:<26.3f}{p_cf - p_base:+.3f}")

    print(
        "\nReading: the model FORECASTS a probability change under each simulated "
        "intervention. This is not a causal claim that the intervention would "
        "prevent the attack in reality (see docs/architecture/intervention-model.md)."
    )


if __name__ == "__main__":
    main()
