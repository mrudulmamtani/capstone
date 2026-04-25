import { describe, expect, it } from "vitest";
import { api } from "../lib/api.js";

describe("api client", () => {
  it("has a default axios instance", () => {
    expect(api).toBeDefined();
    expect(typeof api.get).toBe("function");
    expect(typeof api.post).toBe("function");
  });
});
