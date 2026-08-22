import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SeverityBadge } from "./SeverityBadge";

describe("SeverityBadge", () => {
  it("renders the Spanish severity name", () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText("Alta")).toBeInTheDocument();
  });

  // Severity must never be carried by color alone: the rank meter is the
  // redundant encoding that survives grayscale and color vision deficiency.
  it("fills one meter step per rank level", () => {
    const { container } = render(<SeverityBadge severity="medium" />);
    expect(container.querySelectorAll(".meter__step")).toHaveLength(5);
    expect(container.querySelectorAll(".meter__step--on")).toHaveLength(3);
  });

  it("gives critical a strictly higher rank than high", () => {
    const critical = render(<SeverityBadge severity="critical" />).container;
    const high = render(<SeverityBadge severity="high" />).container;
    expect(critical.querySelectorAll(".meter__step--on").length).toBeGreaterThan(
      high.querySelectorAll(".meter__step--on").length,
    );
  });
});
