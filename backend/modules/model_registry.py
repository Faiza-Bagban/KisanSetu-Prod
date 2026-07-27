"""
model_registry.py
Lightweight model versioning — tracks metadata for each trained model
(version, timestamp, training data summary, accuracy) in a JSON registry.
Not a replacement for DVC/MLflow at scale, but sufficient for a small
team tracking a handful of models without extra infrastructure.
"""
import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(BASE_DIR, "saved_models", "registry.json")


def _load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {"models": []}


def _save_registry(registry):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def log_model_version(model_name: str, metrics: dict, notes: str = ""):
    """
    Records a new model version entry. Call this right after training,
    alongside saving the actual .pkl file.
    """
    registry = _load_registry()

    version_num = sum(1 for m in registry["models"] if m["model_name"] == model_name) + 1

    entry = {
        "model_name": model_name,
        "version": version_num,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "notes": notes,
    }

    registry["models"].append(entry)
    _save_registry(registry)
    print(f"Logged {model_name} v{version_num}: {metrics}")
    return entry


def get_latest_version(model_name: str):
    registry = _load_registry()
    versions = [m for m in registry["models"] if m["model_name"] == model_name]
    return versions[-1] if versions else None


def get_all_versions(model_name: str):
    registry = _load_registry()
    return [m for m in registry["models"] if m["model_name"] == model_name]