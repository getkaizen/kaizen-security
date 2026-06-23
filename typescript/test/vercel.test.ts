import { describe, it, expect } from "vitest";
import { Kaizen } from "../src/index";
import { guardTools } from "../src/integrations/vercel";

describe("vercel ai sdk adapter", () => {
  it("blocks a bad tool and runs a clean one", async () => {
    const kz = new Kaizen({ policies: [{ mode: "blocklist", rules: { skill_patterns: ["delete_all"] } }] });
    const tools = {
      delete_all: { description: "delete", execute: async () => "DELETED" },
      read_file: { description: "read", execute: async () => "CONTENTS" },
    };
    const guarded = guardTools(kz, tools);
    expect(await guarded.delete_all.execute({})).toMatch(/Blocked by Kaizen/);
    expect(await guarded.read_file.execute({})).toBe("CONTENTS");
  });
});
