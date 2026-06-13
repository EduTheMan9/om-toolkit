import { expect, test } from "@playwright/test";

// Hand-traced ground truth: jobs A(6,8) B(2,6) C(8,18) D(3,15) E(9,23);
// flow shop J1(3,6) J2(5,2) J3(1,2) J4(6,6) J5(7,5) -> makespan 24 (input order: 27).
test("dispatching compares every rule on the shared-link example", async ({ page }) => {
  await page.goto("/scheduling?j=A,6,8;B,2,6;C,8,18;D,3,15;E,9,23");
  await expect(page.getByText("B → D → A → C → E")).toBeVisible(); // SPT hero (default)
  await expect(page.getByText("15.4").first()).toBeVisible(); // FCFS avg completion
  await expect(page.getByText("Moore–Hodgson").first()).toBeVisible();
});

// Weighted jobs (w=4,1 etc): WSPT pulls the important long job C forward to
// B → C → D → E → A (hand-traced in tests/test_dispatching.py).
test("wspt reorders jobs by weighted processing time", async ({ page }) => {
  await page.goto("/scheduling?j=A,6,8;B,2,6;C,8,18;D,3,15;E,9,23&w=1,2,4,1,3");
  // select the WSPT row (its note is unique) so the hero shows its sequence
  await page.getByText("shortest weighted").click();
  await expect(page.getByText("B → C → D → E → A").first()).toBeVisible();
});

test("johnson mode shows the optimal sequence and narrates the first pick", async ({ page }) => {
  await page.goto("/scheduling?mode=johnson&j=J1,3,6;J2,5,2;J3,1,2;J4,6,6;J5,7,5");
  await expect(page.getByText("J3 → J1 → J4 → J5 → J2").first()).toBeVisible();
  await expect(page.getByText("makespan 24")).toBeVisible();
  await expect(page.getByText("27", { exact: true })).toBeVisible(); // input-order baseline
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/smallest processing time left/i)).toBeVisible();
});
