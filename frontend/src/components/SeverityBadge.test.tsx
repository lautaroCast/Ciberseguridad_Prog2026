import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SeverityBadge } from "./SeverityBadge";

describe("SeverityBadge", () => {
  it("renders the severity label uppercased with the matching class", () => {
    render(<SeverityBadge severity="high" />);
    const badge = screen.getByText("HIGH");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("badge--severity-high");
  });
});
