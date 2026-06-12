import { expect, test } from "@playwright/test";

// Hand-traced ground truth: A 10minx2 (12/h), B 6min (10/h, bottleneck),
// C 4min (15/h); demand 9/h -> demand-constrained, flow rate 9/h.
test("process analysis finds the bottleneck on the shared-link example", async ({ page }) => {
  await page.goto("/process-analysis?r=A,10,2;B,6,1;C,4,1&d=9");
  await expect(page.getByText("capacity 10 /h")).toBeVisible();
  await expect(page.getByText("flow rate 9 /h")).toBeVisible();
  await expect(page.getByText("demand-constrained").first()).toBeVisible();
  await expect(page.getByText("20 min")).toBeVisible(); // unloaded flow time
});

test("teaching drawer narrates the capacity computation", async ({ page }) => {
  await page.goto("/process-analysis?r=A,10,2;B,6,1;C,4,1&d=9");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  // first step: A's capacity = 2 servers / 10 min = 12 units/hour
  await expect(page.getByText(/12 units\/hour/)).toBeVisible();
});

test("littles law mode solves the missing variable", async ({ page }) => {
  await page.goto("/process-analysis?mode=littles");
  await expect(page.getByText("Flow time T = 5")).toBeVisible(); // I=20, R=4
});
