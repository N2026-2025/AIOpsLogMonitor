import { useEffect, useState } from "react";
import {
  getHealth,
  predictIncident,
  explainIncident,
  getEvents,
  type PredictResponse,
  type ExplainResponse,
} from "./api";

const SAMPLE_FEATURES = {
  event_type: "LOG",
  severity: "HIGH",
  status: "FAILURE",
  duration_ms: 5.0,
  status_code: 500,
  hour: 14,
};

export function App() {
  const [health, setHealth] = useState<string>("unknown");
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getHealth()
      .then((h) => setHealth(h.status))
      .catch(() => setHealth("offline"));
    getEvents()
      .then((e) => setEvents(e.events))
      .catch(() => setEvents([]));
  }, []);

  async function runAnalysis() {
    setLoading(true);
    setError(null);
    try {
      const [p, x] = await Promise.all([
        predictIncident(SAMPLE_FEATURES),
        explainIncident(SAMPLE_FEATURES),
      ]);
      setPrediction(p);
      setExplanation(x);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>AIOps Log Monitor</h1>
        <span className={`badge ${health === "ok" ? "ok" : "bad"}`}>
          API: {health}
        </span>
      </header>

      <main>
        <section className="card">
          <h2>Live incident triage</h2>
          <p className="muted">
            Sample features: HIGH severity, FAILURE status, 500 code, 5ms
            duration.
          </p>
          <button onClick={runAnalysis} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze sample incident"}
          </button>
          {error && <p className="error">{error}</p>}
        </section>

        {prediction && (
          <section className="card">
            <h2>Prediction</h2>
            <div className="kpis">
              <div className="kpi">
                <span className="kpi-label">Failure</span>
                <span className="kpi-value">
                  {prediction.failure_prediction.failure ? "YES" : "NO"}
                </span>
              </div>
              <div className="kpi">
                <span className="kpi-label">Confidence</span>
                <span className="kpi-value">
                  {(prediction.failure_prediction.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="kpi">
                <span className="kpi-label">Severity</span>
                <span className="kpi-value">
                  {prediction.severity_prediction.severity}
                </span>
              </div>
            </div>
          </section>
        )}

        {explanation && (
          <section className="card">
            <h2>Why (explainability)</h2>
            <ol>
              {explanation.explanation.top_contributing.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ol>
            <details>
              <summary>Decision path</summary>
              <code>{explanation.explanation.decision_path}</code>
            </details>
          </section>
        )}

        <section className="card">
          <h2>Recent events</h2>
          {events.length === 0 ? (
            <p className="muted">No events returned.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Environment</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Duration (ms)</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e, i) => (
                  <tr key={i}>
                    <td>{String(e.environment ?? "-")}</td>
                    <td>{String(e.severity ?? "-")}</td>
                    <td>{String(e.status ?? "-")}</td>
                    <td>{String(e.duration_ms ?? "-")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}
