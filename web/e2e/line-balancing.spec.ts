import { expect, test } from "@playwright/test";

// Hand-traced ground truth: A(5) B(3,A) C(4,A) D(2,B) E(6,C) F(4,DE), CT 10
// -> all three heuristics: 3 stations, efficiency 80%; RPW weights A=24...
test("line balancing solves the shared-link example with all three heuristics", async ({ page }) => {
  await page.goto("/line-balancing?t=A,5,;B,3,A;C,4,A;D,2,B;E,6,C;F,4,D.E&ct=10");
  await expect(page.getByText("3 stations").first()).toBeVisible();
  await expect(page.getByText("80%").first()).toBeVisible();
  await expect(page.getByText("Kilbridge–Wester")).toBeVisible();
});

test("teaching drawer narrates the rpw ranking", async ({ page }) => {
  await page.goto("/line-balancing?t=A,5,;B,3,A;C,4,A;D,2,B;E,6,C;F,4,D.E&ct=10");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/positional weight/i).first()).toBeVisible();
  await expect(page.getByText(/A \(24\)/).first()).toBeVisible();
});
