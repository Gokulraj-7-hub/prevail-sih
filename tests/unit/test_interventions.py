import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd

from prevail.intervention.interventions import block_destination_port, isolate_host


def _sample_packets():
    return pd.DataFrame({
        "src_ip": ["1.1.1.1", "1.1.1.1", "2.2.2.2"],
        "dst_ip": ["10.0.0.1", "10.0.0.2", "10.0.0.1"],
        "dst_port": [8080, 443, 8080],
        "timestamp": [1.0, 2.0, 3.0],
    })


def test_isolate_host_removes_all_matching_traffic():
    df = _sample_packets()
    spec = isolate_host("1.1.1.1")
    out = spec.filter_fn(df)
    assert len(out) == 1
    assert (out["src_ip"] != "1.1.1.1").all() and (out["dst_ip"] != "1.1.1.1").all()


def test_block_destination_port_only_removes_matching_port():
    df = _sample_packets()
    spec = block_destination_port(8080)
    out = spec.filter_fn(df)
    assert len(out) == 1
    assert (out["dst_port"] != 8080).all()


def test_intervention_transformation_preserves_schema():
    df = _sample_packets()
    spec = isolate_host("1.1.1.1")
    out = spec.filter_fn(df)
    assert list(out.columns) == list(df.columns)
