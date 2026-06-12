import { expect, test } from "@playwright/test";

// Hand-traced ground truth (tests/test_cells.py): ROC orders M1,M3,M2,M4 /
// P1,P4,P2,P3,P5; 2 cells; e = 9, 0 exceptional, 1 void -> efficacy 0.9.
test("cellular finds two cells on the shared-link example", async ({ page }) => {
  await page.goto("/cellular?m=10010;01101;10010;01100");
  await expect(page.getByText("2 cells")).toBeVisible();
  await expect(page.getByText("grouping efficacy 0.9")).toBeVisible();
});

test("cell composition matches the hand trace", async ({ page }) => {
  await page.goto("/cellular?m=10010;01101;10010;01100");
  await expect(page.getByText("M1, M3")).toBeVisible(); // Cell 1 machines
  await expect(page.getByText("parts: P2, P3, P5")).toBeVisible(); // Cell 2
});

test("teaching drawer narrates the binary-value sort", async ({ page }) => {
  await page.goto("/cellular?m=10010;01101;10010;01100");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  // pass 1: M1 = 18, M3 = 18, M2 = 13, M4 = 12
  await expect(page.getByText(/M1 = 18, M3 = 18/)).toBeVisible();
});
