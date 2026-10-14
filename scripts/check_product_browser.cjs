const { chromium } = require("../frontend/node_modules/playwright");
(async () => {
  const browser = await chromium.launch({
    ...(process.env.ORBIT_CHROME_PATH
      ? { executablePath: process.env.ORBIT_CHROME_PATH }
      : {}),
    args: ["--no-sandbox"],
  });
  for (const width of [1440, 390]) {
    const context = await browser.newContext({
      viewport: { width, height: 900 },
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(process.env.ORBIT_FRONTEND + "/login");
    await page.getByLabel("Email Address").fill(process.env.ORBIT_EMAIL);
    await page
      .getByLabel("Password", { exact: true })
      .fill(process.env.ORBIT_PASSWORD);
    await page.getByRole("button", { name: "Sign In", exact: true }).click();
    await page.waitForURL("**/dashboard");
    const input = page.getByLabel("Property search");
    await input.fill("Draft persisted across reload");
    await page.reload();
    await input.waitFor();
    if ((await input.inputValue()) !== "Draft persisted across reload")
      throw Error("Draft did not persist");
    await input.fill("Denver");
    await page.getByRole("button", { name: "Search properties" }).click();
    await page
      .getByText("Found 1 matching properties. Showing 1 results.")
      .waitFor();
    await page
      .getByText("HTTP contract fixture", { exact: true })
      .first()
      .waitFor();
    await input.fill("empty");
    await page.getByRole("button", { name: "Search properties" }).click();
    await page
      .getByText("Found 0 matching properties. Showing 0 results.")
      .waitFor();
    if (await page.getByText("HTTP contract fixture", { exact: true }).count())
      throw Error("Stale property survived empty response");
    await input.fill("outage");
    await page.getByRole("button", { name: "Search properties" }).click();
    await page
      .getByText(/Search unavailable: Search unavailable \(HTTP 503\)/)
      .waitFor();
    await page.getByRole("button", { name: "🗺️ Map", exact: true }).click();
    await page
      .getByText(/Map unavailable. Listing search remains available/)
      .waitFor();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    );
    if (overflow) throw Error("Horizontal overflow " + width);
    if (errors.length) throw Error(errors.join("\n"));
    await page.screenshot({
      path: process.env.ORBIT_EVIDENCE + "/orbit-" + width + ".png",
      fullPage: true,
    });
    await page.getByRole("button", { name: "Sign out" }).click();
    await page.waitForURL("**/login");
    console.log(
      JSON.stringify({
        width,
        auth: "real SQLite/JWT through actual gateway",
        query: "real HTTP contract fixture, not MLS/OpenSearch",
        draftReload: true,
        emptyClearsOld: true,
        outageVisible: true,
        unconfiguredMapVisible: true,
        logout: true,
        pageErrors: errors.length,
        horizontalOverflow: overflow,
      }),
    );
    await context.close();
  }
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
