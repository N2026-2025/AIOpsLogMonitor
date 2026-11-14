export interface HealthResponse {
  status: string;
  timestamp: string;
}

export interface PredictResponse {
  status: string;
  features: Record<string, unknown>;
  failure_prediction: {
    failure: boolean;
    confidence: number;
    features: Record<string, unknown>;
  };
  severity_prediction: {
    severity: string;
    success: boolean;
  };
  model_version: string;
}

export interface ExplainResponse {
  status: string;
  explanation: {
    features: Record<string, unknown>;
    shap_values: number[];
    top_contributing: string[];
    decision_path: string;
    model_version: string;
    feature_importance: Record<string, number>;
  };
  features: Record<string, unknown>;
}

export interface EventResponse {
  status: string;
  count: number;
  events: Record<string, unknown>[];
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch("/api/v1/health");
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function predictIncident(
  features: Record<string, unknown>
): Promise<PredictResponse> {
  const res = await fetch("/api/v1/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ features }),
  });
  if (!res.ok) throw new Error(`Predict failed: ${res.status}`);
  return res.json();
}

export async function explainIncident(
  features: Record<string, unknown>
): Promise<ExplainResponse> {
  const res = await fetch("/api/v1/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ features }),
  });
  if (!res.ok) throw new Error(`Explain failed: ${res.status}`);
  return res.json();
}

export async function getEvents(): Promise<EventResponse> {
  const res = await fetch("/api/v1/events?limit=10");
  if (!res.ok) throw new Error(`Events fetch failed: ${res.status}`);
  return res.json();
}

export async function getMetrics(): Promise<string> {
  const res = await fetch("/metrics");
  if (!res.ok) throw new Error(`Metrics fetch failed: ${res.status}`);
  return res.text();
}
