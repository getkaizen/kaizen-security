import { Action, Policy, Verdict, allow, block } from "./models.js";

const MAX_PATTERN = 200;
const MAX_TOOL = 512;

function norm(s?: string): string {
  const nfkc = (s ?? "").normalize("NFKC");
  const stripped = Array.from(nfkc)
    .filter((c) => {
      const code = c.codePointAt(0) ?? 0;
      return !((code >= 0x200b && code <= 0x200f) || code === 0xfeff);
    })
    .join("");
  return stripped.trim().toLowerCase();
}

function hostOf(target?: string): string {
  if (!target) return "";
  let t = target.trim();
  const m = t.match(/^[a-z][a-z0-9+.-]*:\/\/([^/]+)/i);
  if (m) t = m[1];
  t = t.split("/")[0];
  if (t.includes("]")) {
    t = t.slice(0, t.indexOf("]")).replace(/[[\]]/g, "");
  } else if (t.includes(":")) {
    t = t.split(":")[0];
  }
  return t.toLowerCase();
}

function ipv4ToInt(ip: string): number | null {
  const parts = ip.split(".");
  if (parts.length !== 4) return null;
  let n = 0;
  for (const p of parts) {
    const x = Number(p);
    if (!Number.isInteger(x) || x < 0 || x > 255) return null;
    n = (n << 8) | x;
  }
  return n >>> 0;
}

function ipInCidr(ip: string, cidr: string): boolean {
  if (!cidr.includes("/")) return norm(ip) === norm(cidr);
  const [net, bitsStr] = cidr.split("/");
  const bits = Number(bitsStr);
  const ipN = ipv4ToInt(ip);
  const netN = ipv4ToInt(net);
  if (ipN === null || netN === null || !Number.isInteger(bits) || bits < 0 || bits > 32) return false;
  if (bits === 0) return true;
  const mask = (~0 << (32 - bits)) >>> 0;
  return (ipN & mask) === (netN & mask);
}

function domainHit(host: string, domain: string): boolean {
  const h = norm(host).replace(/\.$/, "");
  const d = norm(domain).replace(/\.$/, "").replace(/^\*\./, "");
  if (!h || !d) return false;
  return h === d || h.endsWith("." + d);
}

function blocklist(action: Action, rules: Record<string, any>): Verdict {
  const publishers: string[] = (rules.publishers ?? []).map(norm);
  if (action.publisher && publishers.includes(norm(action.publisher))) {
    return block(`blocked publisher: ${action.publisher}`, [{ kind: "publisher", value: action.publisher, source: "blocklist" }]);
  }
  const host = hostOf(action.target);
  for (const ip of rules.ip ?? []) {
    if (host && ipInCidr(host, String(ip))) {
      return block(`blocked address: ${host}`, [{ kind: "ip", value: host, source: "blocklist" }]);
    }
  }
  for (const dom of rules.domains ?? []) {
    if (domainHit(host, String(dom))) {
      return block(`blocked domain: ${host}`, [{ kind: "domain", value: host, source: "blocklist" }]);
    }
  }
  if (action.hash) {
    const hashes: string[] = (rules.hashes ?? []).map((h: string) => h.toLowerCase());
    if (hashes.includes(action.hash.toLowerCase())) {
      return block(`blocked hash: ${action.hash}`, [{ kind: "hash", value: action.hash, source: "blocklist" }]);
    }
  }
  const tool = (action.tool ?? "").slice(0, MAX_TOOL);
  for (const pat of rules.skill_patterns ?? []) {
    const p = String(pat).slice(0, MAX_PATTERN);
    try {
      if (tool && new RegExp(`^(?:${p})$`).test(tool)) {
        return block("blocked by policy: malicious skill pattern", [{ kind: "skill", value: tool, source: "blocklist" }]);
      }
    } catch {
      /* invalid regex, skip */
    }
  }
  return allow();
}

function allowlist(action: Action, rules: Record<string, any>): Verdict {
  const checks: Array<[string, boolean]> = [];
  if (rules.publishers) {
    checks.push(["publisher", action.publisher ? (rules.publishers as string[]).map(norm).includes(norm(action.publisher)) : false]);
  }
  if (rules.tools) {
    checks.push(["tool", action.tool ? (rules.tools as string[]).map(norm).includes(norm(action.tool)) : false]);
  }
  if (rules.domains) {
    const host = hostOf(action.target);
    checks.push(["domain", (rules.domains as string[]).some((d) => domainHit(host, String(d)))]);
  }
  for (const [dim, ok] of checks) {
    if (!ok) return block(`not on the allowlist: ${dim}`, [{ kind: "allowlist", value: dim, source: "allowlist" }]);
  }
  return allow();
}

export function evaluate(action: Action, policies: Policy[]): Verdict {
  for (const p of policies) {
    if (p.enabled === false) continue;
    const rules = p.rules ?? {};
    if (p.mode === "blocklist") {
      const v = blocklist(action, rules);
      if (v.decision === "block") return v;
    } else if (p.mode === "allowlist") {
      const v = allowlist(action, rules);
      if (v.decision === "block") return v;
    }
  }
  return allow();
}
