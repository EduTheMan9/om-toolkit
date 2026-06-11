import { describe, expect, it } from "vitest";
import { formatMoney, formatNumber, percentGap } from "./format";

describe("formatting", () => {
  it("formats money without trailing zeros", () => {
    expect(formatMoney(640)).toBe("$640");
    expect(formatMoney(1234.5)).toBe("$1,234.5");
  });

  it("formats the gap to the best plan", () => {
    expect(percentGap(900, 640)).toBe("+41%");
    expect(percentGap(640, 640)).toBe("+0%");
  });

  it("formats plain numbers without trailing zeros", () => {
    expect(formatNumber(15.4)).toBe("15.4");
    expect(formatNumber(24)).toBe("24");
    expect(formatNumber(1234.5)).toBe("1,234.5");
  });
});
