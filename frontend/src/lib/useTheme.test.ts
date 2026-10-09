import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useTheme } from "./useTheme";

// jsdom has no matchMedia; this fake lets each test pick the OS theme and
// flip it later.
function mockSystemTheme(initial: "light" | "dark") {
  const listeners = new Set<() => void>();
  const query = {
    matches: initial === "dark",
    addEventListener: (_: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_: string, listener: () => void) => listeners.delete(listener),
  };
  vi.stubGlobal("matchMedia", () => query);
  return (next: "light" | "dark") => {
    query.matches = next === "dark";
    listeners.forEach((listener) => listener());
  };
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useTheme", () => {
  it("follows the OS theme until the viewer chooses", () => {
    mockSystemTheme("dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current[0]).toBe("dark");
    // No explicit attribute: the stylesheet's prefers-color-scheme decides.
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  // The old three-state cycle passed through "system", which always looked
  // like one of the other two — one click in three changed nothing.
  it("changes the effective theme on every click", () => {
    mockSystemTheme("dark");
    const { result } = renderHook(() => useTheme());
    const seen = [result.current[0]];
    for (let i = 0; i < 3; i++) {
      act(() => result.current[1]());
      seen.push(result.current[0]);
    }
    expect(seen).toEqual(["dark", "light", "dark", "light"]);
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(localStorage.getItem("vulnscan-theme")).toBe("light");
  });

  it("restores a stored choice over the OS theme", () => {
    mockSystemTheme("dark");
    localStorage.setItem("vulnscan-theme", "light");
    const { result } = renderHook(() => useTheme());
    expect(result.current[0]).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("tracks OS theme changes while no choice is stored", () => {
    const setSystem = mockSystemTheme("light");
    const { result } = renderHook(() => useTheme());
    act(() => setSystem("dark"));
    expect(result.current[0]).toBe("dark");
  });

  it("keeps working when storage is blocked", () => {
    mockSystemTheme("light");
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const { result } = renderHook(() => useTheme());
    act(() => result.current[1]());
    expect(result.current[0]).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });
});
