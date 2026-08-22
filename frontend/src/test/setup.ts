import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Vitest runs without `globals: true`, so @testing-library/react never
// registers its automatic afterEach cleanup — every render would stay in
// the document and the next test would match two copies of the component.
afterEach(cleanup);
