#!/usr/bin/env python
"""Deterministic data seed for AIOps Log Monitor.

Generates a fixed dataset with predictable patterns so CI/CD, demos, and
local development always see the same data. Seeds 200 events across
5 environments (prod, staging, dev, qa, uat) with known failure/injection
patterns for verification.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

np.random.seed(42)

N_EVENTS = 200
ENVIRONMENTS = ["prod", "staging", "dev", "qa", "uat"]
STATUSES = ["SUCCESS", "FAILURE", "UNKNOWN"]
EVENT_TYPES = ["LOG", "METRIC", "TRACE"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
LOGGER_NAMES = ["auth-service", "payment-service", "order-service", "inventory-service", "notification-service"]

start_time = datetime(2026, 11, 13, 0, 0, 0)

rows = []
for i in range(N_EVENTS):
    env = np.random.choice(ENVIRONMENTS, p=[0.4, 0.2, 0.2, 0.1, 0.1])
    status = np.random.choice(STATUSES, p=[0.75, 0.24, 0.01])
    severity = np.random.choice(SEVERITIES, p=[0.6, 0.3, 0.1])
    event_type = np.random.choice(EVENT_TYPES, p=[0.7, 0.2, 0.1])
    duration_ms = float(np.random.exponential(scale=500)) if status == "FAILURE" else float(np.random.exponential(scale=50))
    status_code = np.random.choice([500, 502, 503, 504]) if status == "FAILURE" else np.random.choice([200, 201, 204])
    ts = start_time + timedelta(seconds=int(i * 30))
    hour = ts.hour
    day_of_week = ts.strftime("%A")
    month = ts.month
    week = ts.isocalendar()[1]

    row = {
        "environment": env,
        "project": "aiops-grid",
        "hostname": f"host-{i % 10:02d}.{env}.local",
        "instance_id": f"i-{i:05d}",
        "event_type": event_type,
        "category": "system" if event_type == "LOG" else "metric",
        "severity": severity,
        "status": status,
        "status_code": int(status_code),
        "duration_ms": round(duration_ms, 2),
        "hour": hour,
        "day_of_week": day_of_week,
        "month": month,
        "week": week,
        "line": int(i),
        "process_id": int(1000 + (i % 50)),
        "method": np.random.choice(["GET", "POST", "PUT", "DELETE"]),
        "path": f"/api/v1/{np.random.choice(['events', 'incidents', 'health', 'metrics'])}",
        "logger_name": np.random.choice(LOGGER_NAMES),
        "level": np.random.choice(["INFO", "WARN", "ERROR", "DEBUG"]),
        "risk_score": round(0.5 + (i % 10) * 0.05, 4),
        "is_weekend": 1 if ts.weekday() >= 5 else 0,
        "severity_level": {"LOW": 0, "MEDIUM": 1, "HIGH": 2}[severity],
        "status_failure": 1 if status == "FAILURE" else 0,
        "log_duration": round(float(np.log1p(duration_ms)), 4),
        "status_code_is_error": 1 if status_code >= 400 else 0,
        "schema_version": "1.0",
        "sdk_version": "2.3.1",
        "app_version": "1.0.0",
        "trace_id": f"trace-{i:06d}",
        "message": f"Sample event {i} for {env} environment",
        "source_file": "seed_deterministic.csv",
        "ingested_at": ts.isoformat(),
    }
    rows.append(row)

df = pd.DataFrame(rows)

output_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed_deterministic.csv")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_csv(output_path, index=False)

print(f"Seeded {len(df)} deterministic events to {output_path}")
print(f"Failure rate: {df['status'].eq('FAILURE').mean():.1%}")
print(f"Environments: {sorted(df['environment'].unique().tolist())}")
print(f"Severities: {sorted(df['severity'].unique().tolist())}")
