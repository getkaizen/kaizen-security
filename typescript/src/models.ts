export interface Action {
  kind?: string;
  tool?: string;
  publisher?: string;
  target?: string;
  hash?: string;
  metadata?: Record<string, unknown>;
}

export type Decision = "allow" | "block";

export interface Finding {
  kind: string;
  value: string;
  source: string;
}

export interface Verdict {
  decision: Decision;
  /** Convenience flag, true when decision is "block". Mirrors the Python SDK. */
  blocked: boolean;
  reason: string;
  evidence: Finding[];
}

export type PolicyMode = "blocklist" | "allowlist" | "correlation";

export interface Policy {
  mode: PolicyMode;
  rules: Record<string, any>;
  name?: string;
  enabled?: boolean;
}

export function isBlocked(v: Verdict): boolean {
  return v.decision === "block";
}

export function allow(reason = "no policy matched"): Verdict {
  return { decision: "allow", blocked: false, reason, evidence: [] };
}

export function block(reason: string, evidence: Finding[] = []): Verdict {
  return { decision: "block", blocked: true, reason, evidence };
}
