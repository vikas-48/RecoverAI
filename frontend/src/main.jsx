import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  Clock3,
  DollarSign,
  FileText,
  LayoutDashboard,
  ShieldCheck,
  Users,
  XCircle
} from "lucide-react";
import { api } from "./api";
import "./styles.css";

const fallbackCases = [
  {
    payment_id: "PAY200005",
    amount: 21292.06,
    failure_reason: "insufficient_funds",
    attempt_number: 1,
    recovery_probability: 0.87,
    proposed_action: "schedule_retry",
    final_action: "schedule_retry",
    policy_approved: true,
    requires_human: false,
    outcome_status: "recovered",
    amount_recovered: 21292.06,
    success: true
  },
  {
    payment_id: "PAY200011",
    amount: 78120.4,
    failure_reason: "network_error",
    attempt_number: 1,
    recovery_probability: 0.84,
    proposed_action: "schedule_retry",
    final_action: "escalate",
    policy_approved: false,
    requires_human: true,
    outcome_status: "failed",
    amount_recovered: 0,
    success: false
  },
  {
    payment_id: "PAY200006",
    amount: 8200,
    failure_reason: "bank_decline",
    attempt_number: 3,
    recovery_probability: 0.32,
    proposed_action: "stop",
    final_action: "stop",
    policy_approved: false,
    requires_human: false,
    outcome_status: "failed",
    amount_recovered: 0,
    success: false
  }
];

const money = (v) =>
  `₹${Number(v || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0
  })}`;

const percent = (v) =>
  v == null ? "—" : `${(Number(v) * 100).toFixed(1)}%`;

const label = (v = "") =>
  String(v)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (x) => x.toUpperCase());

const eventTime = (timestamp) => {
  if (!timestamp) return "—";

  const value = String(timestamp);

  // Supports both ISO timestamps and the existing audit timestamp format.
  const parsed = new Date(value);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  }

  return value.slice(11, 19) || value;
};

function Metric({ icon: Icon, title, value, detail }) {
  return (
    <div className="metric">
      <div className="metric-icon">
        <Icon size={18} />
      </div>
      <div>
        <div className="metric-title">{title}</div>
        <div className="metric-value">{value}</div>
        <div className="metric-detail">{detail}</div>
      </div>
    </div>
  );
}

function Status({ children, good = false, warn = false }) {
  return (
    <span className={`status ${good ? "good" : ""} ${warn ? "warn" : ""}`}>
      {children}
    </span>
  );
}

