import { describe, expect, it } from "vitest";

import { formatDuration, stripAnsi } from "./format";

const ESC = String.fromCharCode(27);

describe("formatDuration", () => {
  it("formats seconds as m:ss", () => {
    expect(formatDuration(259)).toBe("4:19");
    expect(formatDuration(8)).toBe("0:08");
  });

  it("returns a dash for nonsense input", () => {
    expect(formatDuration(Number.NaN)).toBe("—");
    expect(formatDuration(-1)).toBe("—");
  });
});

describe("stripAnsi", () => {
  // Real nuclei output: the failure arrives wrapped in SGR escapes, which
  // otherwise render as literal "[1;31m" noise inside the error block.
  it("removes color escapes from raw tool output", () => {
    const raw = `[${ESC}[1;31mFTL${ESC}[0m] Could not run nuclei: no templates provided for scan`;
    expect(stripAnsi(raw)).toBe("[FTL] Could not run nuclei: no templates provided for scan");
  });

  it("also removes escapes whose ESC byte was already lost", () => {
    expect(stripAnsi("[1;31mFTL[0m listo")).toBe("FTL listo");
  });

  it("leaves ordinary text untouched", () => {
    expect(stripAnsi("tool exited with code 1")).toBe("tool exited with code 1");
  });
});
