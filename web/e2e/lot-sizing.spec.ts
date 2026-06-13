import { expect, test } from "@playwright/test";

// The hand-traced ground truth: [50,60,90,70,30,100], S=150, h=1 -> $640.
test("lot sizing solves the shared-link example to the hand-traced answer", async ({ page }) => {
  await page.goto("/lot-sizing?d=50,60,90,70,30,100&s=150&h=1");
  await expect(page.getByText("$640").first()).toBeVisible();
  await expect(page.getByText("+41%")).toBeVisible(); // lot-for-lot gap
});

test("teaching drawer narrates the first silver-meal decision", async ({ page }) => {
  await page.goto("/lot-sizing?d=50,60,90,70,30,100&s=150&h=1");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/Lot 1/).first()).toBeVisible();
  await page.getByRole("button", { name: /next/i }).click();
  await expect(page.getByText("$105")).toBeVisible(); // avg after first extension
});

// Backlog (tests/test_dynamic_lot_sizing.py): [10,0,30], S=50, h=1, b=2 -> the
// backlog-aware optimum produces once (qty 40) for $90, beating no-shortage plans.
test("backlog penalty adds a backlog-aware plan that backorders", async ({ page }) => {
  await page.goto("/lot-sizing?d=10,0,30&s=50&h=1&b=2");
  await expect(page.getByText("WW + backlog").first()).toBeVisible();
  await expect(page.getByText("backorders allowed")).toBeVisible();
  await expect(page.getByText("$90").first()).toBeVisible();
});

test("eoq mode shows the closed-form optimum", async ({ page }) => {
  await page.goto("/lot-sizing?mode=eoq");
  await expect(page.getByText("Q* = 200.0")).toBeVisible();
  await expect(page.getByText("$1,200").first()).toBeVisible();
});
