"""World Model V1: small temporal Transformer encoder, one-step next-state
prediction (master prompt Phase 10).

Historical states -> feature projection -> positional encoding -> Transformer
encoder -> next-state prediction head. Output is a *state* (feature vector),
never a label -- that is what structurally distinguishes this from a
classifier (see architecture.md Sec 1.4).

Mixed-feature-output note (D-007, DECISIONS.md): Phase 11 asks for separate
per-type loss heads when a state mixes continuous/binary/categorical fields.
PREVAIL's v1 feature registry (data-contract.md Sec 3) is homogeneously
continuous/ratio-valued -- no one-hot categorical or true binary fields are
in the feature vector itself -- so a single regression head with Huber loss
(robust to the heavy-tailed count features like bytes_sum) is used here. This
is revisited if/when a future feature version adds categorical fields.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class PrevailWorldModel(nn.Module):
    """Small Transformer encoder World Model (master prompt Sec 13 starting hparams)."""

    def __init__(
        self,
        n_features: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
        n_stages: int = 5,
    ):
        super().__init__()
        self.n_features = n_features
        self.input_proj = nn.Linear(n_features, d_model)
        self.pos_encoding = PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=dim_feedforward,
            dropout=dropout, batch_first=True, activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(d_model)
        # Next-state prediction head (regression over all features).
        self.state_head = nn.Linear(d_model, n_features)
        # Auxiliary stage head, trained jointly for a richer representation but
        # NOT the module boundary used for attack-stage interpretation -- that
        # lives in prevail.attack_stage and operates on emitted *states*, so it
        # can be applied uniformly to real states and to World-Model rollouts.
        self.aux_stage_head = nn.Linear(d_model, n_stages)

    def _causal_mask(self, seq_len: int, device) -> torch.Tensor:
        return torch.triu(torch.full((seq_len, seq_len), float("-inf"), device=device), diagonal=1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        """x: (batch, seq_len, n_features) -> predicted next-state features
        (batch, n_features) taken from the representation at the last
        timestep, using a causal mask so no position attends to the future."""
        h = self.input_proj(x)
        h = self.pos_encoding(h)
        mask = self._causal_mask(x.size(1), x.device)
        h = self.encoder(h, mask=mask)
        h = self.norm(h)
        last = h[:, -1, :]
        return {
            "next_state": self.state_head(last),
            "stage_logits": self.aux_stage_head(last),
        }
