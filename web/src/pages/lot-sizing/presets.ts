import type { DynamicInputs } from "../../lib/urlState";

export const DYNAMIC_PRESETS: Record<string, DynamicInputs> = {
  "Six-period demo": { demands: [50, 60, 90, 70, 30, 100], setupCost: 150, holdingCost: 1 },
  "Lumpy demand": { demands: [10, 80, 0, 120, 5, 0, 90, 40], setupCost: 200, holdingCost: 2 },
  "Cheap setups": { demands: [40, 50, 35, 60, 45, 55], setupCost: 30, holdingCost: 3 },
};
