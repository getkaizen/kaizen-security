import { Action, Policy, Verdict, allow, block, isBlocked } from "./models";
import { evaluate } from "./engine";

export class KaizenBlocked extends Error {
  verdict: Verdict;
  constructor(verdict: Verdict) {
    super(verdict.reason);
    this.name = "KaizenBlocked";
    this.verdict = verdict;
  }
}

export interface KaizenOptions {
  apiKey?: string;
  baseUrl?: string;
  policies?: Policy[];
  agent?: string;
  failOpen?: boolean;
  report?: boolean;
  onVerdict?: (v: Verdict, a: Action) => void;
}

export class Kaizen {
  apiKey: string;
  baseUrl: string;
  policies: Policy[];
  agent: string;
  failOpen: boolean;
  private report: boolean;
  private onVerdict?: (v: Verdict, a: Action) => void;

  constructor(opts: KaizenOptions = {}) {
    this.apiKey = opts.apiKey ?? "";
    this.baseUrl = (opts.baseUrl ?? "https://api.getkaizen.io").replace(/\/+$/, "");
    this.policies = opts.policies ?? [];
    this.agent = opts.agent ?? "default";
    this.failOpen = opts.failOpen ?? false;
    this.report = opts.report ?? true;
    this.onVerdict = opts.onVerdict;
  }

  inspect(action: Action): Verdict {
    let v: Verdict;
    try {
      v = evaluate(action, this.policies);
    } catch {
      v = this.failOpen ? allow("engine error, failed open") : block("engine error, failed closed");
    }
    if (this.apiKey && this.report) this.send(action, v);
    if (this.onVerdict) {
      try {
        this.onVerdict(v, action);
      } catch {
        /* ignore */
      }
    }
    return v;
  }

  enforce(action: Action): Verdict {
    const v = this.inspect(action);
    if (isBlocked(v)) throw new KaizenBlocked(v);
    return v;
  }

  private send(action: Action, verdict: Verdict): void {
    // best-effort, fire and forget
    fetch(`${this.baseUrl}/v1/verdicts`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({ agent: this.agent, action, verdict }),
    }).catch(() => {
      /* network errors are non-fatal */
    });
  }
}
