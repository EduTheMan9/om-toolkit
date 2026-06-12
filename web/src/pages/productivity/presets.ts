import type { ProductivityInputs } from "../../lib/urlState";

export const PRODUCTIVITY_PRESETS: Record<string, ProductivityInputs> = {
  // Last period is the worked example from the test suite (multifactor 5/3)
  "Bakery, two weeks": {
    outputPrevious: 5000,
    outputCurrent: 6000,
    inputs: [
      { name: "Labor", previous: 1500, current: 1600 },
      { name: "Materials", previous: 1000, current: 1150 },
      { name: "Overhead", previous: 500, current: 500 },
    ],
  },
  // Labor productivity explodes but MULTIFACTOR falls - the robot costs
  // more than the labor it saved
  "Automation trade-off": {
    outputPrevious: 8000,
    outputCurrent: 8200,
    inputs: [
      { name: "Labor", previous: 2000, current: 800 },
      { name: "Machines", previous: 500, current: 2200 },
      { name: "Materials", previous: 2000, current: 2050 },
    ],
  },
};
