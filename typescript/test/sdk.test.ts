import { describe, it, expect } from "vitest";
import { Kaizen, KaizenBlocked } from "../src/index";

const bl = (rules: Record<string, any>) => new Kaizen({ policies: [{ mode: "blocklist", rules }] });

describe("kaizen engine", () => {
  it("blocks a blocklisted publisher (case and space insensitive)", () => {
    expect(bl({ publishers: ["evilcorp"] }).inspect({ publisher: " EvilCorp " }).decision).toBe("block");
  });

  it("blocks an ip inside a CIDR, scheme and port ignored", () => {
    expect(bl({ ip: ["45.9.148.0/24"] }).inspect({ kind: "connect", target: "http://45.9.148.108:8080/x" }).decision).toBe("block");
  });

  it("blocks a domain and its subdomains", () => {
    expect(bl({ domains: ["evil.com"] }).inspect({ target: "https://api.evil.com/path" }).decision).toBe("block");
  });

  it("uses fullmatch semantics for skill patterns", () => {
    expect(bl({ skill_patterns: ["delete_.*"] }).inspect({ tool: "delete_all" }).decision).toBe("block");
    expect(bl({ skill_patterns: ["delete"] }).inspect({ tool: "delete_all" }).decision).toBe("allow");
  });

  it("allows a clean action", () => {
    expect(bl({ publishers: ["evilcorp"] }).inspect({ tool: "read", publisher: "internal" }).decision).toBe("allow");
  });

  it("allowlist uses AND across constrained dimensions", () => {
    const kz = new Kaizen({ policies: [{ mode: "allowlist", rules: { tools: ["read"], publishers: ["internal"] } }] });
    expect(kz.inspect({ tool: "read", publisher: "external" }).decision).toBe("block");
    expect(kz.inspect({ tool: "read", publisher: "internal" }).decision).toBe("allow");
  });

  it("enforce throws KaizenBlocked", () => {
    expect(() => bl({ skill_patterns: ["delete_all"] }).enforce({ tool: "delete_all" })).toThrow(KaizenBlocked);
  });

  it("fires the onVerdict hook", () => {
    const seen: string[] = [];
    const kz = new Kaizen({ policies: [{ mode: "blocklist", rules: { skill_patterns: ["delete_all"] } }], onVerdict: (v) => seen.push(v.decision) });
    kz.inspect({ tool: "delete_all" });
    expect(seen).toContain("block");
  });
});
