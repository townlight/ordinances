const { spawn } = require("node:child_process");
const { mkdir } = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const basePort = Number(process.env.TOWNLIGHT_CODE_BROWSER_QA_PORT || "18022");
const artifactDir = process.env.TOWNLIGHT_CODE_BROWSER_QA_ARTIFACT_DIR || "";
const staffHeaders = {
  "X-Townlight-Code-Role": "staff",
  "X-Townlight-Code-Actor": "browser-qa@example.gov",
};

const phases = [
  {
    name: "empty",
    port: basePort,
    demoSeed: false,
    scenarios: [
      { name: "staff-code-access-mobile", path: "/staff/code", width: 390, height: 900, status: 403 },
      { name: "staff-code-empty-mobile", path: "/staff/code", width: 390, height: 900, status: 200, headers: staffHeaders },
      { name: "staff-sources-access-mobile", path: "/staff/sources", width: 390, height: 900, status: 403 },
      { name: "staff-sources-empty-mobile", path: "/staff/sources", width: 390, height: 900, status: 200, headers: staffHeaders },
      { name: "staff-imports-access-mobile", path: "/staff/imports", width: 390, height: 900, status: 403 },
      { name: "staff-imports-empty-mobile", path: "/staff/imports", width: 390, height: 900, status: 200, headers: staffHeaders },
      { name: "staff-sync-access-mobile", path: "/staff/sync", width: 390, height: 900, status: 403 },
      { name: "staff-sync-empty-mobile", path: "/staff/sync", width: 390, height: 900, status: 200, headers: staffHeaders },
    ],
  },
  {
    name: "populated",
    port: basePort + 1,
    demoSeed: true,
    scenarios: [
      { name: "staff-code-workspace-desktop", path: "/staff/code", width: 1440, height: 1100, status: 200, headers: staffHeaders },
      { name: "staff-code-workspace-mobile", path: "/staff/code", width: 390, height: 900, status: 200, headers: staffHeaders },
      { name: "staff-sources-workspace-desktop", path: "/staff/sources", width: 1440, height: 1100, status: 200, headers: staffHeaders },
      { name: "staff-sources-workspace-mobile", path: "/staff/sources", width: 390, height: 900, status: 200, headers: staffHeaders },
      { name: "staff-imports-populated-desktop", path: "/staff/imports", width: 1440, height: 1100, status: 200, headers: staffHeaders },
      { name: "staff-imports-populated-mobile", path: "/staff/imports", width: 390, height: 1000, status: 200, headers: staffHeaders },
      { name: "staff-sync-populated-desktop", path: "/staff/sync", width: 1440, height: 1100, status: 200, headers: staffHeaders },
      { name: "staff-sync-populated-mobile", path: "/staff/sync", width: 390, height: 1000, status: 200, headers: staffHeaders },
    ],
  },
];

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

async function main() {
  if (artifactDir) {
    await mkdir(artifactDir, { recursive: true });
  }
  const browser = await chromium.launch();
  try {
    const rows = [];
    for (const phase of phases) {
      const baseUrl = `http://127.0.0.1:${phase.port}`;
      const server = startServer(phase);
      try {
        await waitForHealth(baseUrl, server);
        for (const scenario of phase.scenarios) {
          rows.push(await runScenario(browser, baseUrl, phase.name, scenario));
        }
      } finally {
        server.process.kill();
      }
    }
    printRows(rows);
    const failed = rows.filter((row) => !row.passed);
    if (failed.length) {
      throw new Error(`Browser staff QA failed for: ${failed.map((row) => row.scenario).join(", ")}`);
    }
  } finally {
    await browser.close();
  }
}

function startServer(phase) {
  const serverProcess = spawn(
    process.env.PYTHON || "python",
    ["-m", "uvicorn", "townlight_code.main:app", "--host", "127.0.0.1", "--port", String(phase.port)],
    {
      env: { ...process.env, TOWNLIGHT_CODE_DEMO_SEED: phase.demoSeed ? "true" : "false" },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const server = { process: serverProcess, stdout: "", stderr: "" };
  serverProcess.stdout.on("data", (chunk) => {
    server.stdout += chunk.toString();
  });
  serverProcess.stderr.on("data", (chunk) => {
    server.stderr += chunk.toString();
  });
  return server;
}

async function runScenario(browser, baseUrl, phaseName, scenario) {
  const context = await browser.newContext({
    viewport: { width: scenario.width, height: scenario.height },
    extraHTTPHeaders: scenario.headers || {},
  });
  try {
    const page = await context.newPage();
    const consoleErrors = [];
    const pageErrors = [];
    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        consoleErrors.push(message.text());
      }
    });
    page.on("pageerror", (error) => {
      pageErrors.push(error.message);
    });

    const response = await page.goto(`${baseUrl}${scenario.path}`, { waitUntil: "networkidle" });
    const status = response?.status();
    const evidence = await page.evaluate(() => {
      const main = document.querySelectorAll("main#content").length;
      const skip = document.querySelectorAll('a[href="#content"]').length;
      const fixPaths = [...document.querySelectorAll(".fix-path")];
      const fixReadable = fixPaths.every((node) => {
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        const radius = Number.parseFloat(style.borderTopLeftRadius);
        return (
          style.display === "block" &&
          radius <= 8 &&
          rect.width <= document.documentElement.clientWidth &&
          style.overflowWrap !== "normal"
        );
      });
      const horizontalOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
      return { main, skip, fixCount: fixPaths.length, fixReadable, horizontalOverflow };
    });
    await page.keyboard.press("Tab");
    const firstFocus = await page.evaluate(() => document.activeElement?.textContent?.trim() || "");
    if (artifactDir) {
      await page.screenshot({
        path: path.join(artifactDir, `${scenario.name}.png`),
        fullPage: true,
      });
    }

    const unexpectedConsoleErrors =
      scenario.status === 403
        ? consoleErrors.filter((message) => !message.includes("Failed to load resource"))
        : consoleErrors;
    const requiresFixPath = scenario.status !== 200 || scenario.path !== "/staff/sources";
    const passed =
      status === scenario.status &&
      evidence.main === 1 &&
      evidence.skip === 1 &&
      (!requiresFixPath || evidence.fixCount > 0) &&
      evidence.fixReadable &&
      !evidence.horizontalOverflow &&
      firstFocus.includes("Skip") &&
      unexpectedConsoleErrors.length === 0 &&
      pageErrors.length === 0;
    return {
      scenario: scenario.name,
      phase: phaseName,
      status,
      firstFocus,
      ...evidence,
      consoleErrors,
      unexpectedConsoleErrors,
      pageErrors,
      passed,
    };
  } finally {
    await context.close();
  }
}

function printRows(rows) {
  console.table(
    rows.map((row) => ({
      scenario: row.scenario,
      phase: row.phase,
      status: row.status,
      main: row.main,
      skip: row.skip,
      fixReadable: row.fixReadable,
      overflow: row.horizontalOverflow,
      focus: row.firstFocus,
      console: row.unexpectedConsoleErrors.length,
      pageErrors: row.pageErrors.length,
      passed: row.passed,
    })),
  );
}

async function waitForHealth(baseUrl, server) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (await healthOk(baseUrl)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`Timed out waiting for ${baseUrl}/health\nstdout:\n${server.stdout}\nstderr:\n${server.stderr}`);
}

function healthOk(baseUrl) {
  return new Promise((resolve) => {
    const request = http.get(`${baseUrl}/health`, (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });
    request.on("error", () => resolve(false));
    request.setTimeout(1000, () => {
      request.destroy();
      resolve(false);
    });
  });
}
