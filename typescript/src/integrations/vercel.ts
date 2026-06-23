import { isBlocked } from "../models.js";
import { Kaizen } from "../client.js";

/**
 * Wrap one Vercel AI SDK tool so Kaizen inspects each call. A blocked call
 * returns a refusal string to the model instead of executing the tool.
 */
export function guardTool(kaizen: Kaizen, name: string, tool: any) {
  const orig = tool.execute;
  return {
    ...tool,
    execute: async (args: any, options?: any) => {
      const verdict = kaizen.inspect({ kind: "tool_call", tool: name, metadata: { input: args } });
      if (isBlocked(verdict)) return `Blocked by Kaizen: ${verdict.reason}`;
      return orig ? orig(args, options) : undefined;
    },
  };
}

/**
 * Wrap every tool in a Vercel AI SDK `tools` object:
 *
 *   const result = await generateText({ model, tools: guardTools(kz, tools) });
 */
export function guardTools(kaizen: Kaizen, tools: Record<string, any>): Record<string, any> {
  const out: Record<string, any> = {};
  for (const [name, t] of Object.entries(tools)) out[name] = guardTool(kaizen, name, t);
  return out;
}
