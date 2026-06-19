import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import {
  completeCallingBotPurchase,
  getCallingBotCall,
  getCallingBotConfig,
  listCallingBotCalls,
  prepareCallingBotPurchase,
  startCallingBotCall,
} from "../lib/api";

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return value;
  }
}

function CallingBotAdminPage() {
  const [config, setConfig] = useState(null);
  const [calls, setCalls] = useState([]);
  const [selectedCallReference, setSelectedCallReference] = useState("");
  const [selectedCall, setSelectedCall] = useState(null);
  const [prepareResult, setPrepareResult] = useState(null);
  const [purchaseResult, setPurchaseResult] = useState(null);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [isLoadingCalls, setIsLoadingCalls] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [startForm, setStartForm] = useState({
    customer_name: "",
    customer_phone: "",
    customer_email: "",
    desired_coverage_amount: "",
    notes: "",
  });
  const [purchaseForm, setPurchaseForm] = useState({
    selected_plan_id: "",
    payment_otp: "",
  });

  const metrics = useMemo(() => {
    const completedCalls = calls.filter((item) => item.status === "completed");
    const activeCalls = calls.filter((item) =>
      ["queued", "initiated", "ringing", "in-progress"].includes(item.status)
    );
    const convertedCalls = calls.filter((item) => item.policy_number);

    return [
      {
        label: "Calls tracked",
        value: calls.length,
        helper: "All outbound bot calls created from the customer admin side",
      },
      {
        label: "Active calls",
        value: activeCalls.length,
        helper: "Queued, ringing, or in-progress outbound conversations",
      },
      {
        label: "Completed calls",
        value: completedCalls.length,
        helper: "Calls that reached a terminal Twilio or purchase state",
      },
      {
        label: "Policies issued",
        value: convertedCalls.length,
        helper: "Calls that converted into a completed policy purchase",
      },
    ];
  }, [calls]);

  useEffect(() => {
    void loadConfig();
    void loadCalls();
  }, []);

  async function loadConfig() {
    setIsLoadingConfig(true);
    try {
      const response = await getCallingBotConfig();
      setConfig(response);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoadingConfig(false);
    }
  }

  async function loadCalls(preferredReference = "") {
    setIsLoadingCalls(true);
    try {
      const response = await listCallingBotCalls();
      const nextCalls = response.items ?? [];
      setCalls(nextCalls);

      const nextReference =
        preferredReference || selectedCallReference || nextCalls[0]?.call_reference || "";
      if (nextReference) {
        await loadCallDetail(nextReference, nextCalls);
      } else {
        setSelectedCallReference("");
        setSelectedCall(null);
      }
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoadingCalls(false);
    }
  }

  async function loadCallDetail(callReference, knownCalls = null) {
    try {
      const detail = await getCallingBotCall(callReference);
      setSelectedCallReference(callReference);
      setSelectedCall(detail);
      setPurchaseResult(null);

      if (detail.selected_plan_id) {
        setPurchaseForm((currentValue) => ({
          ...currentValue,
          selected_plan_id: detail.selected_plan_id,
        }));
      } else if (knownCalls) {
        const fallbackCall = knownCalls.find(
          (item) => item.call_reference === callReference
        );
        if (!detail.selected_plan_id && fallbackCall?.selected_plan_name) {
          setPurchaseForm((currentValue) => ({
            ...currentValue,
            selected_plan_id: currentValue.selected_plan_id,
          }));
        }
      }
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  async function handleStartCall(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: "", message: "" });
    setPrepareResult(null);
    setPurchaseResult(null);

    try {
      const payload = {
        customer_name: startForm.customer_name.trim(),
        customer_phone: startForm.customer_phone.trim(),
        customer_email: startForm.customer_email.trim() || null,
        desired_coverage_amount: startForm.desired_coverage_amount
          ? Number(startForm.desired_coverage_amount)
          : null,
        notes: startForm.notes.trim() || null,
      };
      const response = await startCallingBotCall(payload);
      setStatus({ type: "success", message: response.message });
      setStartForm({
        customer_name: "",
        customer_phone: "",
        customer_email: "",
        desired_coverage_amount: "",
        notes: "",
      });
      await loadCalls(response.call_reference);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handlePreparePurchase() {
    if (!selectedCallReference || !purchaseForm.selected_plan_id.trim()) {
      setStatus({
        type: "error",
        message: "Choose one recommended plan before preparing the payment OTP.",
      });
      return;
    }

    setIsSubmitting(true);
    setStatus({ type: "", message: "" });
    setPurchaseResult(null);

    try {
      const response = await prepareCallingBotPurchase(selectedCallReference, {
        selected_plan_id: purchaseForm.selected_plan_id.trim(),
      });
      setPrepareResult(response);
      setStatus({ type: "success", message: response.message });
      await loadCalls(selectedCallReference);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCompletePurchase(event) {
    event.preventDefault();
    if (!selectedCallReference) {
      return;
    }

    setIsSubmitting(true);
    setStatus({ type: "", message: "" });

    try {
      const response = await completeCallingBotPurchase(selectedCallReference, {
        selected_plan_id: purchaseForm.selected_plan_id.trim(),
        payment_otp: purchaseForm.payment_otp.trim(),
      });
      setPurchaseResult(response);
      setStatus({ type: "success", message: response.message });
      setPurchaseForm((currentValue) => ({ ...currentValue, payment_otp: "" }));
      await loadCalls(selectedCallReference);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Customer-app calling bot</p>
        <h2>Run outbound insurance sales calls, capture coverage needs, and finish the purchase journey.</h2>
        <p className="page-copy">
          This admin section starts Twilio outbound calls from the main backend,
          tracks each conversation, shows matched plans from the database, and
          lets the admin finish the mock OTP and policy issuance flow.
        </p>
      </header>

      <div className="stats-grid">
        {metrics.map((item) => (
          <StatCard
            key={item.label}
            label={item.label}
            value={item.value}
            helper={item.helper}
          />
        ))}
      </div>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard
        title="Bot setup"
        subtitle="Safe calling-bot configuration from the main backend."
        actions={
          <button
            type="button"
            className="secondary-button"
            onClick={loadConfig}
            disabled={isLoadingConfig}
          >
            {isLoadingConfig ? "Refreshing..." : "Refresh config"}
          </button>
        }
      >
        {!config ? (
          <EmptyState
            title="No config loaded yet"
            description="Refresh the bot setup to confirm the Twilio number, masked SID, and flow steps."
          />
        ) : (
          <div className="calling-config-grid">
            <article className="hero-mini-card">
              <strong>{config.bot_name}</strong>
              <p>{config.channel} · {config.mode}</p>
            </article>
            <article className="hero-mini-card">
              <strong>From number</strong>
              <p>{config.twilio_from_number || "Not configured"}</p>
            </article>
            <article className="hero-mini-card">
              <strong>Default test target</strong>
              <p>{config.twilio_test_to_number || "Not configured"}</p>
            </article>
            <article className="hero-mini-card">
              <strong>Webhook base URL</strong>
              <p>{config.webhook_base_url || "Not configured"}</p>
            </article>
            <article className="hero-mini-card">
              <strong>Masked SID</strong>
              <p>{config.masked_account_sid || "Not configured"}</p>
            </article>
            <article className="hero-mini-card">
              <strong>Auth token</strong>
              <p>{config.auth_token_configured ? "Configured" : "Missing"}</p>
            </article>
          </div>
        )}
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Start outbound call" subtitle="Create one customer call and hand the conversation to the bot.">
          <form className="stacked-fields" onSubmit={handleStartCall}>
            <input
              className="field-input"
              value={startForm.customer_name}
              onChange={(event) =>
                setStartForm((currentValue) => ({
                  ...currentValue,
                  customer_name: event.target.value,
                }))
              }
              placeholder="Customer full name"
              required
            />
            <input
              className="field-input"
              value={startForm.customer_phone}
              onChange={(event) =>
                setStartForm((currentValue) => ({
                  ...currentValue,
                  customer_phone: event.target.value,
                }))
              }
              placeholder="Customer phone number"
              required
            />
            <input
              className="field-input"
              type="email"
              value={startForm.customer_email}
              onChange={(event) =>
                setStartForm((currentValue) => ({
                  ...currentValue,
                  customer_email: event.target.value,
                }))
              }
              placeholder="Customer email for policy PDF"
            />
            <input
              className="field-input"
              type="number"
              min="0"
              value={startForm.desired_coverage_amount}
              onChange={(event) =>
                setStartForm((currentValue) => ({
                  ...currentValue,
                  desired_coverage_amount: event.target.value,
                }))
              }
              placeholder="Optional coverage amount"
            />
            <textarea
              className="field-input field-textarea"
              rows="4"
              value={startForm.notes}
              onChange={(event) =>
                setStartForm((currentValue) => ({
                  ...currentValue,
                  notes: event.target.value,
                }))
              }
              placeholder="Optional admin note about this call."
            />
            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "Starting..." : "Start outbound call"}
            </button>
          </form>
        </SectionCard>

        <SectionCard
          title="Call register"
          subtitle="Refresh and inspect each outbound call without copying the old dashboard exactly."
          actions={
            <button
              type="button"
              className="secondary-button"
              onClick={() => loadCalls()}
              disabled={isLoadingCalls}
            >
              {isLoadingCalls ? "Refreshing..." : "Refresh calls"}
            </button>
          }
        >
          {calls.length === 0 ? (
            <EmptyState
              title="No calls tracked yet"
              description="As soon as the admin starts outbound calls, summaries will appear here."
            />
          ) : (
            <div className="calling-call-list">
              {calls.map((item) => (
                <button
                  key={item.call_reference}
                  type="button"
                  className={
                    item.call_reference === selectedCallReference
                      ? "calling-call-item calling-call-item-active"
                      : "calling-call-item"
                  }
                  onClick={() => loadCallDetail(item.call_reference)}
                >
                  <div className="calling-call-item-head">
                    <strong>{item.customer_name}</strong>
                    <span className="info-chip">{item.status}</span>
                  </div>
                  <p>{item.customer_phone}</p>
                  <p>
                    {item.selected_plan_name || "Plan not selected"} · {item.policy_number || "No policy yet"}
                  </p>
                </button>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Selected call details" subtitle="View the call snapshot, recommended plans, transcript, and purchase status.">
        {!selectedCall ? (
          <EmptyState
            title="No call selected"
            description="Choose one call from the register to see its coverage capture, recommendations, and purchase actions."
          />
        ) : (
          <div className="calling-detail-layout">
            <div className="calling-detail-column">
              <div className="calling-detail-grid">
                <article className="mini-card">
                  <h4>{selectedCall.customer_name}</h4>
                  <p>{selectedCall.customer_phone}</p>
                  <p>{selectedCall.customer_email || "No email on record"}</p>
                </article>
                <article className="mini-card">
                  <h4>Status</h4>
                  <p>{selectedCall.status}</p>
                  <p>{selectedCall.customer_interest}</p>
                </article>
                <article className="mini-card">
                  <h4>Coverage</h4>
                  <p>{formatCurrency(selectedCall.desired_coverage_amount)}</p>
                  <p>Duration: {selectedCall.duration_seconds ?? "-"} seconds</p>
                </article>
                <article className="mini-card">
                  <h4>Purchase</h4>
                  <p>{selectedCall.selected_plan_name || "Not selected"}</p>
                  <p>{selectedCall.payment_status || "Payment not started"}</p>
                </article>
              </div>

              <SectionCard title="Recommended plans" subtitle="Plan suggestions prepared after the customer gave a coverage amount.">
                {selectedCall.recommended_plans.length === 0 ? (
                  <EmptyState
                    title="No plans prepared yet"
                    description="Once the bot captures coverage and quotes are generated, matching plans will appear here."
                  />
                ) : (
                  <div className="calling-plan-grid">
                    {selectedCall.recommended_plans.map((plan) => (
                      <button
                        key={plan.plan_id}
                        type="button"
                        className={
                          purchaseForm.selected_plan_id === plan.plan_id
                            ? "calling-plan-card calling-plan-card-active"
                            : "calling-plan-card"
                        }
                        onClick={() =>
                          setPurchaseForm((currentValue) => ({
                            ...currentValue,
                            selected_plan_id: plan.plan_id,
                          }))
                        }
                      >
                        <div className="calling-plan-head">
                          <strong>{plan.plan_name}</strong>
                          <span className="quote-price-badge">
                            {formatCurrency(plan.total_premium)}
                          </span>
                        </div>
                        <p>{plan.company_name}</p>
                        <p>Coverage: {formatCurrency(plan.coverage_amount)}</p>
                      </button>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>

            <div className="calling-detail-column">
              <SectionCard title="Payment and policy actions" subtitle="Prepare the mock OTP first, then confirm the purchase with the customer.">
                <div className="stacked-fields">
                  <div className="info-panel">
                    <p><strong>Call reference:</strong> {selectedCall.call_reference}</p>
                    <p><strong>Twilio SID:</strong> {selectedCall.call_sid || "-"}</p>
                    <p><strong>Transaction:</strong> {selectedCall.transaction_id || "-"}</p>
                    <p><strong>Policy:</strong> {selectedCall.policy_number || "-"}</p>
                    <p><strong>Policy PDF:</strong> {selectedCall.policy_pdf_url || "-"}</p>
                    <p><strong>Policy email status:</strong> {selectedCall.policy_email_status}</p>
                    <p><strong>Created:</strong> {formatDateTime(selectedCall.created_at)}</p>
                  </div>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={handlePreparePurchase}
                    disabled={isSubmitting || !purchaseForm.selected_plan_id}
                  >
                    {isSubmitting ? "Preparing..." : "Generate payment OTP"}
                  </button>

                  {prepareResult ? (
                    <div className="calling-otp-card">
                      <p className="eyebrow-text">Mock OTP preview</p>
                      <h3>{prepareResult.plain_otp || "Hidden"}</h3>
                      <p>
                        Payment reference: {prepareResult.payment_reference}
                      </p>
                      <p>Expires: {formatDateTime(prepareResult.otp_expires_at)}</p>
                    </div>
                  ) : null}

                  <form className="stacked-fields" onSubmit={handleCompletePurchase}>
                    <input
                      className="field-input"
                      value={purchaseForm.selected_plan_id}
                      onChange={(event) =>
                        setPurchaseForm((currentValue) => ({
                          ...currentValue,
                          selected_plan_id: event.target.value,
                        }))
                      }
                      placeholder="Selected plan id"
                      required
                    />
                    <input
                      className="field-input"
                      value={purchaseForm.payment_otp}
                      onChange={(event) =>
                        setPurchaseForm((currentValue) => ({
                          ...currentValue,
                          payment_otp: event.target.value,
                        }))
                      }
                      placeholder="Enter customer OTP"
                      required
                    />
                    <button type="submit" className="primary-button" disabled={isSubmitting}>
                      {isSubmitting ? "Completing..." : "Complete purchase"}
                    </button>
                  </form>

                  {purchaseResult ? (
                    <div className="alert-box alert-success">
                      Policy {purchaseResult.policy_number || "-"} issued successfully.
                    </div>
                  ) : null}
                </div>
              </SectionCard>

              <SectionCard title="Transcript and events" subtitle="Simple event history for the bot conversation and admin follow-up.">
                {selectedCall.transcript_lines.length === 0 ? (
                  <EmptyState
                    title="No transcript lines yet"
                    description="As the call progresses, the backend will append status changes and flow milestones here."
                  />
                ) : (
                  <div className="calling-transcript">
                    {selectedCall.transcript_lines.map((line, index) => (
                      <p key={`${selectedCall.call_reference}-${index}`}>{line}</p>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default CallingBotAdminPage;
