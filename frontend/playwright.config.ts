import { defineConfig } from "@playwright/test";
import path from "path";

const rootDir = path.resolve(__dirname, "..");
const isWin = process.platform === "win32";
const venvPython = isWin
  ? path.join(rootDir, "venv", "Scripts", "python.exe")
  : path.join(rootDir, "venv", "bin", "python");

/** Use non-default ports to avoid clashing with other services (e.g. Open WebUI on 3000) */
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 3100;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    headless: true,
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  /* Start backend + frontend before running E2E tests */
  webServer: [
    {
      command: `"${venvPython}" main.py`,
      cwd: rootDir,
      url: `http://localhost:${BACKEND_PORT}/api/status`,
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: `npx next dev --port ${FRONTEND_PORT}`,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
