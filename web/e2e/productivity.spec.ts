import { expect, test } from "@playwright/test";

// Hand-traced bakery example (tests/test_productivity.py): multifactor
// 5000/3000 = 1.67 -> 6000/3250 = 1.85, change +10.8%; Labor +12.5%.
test("productivity compares two periods on the shared-link example", async ({ page }) => {
  await page.goto(
    "/productivity?o=5000,6000&i=Labor,1500,1600;Materials,1000,1150;Overhead,500,500",
  );
  await expect(page.getByText("+10.8%").first()).toBeVisible();
  await expect(page.getByText("1.67").first()).toBeVisible();
  await expect(page.getByText("1.85").first()).toBeVisible();
  await expect(page.getByText("+12.5%").first()).toBeVisible(); // Labor row
});

test("teaching drawer narrates the multifactor totals", async ({ page }) => {
  await page.goto(
    "/productivity?o=5000,6000&i=Labor,1500,1600;Materials,1000,1150;Overhead,500,500",
  );
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/\$5,000.*\$3,000/)).toBeVisible();
});

test("single-factor calculator divides output by input", async ({ page }) => {
  await page.goto("/productivity?mode=single");
  await expect(page.getByText("2.5", { exact: true })).toBeVisible(); // 500/200
});

// Hand-traced OEE shift (tests/test_oee.py): A 92.9%, P 92.3%, Q 94.4%, OEE 81.0%.
test("oee splits the planned time into the three loss factors", async ({ page }) => {
  await page.goto("/productivity?mode=oee");
  await expect(page.getByText("81.0%").first()).toBeVisible(); // OEE = 17/21
  await expect(page.getByText("92.9%").first()).toBeVisible(); // Availability
  await expect(page.getByText("94.4%").first()).toBeVisible(); // Quality
});
