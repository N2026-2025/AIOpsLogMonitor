{
  "webServer": {
    "command": "python -m src.api.main",
    "url": "http://localhost:8000",
    "timeout": 30000,
    "reuseExistingServer": !process.env.CI
  },
  "use": {
    "baseURL": "http://localhost:8000",
    "headless": true,
    "viewport": { "width": 1280, "height": 720 },
    "ignoreHTTPSErrors": true,
    "video": "on-first-retry",
    "trace": "on-first-retry"
  },
  "projects": [
    {
      "name": "chromium",
      "use": { "browserName": "chromium" }
    }
  ],
  "testDir": "e2e",
  "retries": 2,
  "workers": 1
}
