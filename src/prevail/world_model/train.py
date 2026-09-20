"""Milestone 5 training loop: World Model V1, one-step prediction (Phase 10, 12)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from prevail.world_model.model import PrevailWorldModel


class FeatureScaler:
    """Standardization fit on train only, applied everywhere (no leakage)."""

    def __init__(self):
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "FeatureScaler":
        flat = X.reshape(-1, X.shape[-1])
        self.mean_ = flat.mean(axis=0)
        self.std_ = flat.std(axis=0)
        self.std_[self.std_ < 1e-8] = 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean_) / self.std_

    def inverse_transform_vec(self, y: np.ndarray) -> np.ndarray:
        return y * self.std_ + self.mean_


def make_loader(X: np.ndarray, y: np.ndarray, y_stage: np.ndarray, batch_size: int, shuffle: bool) -> DataLoader:
    ds = TensorDataset(
        torch.tensor(X, dtype=torch.float32),
        torch.tensor(y, dtype=torch.float32),
        torch.tensor(y_stage, dtype=torch.long),
    )
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


def train_world_model(
    X_train: np.ndarray, y_train: np.ndarray, y_stage_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray, y_stage_val: np.ndarray,
    n_features: int,
    seed: int = 42,
    d_model: int = 64,
    n_heads: int = 4,
    n_layers: int = 3,
    dropout: float = 0.1,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    max_epochs: int = 200,
    patience: int = 15,
    batch_size: int = 32,
    stage_loss_weight: float = 0.3,
    device: str = "cpu",
) -> tuple[PrevailWorldModel, FeatureScaler, dict]:
    torch.manual_seed(seed)

    scaler = FeatureScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_val_s = scaler.transform(X_val)
    y_train_s = (y_train - scaler.mean_) / scaler.std_
    y_val_s = (y_val - scaler.mean_) / scaler.std_

    train_loader = make_loader(X_train_s, y_train_s, y_stage_train, batch_size, shuffle=True)
    val_loader = make_loader(X_val_s, y_val_s, y_stage_val, batch_size, shuffle=False)

    model = PrevailWorldModel(
        n_features=n_features, d_model=d_model, n_heads=n_heads, n_layers=n_layers, dropout=dropout,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    state_loss_fn = nn.HuberLoss()
    stage_loss_fn = nn.CrossEntropyLoss()

    best_val = float("inf")
    best_state = None
    epochs_no_improve = 0
    history = {"train_loss": [], "val_loss": []}

    for epoch in range(max_epochs):
        model.train()
        train_losses = []
        for xb, yb, sb in train_loader:
            xb, yb, sb = xb.to(device), yb.to(device), sb.to(device)
            opt.zero_grad()
            out = model(xb)
            loss = state_loss_fn(out["next_state"], yb) + stage_loss_weight * stage_loss_fn(out["stage_logits"], sb)
            loss.backward()
            opt.step()
            train_losses.append(loss.item())

        model.eval()
        val_losses = []
        with torch.no_grad():
            for xb, yb, sb in val_loader:
                xb, yb, sb = xb.to(device), yb.to(device), sb.to(device)
                out = model(xb)
                loss = state_loss_fn(out["next_state"], yb) + stage_loss_weight * stage_loss_fn(out["stage_logits"], sb)
                val_losses.append(loss.item())

        train_loss = float(np.mean(train_losses))
        val_loss = float(np.mean(val_losses)) if val_losses else train_loss
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        if val_loss < best_val - 1e-5:
            best_val = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    history["best_val_loss"] = best_val
    history["epochs_run"] = epoch + 1
    return model, scaler, history
