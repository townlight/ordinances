const { spawn, spawnSync } = require("node:child_process");
const { mkdir } = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const port = Number(process.env.CIVICCODE_PUBLIC_BROWSER_QA_PORT || "18024");
const artifactDir = process.env.CIVICCODE_PUBLIC_BROWSER_QA_ARTIFACT_DIR || "";
const pythonCommand = resolvePythonCommand();
const serverHost = process.env.CIVICCODE_PUBLIC_BROWSER_QA_SERVER_HOST || "127.0.0.1";
const browserHost = process.env.CIVICCODE_PUBLIC_BROWSER_QA_BROWSER_HOST || "127.0.0.1";

const scenarios = [
  { name: "public-home-desktop", path: "/civiccode", width: 1440, height: 1000, status: 200, text: ["Read code with citations", "Ready for a search"] },
  { name: "public-home-mobile", path: "/civiccode", width: 390, height: 900, status: 200, text: ["Read code with citations", "What this does not do"] },
  { name: "public-search-empty-mobile", path: "/civiccode/search", width: 390, height: 900, status: 200, text: ["Search query cannot be empty", "Enter a section number"] },
  { name: "public-search-results-desktop", path: "/civiccode/search?q=roosters", width: 1440, height: 1000, status: 200, text: ["Search results for roosters", "Citation-ready results"] },
  { name: "public-answer-cited-desktop", path: "/civiccode/answer?q=What%20does%20section%2013.40.020%20say%3F&section_number=13.40.020", width: 1440, height: 1000, status: 200, text: ["Cited code answer", "Citation", "not a legal determination"] },
  { name: "public-answer-cited-mobile", path: "/civiccode/answer?q=What%20does%20section%2013.40.020%20say%3F&section_number=13.40.020", width: 390, height: 900, status: 200, text: ["Cited code answer", "Open authoritative section text"] },
  { name: "public-answer-refusal-mobile", path: "/civiccode/search?q=Should%20I%20sue%20my%20neighbor%20over%20roosters%3F", width: 390, height: 900, status: 200, text: ["CivicCode cannot provide legal advice", "contact the City Attorney"] },
  { name: "public-section-detail-desktop", path: "/civiccode/sections/13.40.020", width: 1440, height: 1000, status: 200, text: ["Authoritative code text", "Records-ready export", "Need an official interpretation"] },
  { name: "public-section-detail-mobile", path: "/civiccode/sections/13.40.020", width: 390, height: 900, status: 200, text: ["Authoritative code text", "Citation", "Related materials"] },
  { name: "public-section-export-mobile", path: "/civiccode/sections/13.40.020/export", width: 390, height: 900, status: 200, skipText: "Skip to export content", text: ["CivicCode records-ready export", "Source provenance", "Legal boundary"] },
  {
    name: "react-app-api-search-answer-desktop",
    path: "/civiccode/app",
    width: 1440,
    height: 1000,
    status: 200,
    appActions: true,
    text: ["Read municipal code", "Search", "Answer"],
  },
  {
    name: "react-app-empty-error-mobile",
    path: "/civiccode/app",
    width: 390,
    height: 900,
    status: 200,
    appEmptyState: true,
    text: ["Read municipal code", "Search", "Answer"],
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
  const baseUrl = `http://${browserHost}:${port}`;
  const server = startServer();
  const browser = await chromium.launch();
  try {
    await waitForHealth(baseUrl, server);
    const rows = [];
    for (const scenario of scenarios) {
      rows.push(await runScenario(browser, baseUrl, scenario));
    }
    printRows(rows);
    const failed = rows.filter((row) => !row.passed);
    if (failed.length) {
      throw new Error(`Browser public QA failed for: ${failed.map((row) => row.scenario).join(", ")}`);
    }
  } finally {
    await browser.close();
    server.controller.abort();
  }
}

function startServer() {
  const controller = new AbortController();
  const serverProcess = spawn(
    pythonCommand,
    ["-m", "uvicorn", "civiccode.main:app", "--host", serverHost, "--port", String(port)],
    {
      env: { ...process.env, CIVICCODE_DEMO_SEED: "true" },
      signal: controller.signal,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  serverProcess.on("error", (error) => {
    if (error.name !== "AbortError") {
      throw error;
    }
  });
  const server = { controller, stdout: "", stderr: "" };
  serverProcess.stdout.on("data", (chunk) => {
    server.stdout += chunk.toString();
  });
  serverProcess.stderr.on("data", (chunk) => {
    server.stderr += chunk.toString();
  });
  return server;
}

function resolvePythonCommand() {
  if (process.env.PYTHON) {
    return process.env.PYTHON;
  }
  for (const candidate of ["python3", "python"]) {
    const result = spawnSync(candidate, ["--version"], { stdio: "ignore" });
    if (result.status === 0) {
      return candidate;
    }
  }
  throw new Error("Python launcher not found. Set PYTHON, or install python3/python on PATH.");
}

async function runScenario(browser, baseUrl, scenario) {
  const context = await browser.newContext({
    viewport: { width: scenario.width, height: scenario.height },
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
    const apiResponses = [];
    page.on("response", (response) => {
      const url = response.url();
      if (url.includes("/api/v1/civiccode/search") || url.includes("/api/v1/civiccode/questions/answer")) {
        apiResponses.push({ url, status: response.status() });
      }
    });
    const response = await page.goto(`${baseUrl}${scenario.path}`, { waitUntil: "networkidle" });
    if (scenario.appActions) {
      await Promise.all([
        page.waitForResponse((item) => item.url().includes("/api/v1/civiccode/search")),
        page.getByRole("button", { name: "Search" }).first().click(),
      ]);
      await Promise.all([
        page.waitForResponse((item) => item.url().includes("/api/v1/civiccode/questions/answer")),
        page.getByRole("button", { name: "Answer" }).first().click(),
      ]);
      await page.getByText("Up to four chickens, ducks, pigeons").waitFor();
    }
    if (scenario.appEmptyState) {
      await page.getByLabel("Question or section").fill("   ");
      await page.getByRole("button", { name: "Search" }).first().click();
      await page.getByText("Enter a section number or plain-language term before searching.").waitFor();
    }
    const status = response?.status();
    const evidence = await page.evaluate((expectedText) => {
      const bodyText = document.body.textContent || "";
      const main = document.querySelectorAll("main#content").length;
      const skip = document.querySelectorAll('a[href="#content"]').length;
      const horizontalOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
      const textPresent = expectedText.every((text) => bodyText.includes(text));
      return { main, skip, horizontalOverflow, textPresent };
    }, scenario.text);
    await page.keyboard.press("Tab");
    const firstFocus = await page.evaluate(() => document.activeElement?.textContent?.trim() || "");
    if (artifactDir) {
      await page.screenshot({ path: path.join(artifactDir, `${scenario.name}.png`), fullPage: true });
    }
    const skipText = scenario.skipText || "Skip to content";
    const passed =
      status === scenario.status &&
      evidence.main === 1 &&
      evidence.skip === 1 &&
      evidence.textPresent &&
      !evidence.horizontalOverflow &&
      (scenario.appActions || scenario.appEmptyState || firstFocus.includes(skipText)) &&
      (!scenario.appActions || apiResponses.length >= 2) &&
      consoleErrors.length === 0 &&
      pageErrors.length === 0;
    return { scenario: scenario.name, status, firstFocus, apiResponses, ...evidence, consoleErrors, pageErrors, passed };
  } finally {
    await context.close();
  }
}

function printRows(rows) {
  console.table(
    rows.map((row) => ({
      scenario: row.scenario,
      status: row.status,
      main: row.main,
      skip: row.skip,
      text: row.textPresent,
      overflow: row.horizontalOverflow,
      focus: row.firstFocus,
      api: row.apiResponses?.length || 0,
      console: row.consoleErrors.length,
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
