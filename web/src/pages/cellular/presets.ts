export const CELLULAR_PRESETS: Record<string, number[][]> = {
  // The worked example from the test suite: two near-perfect cells
  "Two clean cells (4×5)": [
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0],
  ],
  // M5 serves parts from two families - exceptional elements are unavoidable
  "Bottleneck machine (5×7)": [
    [1, 0, 0, 1, 0, 0, 1],
    [0, 1, 0, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 1, 1, 0],
    [0, 0, 1, 0, 0, 1, 1],
  ],
  // Three perfect cells hidden by the row order - efficacy 1 after ROC
  "Scrambled blocks (6×8)": [
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 1],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 1],
  ],
};