function CaseDetails({
  item,
  onRun,
  loading,
  externalRecovery,
  onRefreshExternal
}) {
  const agentUsed =
    item.agent_source === "llm" ||
    item.agent_source === "deterministic_fallback";

  const policyOverrode =
    item.proposed_action &&
    item.final_action &&
    item.proposed_action !== item.final_action;

  return (
    <section className="case-panel">
      {/* CASE HEADER */}
      <div className="case-head">
        <div>
          <div className="eyebrow">RECOVERY CASE</div>
          <h2>{item.payment_id}</h2>
          <p>
            {label(item.failure_reason)} · Attempt {item.attempt_number}
          </p>
        </div>

        <div className="case-amount">{money(item.amount)}</div>
      </div>

      {/* RECOVERY PROBABILITY */}
      <div className="probability">
        <div>
          <span>Recovery probability</span>
          <strong>
            {item.recovery_probability
              ? percent(item.recovery_probability)
              : "—"}
          </strong>
        </div>

        <div className="bar">
          <div
            style={{
              width: `${Math.min(
                100,
                Math.max(0, Number(item.recovery_probability || 0) * 100)
              )}%`
            }}
          />
        </div>
      </div>

      {/* CUSTOMER INTELLIGENCE */}
      {(item.customer_success_rate != null ||
        item.customer_total_payments != null ||
        item.customer_lifetime_value != null) && (
        <div className="customer-card">
          <div className="section-label">CUSTOMER INTELLIGENCE</div>

          <div className="customer-grid">
            <div className="customer-stat">
              <strong>
                {item.customer_success_rate != null
                  ? percent(item.customer_success_rate)
                  : "—"}
              </strong>
              <span>Success rate</span>
            </div>

            <div className="customer-stat">
              <strong>{item.customer_total_payments ?? "—"}</strong>
              <span>Total payments</span>
            </div>

            <div className="customer-stat">
              <strong>
                {item.customer_lifetime_value != null
                  ? money(item.customer_lifetime_value)
                  : "—"}
              </strong>
              <span>Lifetime value</span>
            </div>
          </div>

          <div className="customer-extra">
            {item.average_payment != null && (
              <span>Avg. payment {money(item.average_payment)}</span>
            )}
            {item.days_since_last_success != null && (
              <span>
                Last successful payment {item.days_since_last_success} days ago
              </span>
            )}
            {item.customer_failure_rate != null && (
              <span>
                Failure rate {percent(item.customer_failure_rate)}
              </span>
            )}
          </div>

          {item.customer_success_rate >= 0.9 && (
            <div className="customer-signal">
              <CheckCircle2 size={16} />
              <span>Strong historical payment behavior</span>
            </div>
          )}
        </div>
      )}

      {/* AI DECISION */}
      {agentUsed && (
        <div className="agent-card">
          <div className="agent-card-head">
            <div>
              <div className="eyebrow">AI DECISION</div>
              <h3>
                {item.agent_source === "llm"
                  ? "Gemini Recovery Agent"
                  : "Deterministic Fallback"}
              </h3>
            </div>

            <Status good={item.agent_source === "llm"}>
              {item.agent_source === "llm" ? "LLM" : "FALLBACK"}
            </Status>
          </div>

          <div className="agent-meta">
            <div>
              <span>Proposal</span>
              <strong>
                {item.proposed_action &&
                item.proposed_action !== "pending"
                  ? label(item.proposed_action)
                  : "—"}
              </strong>
            </div>

            <div>
              <span>Confidence</span>
              <strong>
                {item.confidence != null
                  ? `${Math.round(Number(item.confidence) * 100)}%`
                  : "—"}
              </strong>
            </div>

            <div>
              <span>
                {item.agent_source === "llm" ? "Model" : "Source"}
              </span>
              <strong>
                {item.agent_source === "llm"
                  ? item.model || "Gemini"
                  : "Deterministic"}
              </strong>
            </div>

            <div>
              <span>Provider</span>
              <strong>
                {item.agent_source === "llm"
                  ? item.provider || "Gemini"
                  : "Internal fallback"}
              </strong>
            </div>
          </div>

          {item.reason && (
            <div className="agent-reason">
              <span>Agent reasoning</span>
              <p>{item.reason}</p>
            </div>
          )}
        </div>
      )}

      {/* POLICY OVERRIDE */}
      {policyOverrode && (
        <div className="policy-card">
          <div className="policy-card-icon">
            <ShieldCheck size={20} />
          </div>

          <div>
            <div className="eyebrow">POLICY OVERRIDE</div>

            <strong>
              AI proposed {label(item.proposed_action)}
              {" → "}
              Policy selected {label(item.final_action)}
            </strong>

            <span>
              {item.requires_human
                ? "Automatic execution was blocked and human review is required."
                : "The deterministic policy engine changed the proposed action."}
            </span>
          </div>
        </div>
      )}

      {/* RAZORPAY PAYMENT LINK */}
      {item.external_payment_link_url &&
        item.outcome_status !== "recovered" && (
          <div className="outcome">
            <Activity size={22} />

            <div>
              <strong>Razorpay Payment Link ready</strong>
              <span>Complete the payment to verify recovery.</span>

              <a
                href={item.external_payment_link_url}
                target="_blank"
                rel="noreferrer"
              >
                Open payment link →
              </a>
            </div>
          </div>
        )}

      {/* RAZORPAY CONFIRMATION */}
      {externalRecovery?.status === "recovered" && (
        <div className="outcome outcome-good">
          <CheckCircle2 size={22} />

          <div>
            <strong>
              {money(externalRecovery.amount_recovered)} confirmed by Razorpay
            </strong>

            <span>
              Live webhook reconciliation ·{" "}
              {externalRecovery.razorpay_payment_id || "payment confirmed"}
            </span>
          </div>
        </div>
      )}

      {/* ACTIONS */}
      <button
        className="run-btn"
        onClick={() => onRun(item)}
        disabled={loading}
      >
        {loading ? "Running recovery…" : "Run Recovery Agent"}
      </button>

      <button
        className="text-btn"
        onClick={() => onRefreshExternal(item)}
      >
        ↻ Refresh Razorpay status
      </button>

      {/* DECISION TRACE */}
      <div className="decision-trace">
        <div className="section-label">DECISION TRACE</div>

        {/* 01 — ML */}
        <div className="trace-step">
          <div className="trace-number">01</div>

          <div className="trace-content">
            <div className="trace-head">
              <div>
                <span className="trace-type">ML PREDICTION</span>
                <h3>Recovery probability</h3>
              </div>

              <strong className="trace-score">
                {item.recovery_probability
                  ? percent(item.recovery_probability)
                  : "—"}
              </strong>
            </div>

            <p>
              Probability estimated from payment and customer history.
            </p>
          </div>
        </div>

        <div className="trace-line" />

        {/* 02 — AI AGENT */}
        <div className="trace-step">
          <div className="trace-number">02</div>

          <div className="trace-content">
            <div className="trace-head">
              <div>
                <span className="trace-type">AI RECOVERY AGENT</span>
                <h3>
                  {item.agent_source === "llm"
                    ? "Gemini Recovery Agent"
                    : item.agent_source === "deterministic_fallback"
                    ? "Deterministic Fallback"
                    : "Recovery Agent"}
                </h3>
              </div>

              {item.agent_source && (
                <Status good={item.agent_source === "llm"}>
                  {item.agent_source === "llm" ? "LLM" : "FALLBACK"}
                </Status>
              )}
            </div>

            <div className="trace-details">
              <div>
                <span>Proposal</span>
                <strong>
                  {item.proposed_action &&
                  item.proposed_action !== "pending"
                    ? label(item.proposed_action)
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Confidence</span>
                <strong>
                  {item.confidence != null
                    ? `${Math.round(Number(item.confidence) * 100)}%`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>
                  {item.agent_source === "llm" ? "Model" : "Source"}
                </span>
                <strong>
                  {item.agent_source === "llm"
                    ? item.model || "Gemini"
                    : item.agent_source === "deterministic_fallback"
                    ? "Deterministic"
                    : "—"}
                </strong>
              </div>
            </div>

            {item.reason && (
              <div className="trace-reason">
                <span>Agent reasoning</span>
                <p>{item.reason}</p>
              </div>
            )}
          </div>
        </div>

        <div className="trace-line" />

        {/* 03 — POLICY */}
        <div className="trace-step">
          <div className="trace-number">03</div>

          <div className="trace-content">
            <div className="trace-head">
              <div>
                <span className="trace-type">POLICY ENGINE</span>
                <h3>
                  {policyOverrode
                    ? "Proposal overridden"
                    : item.policy_approved
                    ? "Proposal approved"
                    : item.requires_human
                    ? "Human review required"
                    : item.final_action === "stop"
                    ? "Recovery stopped"
                    : "Policy evaluated"}
                </h3>
              </div>

              <Status
                good={Boolean(item.policy_approved)}
                warn={Boolean(policyOverrode || item.requires_human)}
              >
                {policyOverrode
                  ? "OVERRIDE"
                  : item.policy_approved
                  ? "APPROVED"
                  : item.requires_human
                  ? "HUMAN REVIEW"
                  : item.final_action === "stop"
                  ? "BLOCKED"
                  : "PENDING"}
              </Status>
            </div>

            <div className="policy-flow">
              <span>
                {item.proposed_action &&
                item.proposed_action !== "pending"
                  ? label(item.proposed_action)
                  : "AI proposal"}
              </span>

              <b>→</b>

              <strong>
                {item.final_action &&
                item.final_action !== "pending"
                  ? label(item.final_action)
                  : "Waiting"}
              </strong>
            </div>

            {item.requires_human && (
              <p>
                Automatic execution blocked by the high-value policy.
              </p>
            )}
          </div>
        </div>

        <div className="trace-line" />

        {/* 04 — TOOL */}
        <div className="trace-step">
          <div className="trace-number">04</div>

          <div className="trace-content">
            <div className="trace-head">
              <div>
                <span className="trace-type">TOOL EXECUTION</span>
                <h3>
                  {item.final_action &&
                  item.final_action !== "pending"
                    ? label(item.final_action)
                    : "Not executed"}
                </h3>
              </div>

              {item.final_action &&
                item.final_action !== "pending" && (
                  <Status
                    good={item.outcome_status !== "failed"}
                    warn={item.requires_human}
                  >
                    EXECUTED
                  </Status>
                )}
            </div>

            <p>
              {item.requires_human
                ? "Case escalated for human review."
                : item.final_action === "stop"
                ? "Recovery process intentionally stopped."
                : item.final_action &&
                  item.final_action !== "pending"
                ? "Final policy-approved recovery action executed."
                : "Waiting for recovery execution."}
            </p>
          </div>
        </div>

        <div className="trace-line" />

        {/* 05 — OUTCOME */}
        <div className="trace-step trace-final">
          <div className="trace-number">05</div>

          <div className="trace-content">
            <div className="trace-head">
              <div>
                <span className="trace-type">OUTCOME</span>

                <h3>
                  {item.success
                    ? "Revenue recovered"
                    : item.requires_human
                    ? "Human approval required"
                    : item.outcome_status === "pending"
                    ? "Awaiting payment"
                    : item.outcome_status === "failed"
                    ? "Not recovered"
                    : "Not verified"}
                </h3>
              </div>

              {item.success && <CheckCircle2 size={22} />}
            </div>

            <p>
              {item.success
                ? `${money(item.amount_recovered)} successfully recovered.`
                : item.requires_human
                ? "The system intentionally stopped autonomous execution."
                : item.outcome_status === "pending"
                ? "Waiting for Razorpay payment confirmation."
                : "No revenue was recovered from this action."}
            </p>
          </div>
        </div>
      </div>

      {/* DECISION SUMMARY */}
      {item.proposed_action &&
        item.proposed_action !== "pending" && (
          <div className="agent-result">
            <div>
              <span>Agent proposal</span>
              <strong>{label(item.proposed_action)}</strong>
            </div>

            <div>
              <span>Policy</span>
              <strong>
                {item.policy_approved
                  ? "Approved"
                  : item.requires_human
                  ? "Human review"
                  : "Blocked / stopped"}
              </strong>
            </div>

            <div>
              <span>Final action</span>
              <strong>{label(item.final_action)}</strong>
            </div>
          </div>
        )}

      {/* FINAL OUTCOME */}
      <div
        className={`outcome ${
          item.success
            ? "outcome-good"
            : item.requires_human
            ? "outcome-warn"
            : ""
        }`}
      >
        {item.success ? (
          <CheckCircle2 size={22} />
        ) : item.requires_human ? (
          <Users size={22} />
        ) : (
          <XCircle size={22} />
        )}

        <div>
          <strong>
            {item.success
              ? `${money(item.amount_recovered)} recovered`
              : item.requires_human
              ? "Human approval required"
              : item.final_action === "stop"
              ? "Recovery stopped"
              : item.outcome_status === "pending"
              ? "Awaiting payment confirmation"
              : "Ready for evaluation"}
          </strong>

          <span>
            {item.success
              ? "Payment recovery verified successfully."
              : item.outcome_status === "pending"
              ? "Waiting for Razorpay payment confirmation."
              : item.requires_human
              ? "Automatic action blocked by the high-value policy."
              : item.final_action === "stop"
              ? "Stopping rule prevented further automated attempts."
              : "Run the recovery agent to evaluate this payment."}
          </span>
        </div>
      </div>
    </section>
  );
}

function groupAuditRuns(events = []) {
  const runs = [];
  let currentRun = null;

  for (const event of events) {
    if (event.event_type === "CASE_DETECTED") {
      if (currentRun?.length) runs.push(currentRun);
      currentRun = [event];
    } else if (currentRun) {
      currentRun.push(event);
    }
  }

  if (currentRun?.length) runs.push(currentRun);
  return runs.reverse();
}

function App() {
  const [page, setPage] = useState("overview");
  const [payments, setPayments] = useState(fallbackCases);
  const [selected, setSelected] = useState(fallbackCases[0]);
  const [apiOnline, setApiOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [audit, setAudit] = useState([]);
  const [externalRecovery, setExternalRecovery] = useState(null);
  const [showPreviousRuns, setShowPreviousRuns] = useState(false);

  useEffect(() => {
    api
      .health()
      .then(() => {
        setApiOnline(true);
        return Promise.all([api.payments(25), api.analytics()]);
      })
      .then(([p, a]) => {
        const mapped = p.payments.map((x) => ({
          ...x,
          amount: Number(x.amount),
          recovery_probability: 0,
          proposed_action: "pending",
          final_action: "pending",
          policy_approved: false,
          requires_human: false,
          outcome_status: "pending",
          amount_recovered: 0,
          success: false
        }));

        if (mapped.length) {
          setPayments(mapped);
          setSelected(mapped[0]);
        }

        setAnalytics(a);
      })
      .catch(() => setApiOnline(false));
  }, []);

  async function selectCase(item) {
    setSelected(item);
    setExternalRecovery(null);
    setAudit([]);
    setShowPreviousRuns(false);

    try {
      const a = await api.audit(item.payment_id);
      const events = a.events || [];
      setAudit(events);

      const caseEvent = [...events].reverse().find((e) => e.event_type === "CASE_DETECTED");
      const agentEvent = [...events].reverse().find((e) => e.event_type === "AGENT_PROPOSAL");
      const policyEvent = [...events].reverse().find((e) => e.event_type === "POLICY_DECISION");

      const caseData = caseEvent?.payload || {};
      const agentData = agentEvent?.payload || {};
      const policyData = policyEvent?.payload || {};

      const enriched = {
        ...item,
        customer_id: caseData.customer_id,
        customer_lifetime_value: caseData.customer_lifetime_value,
        customer_total_payments: caseData.customer_total_payments,
        customer_success_rate: caseData.customer_success_rate,
        customer_failure_rate: caseData.customer_failure_rate,
        average_payment: caseData.average_payment,
        days_since_last_success: caseData.days_since_last_success,
        recovery_probability: caseData.recovery_probability ?? item.recovery_probability,
        proposed_action: agentData.action ?? item.proposed_action,
        agent_source: agentData.agent_source,
        provider: agentData.provider,
        model: agentData.model,
        confidence: agentData.confidence,
        reason: agentData.reason,
        final_action: policyData.final_action ?? item.final_action,
        policy_approved: policyData.approved ?? item.policy_approved,
        requires_human: policyData.requires_human ?? item.requires_human
      };

      setSelected(enriched);
      setPayments((xs) => xs.map((x) =>
        x.payment_id === item.payment_id ? enriched : x
      ));
    } catch (e) {
      console.error("Could not load case audit:", e);
    }
  }

  async function runRecovery(item) {
    setLoading(true);

    try {
      // 1. Run the recovery agent.
      const result = await api.runRecovery(item.payment_id);

      const updated = {
        ...item,
        ...result,
        amount: Number(item.amount)
      };

      setExternalRecovery(null);

      // 2. Fetch the audit trail generated by the backend.
      const a = await api.audit(item.payment_id);
      const events = a.events || [];

      setAudit(events);

      // 3. Extract the case context recorded by CASE_DETECTED.
      const caseEvent = [...events]
        .reverse()
        .find((e) => e.event_type === "CASE_DETECTED");

      // 4. Extract the agent proposal recorded by AGENT_PROPOSAL.
      const agentEvent = [...events]
        .reverse()
        .find((e) => e.event_type === "AGENT_PROPOSAL");

      // 5. Enrich the selected case with real backend/audit data.
      const caseData = caseEvent?.payload || {};
      const agentData = agentEvent?.payload || {};

      const enriched = {
        ...updated,

        // Customer intelligence
        customer_id: caseData.customer_id,
        customer_lifetime_value: caseData.customer_lifetime_value,
        customer_total_payments: caseData.customer_total_payments,
        customer_success_rate: caseData.customer_success_rate,
        customer_failure_rate: caseData.customer_failure_rate,
        average_payment: caseData.average_payment,
        days_since_last_success: caseData.days_since_last_success,

        // ML prediction
        recovery_probability:
          caseData.recovery_probability ??
          updated.recovery_probability,

        // Agent provenance
        agent_source: agentData.agent_source,
        provider: agentData.provider,
        model: agentData.model,
        confidence: agentData.confidence,

        // IMPORTANT: use the agent's reason, not the tool/outcome message.
        reason: agentData.reason
      };

      setSelected(enriched);

      setPayments((xs) =>
        xs.map((x) =>
          x.payment_id === item.payment_id ? enriched : x
        )
      );

      // 6. Check Razorpay external recovery state.
      const ext = await api.externalRecovery(item.payment_id);
      setExternalRecovery(ext);
    } catch (e) {
      setSelected({
        ...item,
        outcome_status: "failed",
        final_action: "error",
        reason: e.message
      });
    } finally {
      setLoading(false);
    }
  }

  async function refreshExternal(item = selected) {
    if (!item?.payment_id) return;

    try {
      const ext = await api.externalRecovery(item.payment_id);

      setExternalRecovery(ext);

      if (ext.status === "recovered") {
        setSelected((x) => ({
          ...x,
          outcome_status: "recovered",
          success: true,
          amount_recovered: ext.amount_recovered
        }));

        setPayments((xs) =>
          xs.map((x) =>
            x.payment_id === item.payment_id
              ? {
                  ...x,
                  outcome_status: "recovered",
                  success: true,
                  amount_recovered: ext.amount_recovered
                }
              : x
          )
        );
      }

      const a = await api.audit(item.payment_id);
      setAudit(a.events || []);
    } catch (e) {
      setExternalRecovery({
        status: "error",
        message: e.message
      });
    }
  }

  const stats = useMemo(() => {
    if (!analytics) {
      return {
        risk: 36900000,
        expected: 15000000,
        recovered: 15100000,
        interventions: 2004
      };
    }

    return {
      risk: analytics.recoverai.total_revenue_at_risk,
      expected: analytics.recoverai.expected_revenue_recovered,
      recovered: analytics.recoverai.simulated_revenue_recovered,
      interventions: analytics.recoverai.interventions
    };
  }, [analytics]);

  const auditRuns = groupAuditRuns(audit);
  const latestRun = auditRuns[0] || [];
  const previousRuns = auditRuns.slice(1);

  const latestAgentProposal = [...latestRun]
    .reverse()
    .find((e) => e.event_type === "AGENT_PROPOSAL");

  const latestAgentCall = [...latestRun]
    .reverse()
    .find((e) => e.event_type === "AGENT_LLM_CALL");

  const latestPolicy = [...latestRun]
    .reverse()
    .find((e) => e.event_type === "POLICY_DECISION");

  const latestOutcome = [...latestRun]
    .reverse()
    .find((e) => e.event_type === "OUTCOME_VERIFIED");

  const latestTool = [...latestRun]
    .reverse()
    .find((e) => e.event_type === "TOOL_EXECUTION");

  const latestCase = [...latestRun]
    .reverse()
    .find((e) => e.event_type === "CASE_DETECTED");

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={20} />
          </div>

          <div>
            <strong>RecoverAI</strong>
            <span>Revenue recovery</span>
          </div>
        </div>

        <nav>
          {[
            [LayoutDashboard, "overview", "Overview"],
            [Bot, "queue", "Recovery Queue"],
            [ShieldCheck, "analytics", "Analytics"],
            [FileText, "audit", "Audit Trail"]
          ].map(([Icon, id, name]) => (
            <button
              className={page === id ? "nav-active" : ""}
              onClick={() => setPage(id)}
              key={id}
            >
              <Icon size={18} /> {name}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="live">
            <span />{" "}
            {apiOnline ? "Live API connected" : "Simulation environment"}
          </div>
          <small>Razorpay buildathon prototype</small>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="eyebrow">MERCHANT CONTROL CENTER</div>
            <h1>
              {page === "overview"
                ? "Recovery overview"
                : page === "queue"
                ? "Recovery queue"
                : page === "analytics"
                ? "Recovery analytics"
                : "Audit trail"}
            </h1>
          </div>

          <div className="top-actions">
            <span className={`api-pill ${apiOnline ? "online" : ""}`}>
              <span /> {apiOnline ? "API connected" : "Demo mode"}
            </span>

            <button className="date-btn">
              <Clock3 size={16} /> Last 30 days
            </button>
          </div>
        </header>

        {/* OVERVIEW */}
        {page === "overview" && (
          <>
            <div className="metrics-grid">
              <Metric
                icon={DollarSign}
                title="Revenue at risk"
                value={money(stats.risk)}
                detail="Failed payment volume"
              />

              <Metric
                icon={ArrowUpRight}
                title="Expected recovery"
                value={money(stats.expected)}
                detail={
                  analytics
                    ? `+${Math.round(
                        analytics.expected_revenue_improvement * 100
                      )}% vs baseline`
                    : "+16% vs baseline"
                }
              />

              <Metric
                icon={CheckCircle2}
                title="Recovered"
                value={money(stats.recovered)}
                detail="Verified/simulated outcomes"
              />

              <Metric
                icon={Bot}
                title="Interventions"
                value={stats.interventions.toLocaleString()}
                detail={
                  analytics
                    ? `${Math.round(
                        analytics.intervention_reduction * 100
                      )}% fewer than baseline`
                    : "24% fewer than baseline"
                }
              />
            </div>

            <div className="grid-two">
              <div className="card">
                <div className="card-head">
                  <div>
                    <h3>Recovery funnel</h3>
                    <span>Held-out evaluation batch</span>
                  </div>
                </div>

                <div className="funnel">
                  <div>
                    <span>Failed payments</span>
                    <strong>3,000</strong>
                  </div>

                  <div>
                    <span>Actionable cases</span>
                    <strong>{stats.interventions.toLocaleString()}</strong>
                  </div>

                  <div>
                    <span>Expected recovered</span>
                    <strong>{money(stats.expected)}</strong>
                  </div>

                  <div className="funnel-final">
                    <span>Recovered revenue</span>
                    <strong>{money(stats.recovered)}</strong>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-head">
                  <div>
                    <h3>Why RecoverAI?</h3>
                    <span>Decision quality over blind retries</span>
                  </div>
                </div>

                <div className="principles">
                  <div>
                    <ShieldCheck />
                    <div>
                      <strong>AI proposes, policy authorizes</strong>
                      <span>
                        Money-moving actions remain behind deterministic
                        guardrails.
                      </span>
                    </div>
                  </div>

                  <div>
                    <Bot />
                    <div>
                      <strong>Predict before acting</strong>
                      <span>
                        Recovery probability combines payment and customer
                        context.
                      </span>
                    </div>
                  </div>

                  <div>
                    <Activity />
                    <div>
                      <strong>Measure the outcome</strong>
                      <span>
                        Every action is verified and written to the audit
                        trail.
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-head">
                <div>
                  <h3>Recovery cases</h3>
                  <span>
                    {apiOnline ? "Live dataset" : "Demo scenarios"}
                  </span>
                </div>

                <button
                  className="text-btn"
                  onClick={() => setPage("queue")}
                >
                  View queue →
                </button>
              </div>

              <div className="case-list">
                {payments.slice(0, 8).map((item) => (
                  <button
                    className="case-row"
                    key={item.payment_id}
                    onClick={async () => {
                      await selectCase(item);
                      setPage("queue");
                    }}
                  >
                    <div>
                      <strong>{item.payment_id}</strong>
                      <span>{label(item.failure_reason)}</span>
                    </div>

                    <strong>{money(item.amount)}</strong>

                    <Status
                      good={item.success}
                      warn={item.requires_human}
                    >
                      {item.success
                        ? "Recovered"
                        : item.requires_human
                        ? "Human review"
                        : item.final_action === "stop"
                        ? "Stopped"
                        : "Unprocessed"}
                    </Status>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* RECOVERY QUEUE */}
        {page === "queue" && (
          <div className="queue-layout">
            <div className="card">
              <div className="card-head">
                <div>
                  <h3>Recovery queue</h3>
                  <span>Select a case to inspect the decision trace</span>
                </div>
              </div>

              <div className="case-list">
                {payments.slice(0, 15).map((item) => (
                  <button
                    className={`case-row ${
                      selected.payment_id === item.payment_id
                        ? "selected"
                        : ""
                    }`}
                    key={item.payment_id}
                    onClick={async () => await selectCase(item)}
                  >
                    <div>
                      <strong>{item.payment_id}</strong>
                      <span>
                        {label(item.failure_reason)} · Attempt{" "}
                        {item.attempt_number}
                      </span>
                    </div>

                    <strong>{money(item.amount)}</strong>

                    <Status
                      good={item.success}
                      warn={item.requires_human}
                    >
                      {item.success
                        ? "Recovered"
                        : item.requires_human
                        ? "Human review"
                        : item.final_action === "stop"
                        ? "Stopped"
                        : "Ready"}
                    </Status>
                  </button>
                ))}
              </div>
            </div>

            <CaseDetails
              item={selected}
              onRun={runRecovery}
              loading={loading}
              externalRecovery={externalRecovery}
              onRefreshExternal={refreshExternal}
            />
          </div>
        )}

        {/* ANALYTICS */}
        {page === "analytics" && (
          <div className="card analytics">
            <div className="card-head">
              <div>
                <h3>Baseline vs RecoverAI</h3>
                <span>Synthetic held-out test evaluation</span>
              </div>
            </div>

            <div className="comparison">
              <div>
                <span>RecoverAI expected</span>
                <div className="compare-bar">
                  <i style={{ width: "86%" }} />
                </div>
                <strong>{money(stats.expected)}</strong>
              </div>

              <div>
                <span>Baseline expected</span>
                <div className="compare-bar">
                  <i style={{ width: "74%" }} />
                </div>
                <strong>
                  {money(
                    analytics?.baseline?.expected_revenue_recovered ||
                      12900000
                  )}
                </strong>
              </div>

              <div className="big-callout">
                <strong>
                  +
                  {analytics
                    ? Math.round(
                        analytics.expected_revenue_improvement * 100
                      )
                    : 16}
                  %
                </strong>
                <span>
                  expected recovered revenue vs naive retry baseline
                </span>
              </div>
            </div>
          </div>
        )}

        {/* AUDIT TRAIL */}
        {page === "audit" && (
          <div className="audit-page">
            <div className="audit-header">
              <div>
                <div className="eyebrow">SYSTEM OBSERVABILITY</div>
                <h2>Decision audit</h2>
                <p>Trace every recovery decision from prediction to verified outcome.</p>
              </div>
              <div className="audit-case">
                <span>CASE</span>
                <strong>{selected.payment_id}</strong>
              </div>
            </div>

            <div className="audit-summary">
              <div><span>Latest run</span><strong>{latestRun.length || "—"} events</strong></div>
              <div><span>Agent</span><strong>{latestAgentProposal?.payload?.agent_source === "llm" ? "Gemini" : latestAgentProposal ? "Fallback" : "—"}</strong></div>
              <div><span>Policy</span><strong>{latestPolicy?.payload?.approved ? "Approved" : latestPolicy?.payload?.requires_human ? "Override" : latestPolicy ? "Blocked" : "—"}</strong></div>
              <div><span>Outcome</span><strong>{latestOutcome?.payload?.status ? label(latestOutcome.payload.status) : latestTool?.payload?.action === "escalate" ? "Human review" : "—"}</strong></div>
            </div>

            {latestRun.length > 0 ? (
              <>
                <div className="audit-run-header">
                  <div>
                    <div className="eyebrow">LATEST RUN</div>
                    <strong>{latestCase?.timestamp ? eventTime(latestCase.timestamp) : "Current recovery execution"}</strong>
                    <span>{latestRun.length} recorded events</span>
                  </div>
                  <Status good={latestAgentCall?.payload?.status === "success"} warn={latestAgentCall?.payload?.status === "fallback"}>
                    {latestAgentCall?.payload?.status === "success" ? "GEMINI ACTIVE" : latestAgentCall?.payload?.status === "fallback" ? "SAFE FALLBACK" : "RECORDED"}
                  </Status>
                </div>

                <div className="audit-events">
                  {latestRun.map((e, index) => {
                    const payload = e.payload || {};
                    return (
                      <div className="audit-event" key={e.event_id ?? index}>
                        <div className="audit-event-index">{String(index + 1).padStart(2, "0")}</div>
                        <div className="audit-event-main">
                          <div className="audit-event-head">
                            <div>
                              <span className="audit-event-type">{label(e.event_type)}</span>
                              <strong>{e.payment_id}</strong>
                            </div>
                            <span className="audit-event-time">{eventTime(e.timestamp)}</span>
                          </div>

                          {e.event_type === "CASE_DETECTED" && (
                            <>
                              <div className="audit-detail-grid">
                                <div><span>Amount</span><strong>{money(payload.amount)}</strong></div>
                                <div><span>Failure</span><strong>{label(payload.failure_reason)}</strong></div>
                                <div><span>Recovery probability</span><strong>{percent(payload.recovery_probability)}</strong></div>
                                <div><span>Attempt</span><strong>{payload.attempt_number ?? "—"}</strong></div>
                              </div>
                              <div className="audit-customer-row">
                                <span>Customer success <strong>{percent(payload.customer_success_rate)}</strong></span>
                                <span>Payments <strong>{payload.customer_total_payments ?? "—"}</strong></span>
                                <span>CLV <strong>{payload.customer_lifetime_value != null ? money(payload.customer_lifetime_value) : "—"}</strong></span>
                              </div>
                            </>
                          )}

                          {e.event_type === "AGENT_LLM_CALL" && (
                            <div className="audit-call">
                              <Status good={payload.status === "success"} warn={payload.status === "fallback"}>
                                {payload.status === "success" ? "SUCCESS" : payload.status === "fallback" ? "SAFE FALLBACK" : label(payload.status || "RECORDED")}
                              </Status>
                              <div><span>Provider</span><strong>{payload.provider || "—"}</strong></div>
                              <div><span>Model</span><strong>{payload.model || "—"}</strong></div>
                              {payload.status === "fallback" && <div className="audit-fallback-note">Gemini temporarily unavailable. Deterministic fallback used safely.</div>}
                            </div>
                          )}

                          {e.event_type === "AGENT_PROPOSAL" && (
                            <div className="audit-proposal">
                              <div><span>Proposal</span><strong>{label(payload.action)}</strong></div>
                              <div><span>Confidence</span><strong>{payload.confidence != null ? `${Math.round(Number(payload.confidence) * 100)}%` : "—"}</strong></div>
                              <div><span>Source</span><strong>{payload.agent_source === "llm" ? "Gemini" : "Deterministic fallback"}</strong></div>
                              {payload.reason && <p>{payload.reason}</p>}
                            </div>
                          )}

                          {e.event_type === "POLICY_DECISION" && (
                            <div className="audit-policy">
                              <Status good={Boolean(payload.approved)} warn={Boolean(payload.requires_human)}>
                                {payload.approved ? "APPROVED" : payload.requires_human ? "OVERRIDE" : "BLOCKED"}
                              </Status>
                              <div className="audit-policy-flow"><span>Final action</span><strong>{label(payload.final_action)}</strong></div>
                              {payload.reason && <p>{payload.reason}</p>}
                            </div>
                          )}

                          {e.event_type === "TOOL_EXECUTION" && (
                            <div className="audit-tool">
                              <div><span>Action</span><strong>{label(payload.action)}</strong></div>
                              <Status good={Boolean(payload.success)} warn={!payload.success}>{payload.success ? "EXECUTED" : "FAILED"}</Status>
                              {payload.message && <p>{payload.message}</p>}
                            </div>
                          )}

                          {e.event_type === "OUTCOME_VERIFIED" && (
                            <div className="audit-outcome">
                              <Status good={payload.status === "recovered"} warn={payload.status === "pending"}>{label(payload.status)}</Status>
                              <strong>{payload.amount_recovered != null ? money(payload.amount_recovered) : "—"}</strong>
                              {payload.message && <span>{payload.message}</span>}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="audit-empty">
                <FileText size={24} />
                <strong>No audit events yet</strong>
                <span>Run a recovery case to populate the live decision trace.</span>
              </div>
            )}

            {previousRuns.length > 0 && (
              <div className="previous-runs">
                <button className="previous-runs-toggle" onClick={() => setShowPreviousRuns((value) => !value)}>
                  <span>Previous runs <small>{previousRuns.length}</small></span>
                  <span>{showPreviousRuns ? "Hide ↑" : "Show ↓"}</span>
                </button>

                {showPreviousRuns && (
                  <div className="previous-runs-list">
                    {previousRuns.map((run, runIndex) => {
                      const caseEvent = run.find((e) => e.event_type === "CASE_DETECTED");
                      const agentCall = run.find((e) => e.event_type === "AGENT_LLM_CALL");
                      const proposal = run.find((e) => e.event_type === "AGENT_PROPOSAL");

                      return (
                        <div className="previous-run" key={caseEvent?.event_id || runIndex}>
                          <div><span>RUN</span><strong>{previousRuns.length - runIndex}</strong></div>
                          <div><span>Time</span><strong>{caseEvent?.timestamp ? eventTime(caseEvent.timestamp) : "Previous execution"}</strong></div>
                          <div><span>Agent</span><strong>{proposal?.payload?.agent_source === "llm" ? "Gemini" : "Fallback"}</strong></div>
                          <div><span>Status</span><strong>{agentCall?.payload?.status === "fallback" ? "LLM fallback" : "Completed"}</strong></div>
                          <div><span>Events</span><strong>{run.length}</strong></div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
  