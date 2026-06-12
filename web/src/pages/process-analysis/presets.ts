import type { ProcessInputs } from "../../lib/urlState";

export const PROCESS_PRESETS: Record<string, ProcessInputs> = {
  "Sandwich line": {
    resources: [
      { name: "Take order", timeMin: 1.5, servers: 1 },
      { name: "Make sandwich", timeMin: 3, servers: 2 },
      { name: "Toast", timeMin: 2, servers: 1 },
      { name: "Checkout", timeMin: 1, servers: 1 },
    ],
    demandPerHour: 35,
  },
  "Health clinic (overloaded)": {
    resources: [
      { name: "Reception", timeMin: 5, servers: 1 },
      { name: "Nurse triage", timeMin: 15, servers: 2 },
      { name: "Doctor consult", timeMin: 20, servers: 3 },
    ],
    demandPerHour: 10,
  },
  "Three-step demo": {
    resources: [
      { name: "A", timeMin: 10, servers: 2 },
      { name: "B", timeMin: 6, servers: 1 },
      { name: "C", timeMin: 4, servers: 1 },
    ],
    demandPerHour: 9,
  },
};
