/* Run against an isolated test instance, never a workspace containing real CVs. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { default: AxeBuilder } = require("@axe-core/playwright");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_PATH
      ? { executablePath: process.env.CHROME_PATH }
      : {}),
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1080 },
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors = [];
  const badResponses = [];
  const accessibility = [];
  async function scan(name) {
    const report = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    accessibility.push({
      name,
      violations: report.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
        })),
      })),
    });
    fs.writeFileSync(
      "artifacts/accessibility-audit.json",
      JSON.stringify(accessibility, null, 2),
    );
    const unbound = await page
      .locator("button")
      .evaluateAll((buttons) =>
        buttons
          .filter(
            (b) =>
              b.checkVisibility() &&
              !b.disabled &&
              !(b.type === "submit" && b.form) &&
              typeof b.onclick !== "function",
          )
          .map((b) => ({ id: b.id, text: b.textContent })),
      );
    assert.deepEqual(
      unbound,
      [],
      "Every visible action must have a runtime handler",
    );
  }
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("response", (r) => {
    if (r.status() >= 500) badResponses.push(r.url());
  });
  const base = process.env.TEST_URL || "http://127.0.0.1:8001";
  fs.mkdirSync("artifacts", { recursive: true });
  await page.goto(base);
  await page.locator('#content[aria-busy="false"]').waitFor();
  if (await page.getByRole("button", { name: "Jelajahi data contoh" }).count())
    await page.getByRole("button", { name: "Jelajahi data contoh" }).click();
  else
    await page
      .getByLabel("Pilih lowongan")
      .selectOption({ label: "Senior Frontend Engineer" });
  await page
    .getByRole("button", { name: "Nadia Putri", exact: true })
    .waitFor();
  if (await page.getByRole("button", { name: "Analisis ulang" }).count()) {
    await page.getByRole("button", { name: "Analisis ulang" }).click();
    await page
      .getByRole("button", { name: "Analisis ulang" })
      .waitFor({ state: "hidden" });
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "artifacts/workspace-desktop.png",
    fullPage: true,
  });
  assert.equal(await page.locator("tbody tr").count(), 6);
  await scan("candidate list / desktop");
  await page.getByRole("button", { name: "Nadia Putri", exact: true }).click();
  await page.getByRole("dialog").waitFor();
  await scan("candidate profile dialog");
  await page.getByRole("button", { name: "Shortlist", exact: true }).click();
  await page
    .getByLabel("Catatan tinjauan")
    .fill("Keahlian sesuai. Lanjut ke wawancara teknis.");
  await page.getByRole("button", { name: "Simpan tinjauan" }).click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page.getByRole("button", { name: /Shortlist.*1/ }).waitFor();
  await page.getByLabel("Cari nama atau keahlian").fill("TidakAdaNamaIni");
  await page
    .getByRole("heading", { name: "Tidak ada kandidat yang cocok" })
    .waitFor();
  await page.getByRole("button", { name: "Hapus pencarian" }).click();
  await page
    .getByRole("button", { name: "Nadia Putri", exact: true })
    .waitFor();
  await page.getByRole("button", { name: "Nadia Putri", exact: true }).click();
  await page.getByRole("button", { name: "Verifikasi / edit profil" }).click();
  await page.getByLabel("Total pengalaman (bulan)").fill("54");
  await page.getByRole("button", { name: "Simpan profil" }).click();
  await page
    .getByText("Kandidat atau kriteria telah berubah.", { exact: false })
    .waitFor();
  await page.getByRole("button", { name: "Analisis ulang" }).click();
  await page
    .getByText("Kandidat atau kriteria telah berubah.", { exact: false })
    .waitFor({ state: "hidden" });
  await page.getByRole("button", { name: "Sesuaikan kriteria" }).click();
  await page
    .getByRole("heading", { name: "Prioritas yang mencerminkan kebutuhan." })
    .waitFor();
  await scan("criteria form");
  // Simulate session expiry and re-authentication without real credentials.
  await page.locator("#weight-education").press("ArrowRight");
  await page.locator("#weight-skills").press("ArrowLeft");
  const draftWeight = await page.locator("#weight-education").inputValue();
  const jobId = await page.locator("#job-select").inputValue();
  await page.route(
    `${base}/api/jobs/${jobId}`,
    (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Sesi berakhir." }),
      }),
    { times: 1 },
  );
  await page.getByRole("button", { name: "Simpan kriteria" }).click();
  await page
    .getByRole("heading", { name: "Selamat datang kembali." })
    .waitFor();
  await page.route(
    "**/api/login",
    (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: '{"ok":true}',
      }),
    { times: 1 },
  );
  await page
    .getByLabel("Kata sandi ruang kerja")
    .fill("test-only-mocked-login");
  await page.getByRole("button", { name: "Masuk ke ruang kerja" }).click();
  await page
    .getByRole("heading", { name: "Prioritas yang mencerminkan kebutuhan." })
    .waitFor();
  assert.equal(
    await page.locator("#weight-education").inputValue(),
    draftWeight,
  );
  await page.getByRole("button", { name: "Simpan kriteria" }).click();
  await page.getByRole("link", { name: "Lowongan", exact: true }).click();
  await page
    .getByRole("button", { name: "Buat lowongan", exact: true })
    .click();
  await page.getByLabel("Nama posisi").fill("Data Engineer");
  await page.getByLabel("Keahlian yang dibutuhkan").fill("Python, SQL");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Buat lowongan", exact: true })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page.getByRole("link", { name: /Kandidat/ }).click();
  await page
    .getByRole("button", { name: "Tambah kandidat", exact: true })
    .first()
    .click();
  await page.getByRole("button", { name: "Tambah profil manual" }).click();
  await page.getByLabel("Nama kandidat").fill("Test Engineer");
  await page.getByLabel("Keahlian", { exact: true }).fill("Python, SQL");
  await page.getByLabel("Total pengalaman (bulan)").fill("36");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Tambah kandidat", exact: true })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page
    .getByRole("button", { name: "Test Engineer", exact: true })
    .waitFor();
  // Empty filter, narrow layout, keyboard dialog exit, and focus restoration.
  await page
    .getByLabel("Pilih lowongan")
    .selectOption({ label: "Senior Frontend Engineer" });
  await page
    .getByRole("button", { name: "Nadia Putri", exact: true })
    .waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  await scan("candidate list / mobile");
  await page.screenshot({
    path: "artifacts/workspace-mobile.png",
    fullPage: true,
  });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    true,
  );
  await page.getByRole("button", { name: "Nadia Putri", exact: true }).click();
  await page.keyboard.press("Escape");
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  assert.equal(
    await page.evaluate(() => document.activeElement.textContent),
    "Nadia Putri",
  );
  await page.getByRole("link", { name: "Aktivitas", exact: true }).click();
  await page
    .getByRole("heading", { name: "Setiap langkah punya catatan." })
    .waitFor();
  // Network failure is visible and can be retried.
  await page.route("**/api/audit", (r) => r.abort());
  await page.getByRole("link", { name: "Aktivitas", exact: true }).click();
  await page
    .getByRole("heading", { name: "Ruang kerja belum dapat dimuat" })
    .waitFor();
  await page.unroute("**/api/audit");
  await page.getByRole("button", { name: "Coba kembali" }).click();
  await page
    .getByRole("heading", { name: "Setiap langkah punya catatan." })
    .waitFor();
  assert.deepEqual(errors, []);
  assert.deepEqual(badResponses, []);
  assert.deepEqual(
    accessibility.flatMap((r) => r.violations),
    [],
  );
  fs.writeFileSync(
    "artifacts/browser-report.json",
    JSON.stringify(
      {
        passed: true,
        consoleErrors: errors,
        serverErrors: badResponses,
        viewports: ["1440x1080", "390x844"],
        checks: [
          "demo opt-in",
          "candidate review",
          "search and clear",
          "profile correction",
          "stale rerun",
          "criteria save",
          "job creation",
          "manual candidate",
          "keyboard Escape/focus restore",
          "mobile overflow",
          "network failure/retry",
          "reduced motion",
          "session expiry and in-memory draft recovery",
        ],
      },
      null,
      2,
    ),
  );
  await browser.close();
  console.log("Browser workflow passed. Screenshots saved in artifacts/.");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
