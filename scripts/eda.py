"""EDA script for AIOps Log Monitor.

Reads data/sample.csv and performs extensive exploratory data analysis:
- missing values analysis
- numeric ranges (min/max/mean/std)
- target variable distribution (status, severity)
- categorical value counts
- correlation matrix
- frequent words in message field
- feature importance (RandomForest on failure target)

Outputs PNG charts into docs/eda/ and prints a text summary.
"""

from __future__ import annotations

import os
import re
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
# Dataset principal pedido: processed_events_analysis.csv (fallback a sample.csv)
_PRIMARY = os.path.join(DATA_DIR, "processed_events_analysis.csv")
_FALLBACK = os.path.join(DATA_DIR, "sample.csv")
DATA_PATH = _PRIMARY if os.path.exists(_PRIMARY) else _FALLBACK
OUT_DIR = os.path.join(PROJECT_ROOT, "docs", "eda")
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["axes.grid"] = True


def save_fig(name: str) -> None:
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"saved {path}")


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {df.shape[0]} rows x {df.shape[1]} columns from {DATA_PATH}\n")

    # ---------- 1. missing values ----------
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    print("=== Missing values (columns with nulls) ===")
    print(missing.to_string() if not missing.empty else "None")
    print()

    fig, ax = plt.subplots()
    if not missing.empty:
        missing.plot(kind="barh", ax=ax, color="#4c72b0")
        ax.set_xlabel("Count of missing values")
        ax.set_title("Missing values per column")
    else:
        ax.text(0.5, 0.5, "No missing values", ha="center", va="center")
        ax.set_title("Missing values per column")
    save_fig("missing_values.png")

    # ---------- 2. numeric ranges ----------
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    desc = df[numeric_cols].describe().loc[["min", "max", "mean", "std"]]
    print("\n=== Numeric ranges (min/max/mean/std) ===")
    print(desc.to_string())
    print()

    # histogram grid for key numeric columns
    key_numeric = [c for c in ["duration_ms", "status_code", "hour", "event_count", "line", "process_id"] if c in df.columns]
    if key_numeric:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        axes = axes.ravel()
        for i, col in enumerate(key_numeric[:6]):
            df[col].hist(ax=axes[i], bins=30, color="#55a868", edgecolor="black")
            axes[i].set_title(col)
            axes[i].set_xlabel(col)
            axes[i].set_ylabel("Count")
        for j in range(len(key_numeric), len(axes)):
            axes[j].axis("off")
        fig.suptitle("Distribution of key numeric features")
        save_fig("numeric_distributions.png")

    # ---------- 3. categorical / target ----------
    for col in ["status", "severity", "event_type", "category", "environment"]:
        if col in df.columns:
            counts = df[col].value_counts(dropna=False)
            print(f"\n=== {col} distribution ===")
            print(counts.to_string())
            fig, ax = plt.subplots()
            counts.head(10).plot(kind="bar", ax=ax, color="#8172b3")
            ax.set_title(f"{col} distribution")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
            plt.xticks(rotation=45, ha="right")
            save_fig(f"{col}_distribution.png")

    # ---------- 4. target variable analysis ----------
    if "status" in df.columns:
        failure_rate = (df["status"].astype(str).str.lower() == "failure").mean()
        print(f"\nFailure rate (status=FAILURE): {failure_rate:.4f}")

    # ---------- 5. correlation matrix ----------
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.index)))
        ax.set_xticklabels(corr.columns, rotation=90, fontsize=7)
        ax.set_yticklabels(corr.index, fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_title("Correlation matrix (numeric features)")
        save_fig("correlation_matrix.png")

    # ---------- 6. frequent words in message ----------
    if "message" in df.columns:
        messages = df["message"].dropna().astype(str)
        words: Counter = Counter()
        for msg in messages:
            tokens = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+", msg.lower())
            words.update(tokens)
        top_words = words.most_common(20)
        print("\n=== Top 20 frequent words in message ===")
        for w, c in top_words:
            print(f"{w}: {c}")
        if top_words:
            fig, ax = plt.subplots(figsize=(10, 6))
            ws, cs = zip(*top_words)
            ax.barh(range(len(ws)), cs, color="#c44e52")
            ax.set_yticks(range(len(ws)))
            ax.set_yticklabels(ws)
            ax.invert_yaxis()
            ax.set_xlabel("Count")
            ax.set_title("Top frequent words in log messages")
            save_fig("message_word_frequencies.png")

    # ---------- 7. feature importance (RandomForest on failure target) ----------
    if "status" in df.columns:
        feature_cols = [c for c in [
            "duration_ms", "status_code", "hour", "event_count", "line", "process_id",
            "severity", "event_type", "category", "environment", "method",
        ] if c in df.columns]
        if feature_cols:
            X = df[feature_cols].copy()
            y = (df["status"].astype(str).str.lower() == "failure").astype(int)
            # encode categoricals
            for col in X.columns:
                if X[col].dtype == object:
                    X[col] = X[col].astype("category").cat.codes
            X = X.fillna(0)
            rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            rf.fit(X, y)
            importance = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
            print("\n=== Feature importance (RandomForest, target=FAILURE) ===")
            print(importance.to_string())
            fig, ax = plt.subplots(figsize=(10, 6))
            importance.head(10).plot(kind="barh", ax=ax, color="#64a0c8")
            ax.invert_yaxis()
            ax.set_xlabel("Importance")
            ax.set_title("Top 10 feature importance (predicting failure)")
            save_fig("feature_importance.png")

    print(f"\nEDA complete. Charts written to {OUT_DIR}")


if __name__ == "__main__":
    main()
