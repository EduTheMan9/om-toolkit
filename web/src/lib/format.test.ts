import { describe, expect, it } from "vitest";
import { formatMoney, percentGap } from "./format";

describe("formatting", () => {
  it("formats money without trailing zeros", () => {
    expect(formatMoney(640)).toBe("$640");
    expect(formatMoney(1234.5)).toBe("$1,234.5");
  });

  it("formats the gap to the best plan", () => {
    expect(percentGap(900, 640)).toBe("+41%");
    expect(percentGap(640, 640)).toBe("+0%");
  });
});
