import { test, expect } from "@playwright/test";

test.describe("AIOps Log Monitor E2E", () => {
  test("health endpoint returns ok", async ({ request }) => {
    const response = await request.get("/health");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.timestamp).toBeTruthy();
  });

  test("predict endpoint returns failure prediction", async ({ request }) => {
    const response = await request.post("/api/v1/predict", {
      data: {
        features: {
          event_type: "LOG",
          severity: "HIGH",
          status: "FAILURE",
          duration_ms: 5.0,
          status_code: 500,
          hour: 14,
        },
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("success");
    expect(body.failure_prediction).toHaveProperty("failure");
    expect(body.severity_prediction).toHaveProperty("severity");
  });

  test("explain endpoint returns SHAP values", async ({ request }) => {
    const response = await request.post("/api/v1/explain", {
      data: {
        features: {
          event_type: "LOG",
          severity: "HIGH",
          status: "FAILURE",
          duration_ms: 5.0,
          status_code: 500,
          hour: 14,
        },
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("success");
    expect(body.explanation).toHaveProperty("shap_values");
    expect(body.explanation).toHaveProperty("decision_path");
  });

  test("metrics endpoint exposes Prometheus format", async ({ request }) => {
    const response = await request.get("/metrics");
    expect(response.status()).toBe(200);
    const text = await response.text();
    expect(text).toContain("aioplog_api_requests_total");
  });

  test("events endpoint returns list", async ({ request }) => {
    const response = await request.get("/api/v1/events?limit=5");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty("events");
    expect(Array.isArray(body.events)).toBe(true);
  });
});
