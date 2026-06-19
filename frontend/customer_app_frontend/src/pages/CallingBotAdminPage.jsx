import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import {
  completeCallingBotPurchase,
  getCallingBotCall,
  listCallingBotCalls,
  prepareCallingBotPurchase,
  startCallingBotCall,
} from "../lib/api";

const ACTIVE_CALL_STATUSES = ["queued", "initiated", "ringing", "in-progress"];

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  try {
    return new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    }).format(new Date(value));
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

function formatDuration(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const totalSeconds = Number(value);
  if (Number.isNaN(totalSeconds) || totalSeconds < 0) {
    return "-";
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function getCallDurationSeconds(call) {
  if (call?.duration_seconds !== null && call?.duration_seconds !== undefined) {
    return Number(call.duration_seconds);
  }

  if (!call?.created_at) {
    return null;
  }

  const startedAt = new Date(call.created_at).getTime();
  const endedAt = call.completed_at
    ? new Date(call.completed_at).getTime()
    : call.updated_at
      ? new Date(call.updated_at).getTime()
      : Date.now();

  if (Number.isNaN(startedAt) || Number.isNaN(endedAt) || endedAt < startedAt) {
    return null;
  }

  return Math.floor((endedAt - startedAt) / 1000);
}

function getTranscriptAppearance(line) {
  if (line.startsWith("Bot:")) {
    return {
      role: "Bot",
      content: line.replace("Bot:", "").trim(),
      className: "calling-transcript-entry calling-transcript-bot",
    };
  }

  if (line.startsWith("Customer:")) {
    return {
      role: "Customer",
      content: line.replace("Customer:", "").trim(),
      className: "calling-transcript-entry calling-transcript-customer",
    };
  }

  if (line.startsWith("System:")) {
    return {
      role: "System",
      content: line.replace("System:", "").trim(),
      className: "calling-transcript-entry calling-transcript-system",
    };
  }

  return {
    role: "System",
    content: line,
    className: "calling-transcript-entry calling-transcript-system",
  };
}

function CallingBotAdminPage() {
  const [calls, setCalls] = useState([]);
  const [selectedCallReference, setSelectedCallReference] = useState("");
  const [selectedCall, setSelectedCall] = useState(null);
  const [expandedConversationReference, setExpandedConversationReference] = useState("");
  const [prepareResult, setPrepareResult] = useState(null);
  const [purchaseResult, setPurchaseResult] = useState(null);
  const [status, setStatus] = useState({ type: "", message: "" });
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
    const activeCalls = calls.filter((item) => ACTIVE_CALL_STATUSES.includes(item.status));
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
      {
        label: "Total call minutes",
        value: Math.round(
          calls.reduce(
            (total, item) => total + Number(getCallDurationSeconds(item) || 0),
            0
          ) / 60
        ),
        helper: "Combined completed duration across tracked calls",
      },
    ];
  }, [calls]);

  useEffect(() => {
    void loadCalls();
  }, []);

  useEffect(() => {
    const shouldPoll =
      Boolean(expandedConversationReference) ||
      Boolean(selectedCallReference) ||
      calls.some((item) => ACTIVE_CALL_STATUSES.includes(item.status));

    if (!shouldPoll) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      const preferredReference =
        expandedConversationReference || selectedCallReference || "";
      void loadCalls(preferredReference);
    }, 5000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [calls, expandedConversationReference, selectedCallReference]);

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

  async function handleConversationToggle(callReference) {
    if (expandedConversationReference === callReference) {
      setExpandedConversationReference("");
      return;
    }

    await loadCallDetail(callReference);
    setExpandedConversationReference(callReference);
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

      <div className="stats-grid stats-grid-calling">
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
          subtitle="View outbound call history with status, date, duration, and customer progress."
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
                <article key={item.call_reference} className="calling-call-record">
                  <button
                    type="button"
                    className={
                      item.call_reference === selectedCallReference
                        ? "calling-call-item calling-call-item-active"
                        : "calling-call-item"
                    }
                    onClick={() => loadCallDetail(item.call_reference)}
                  >
                    <div className="calling-call-item-head">
                      <div>
                        <strong>{item.customer_name}</strong>
                        <p className="calling-call-meta">
                          {formatDateTime(item.created_at)} IST
                        </p>
                      </div>
                      <span className="info-chip">{item.status}</span>
                    </div>
                    <p>{item.customer_phone}</p>
                    <p>
                      {item.selected_plan_name || "Plan not selected"} · {item.policy_number || "No policy yet"}
                    </p>
                    <p>
                      Interest: {item.customer_interest || "unknown"} · Email status: {item.policy_email_status}
                    </p>
                    <p>
                      Call duration: {formatDuration(getCallDurationSeconds(item))}
                    </p>
                    <p>
                      Conversation lines: {selectedCallReference === item.call_reference && selectedCall ? selectedCall.transcript_lines.length : "-"}
                    </p>
                  </button>

                  <div className="calling-call-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => handleConversationToggle(item.call_reference)}
                    >
                      {expandedConversationReference === item.call_reference
                        ? "Hide conversation"
                        : "View conversation"}
                    </button>
                  </div>

                  {expandedConversationReference === item.call_reference &&
                  selectedCallReference === item.call_reference &&
                  selectedCall ? (
                    <div className="calling-call-conversation">
                      <div className="section-card-header">
                        <div>
                          <h3>{selectedCall.customer_name} conversation</h3>
                          <p>
                            Full calling-bot exchange for this customer, stored under this call record.
                          </p>
                        </div>
                      </div>
                      <div className="calling-transcript">
                        {selectedCall.transcript_lines.length === 0 ? (
                          <EmptyState
                            title="No conversation captured yet"
                            description="As the call progresses, the full customer and bot conversation will appear here."
                          />
                        ) : (
                          selectedCall.transcript_lines.map((line, index) => {
                            const transcriptItem = getTranscriptAppearance(line);
                            return (
                              <article
                                key={`${selectedCall.call_reference}-${index}`}
                                className={transcriptItem.className}
                              >
                                <span className="calling-transcript-role">
                                  {transcriptItem.role}
                                </span>
                                <p>{transcriptItem.content}</p>
                              </article>
                            );
                          })
                        )}
                      </div>
                    </div>
                  ) : null}
                </article>
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
                  <h4>Coverage and timing</h4>
                  <p>{formatCurrency(selectedCall.desired_coverage_amount)}</p>
                  <p>Duration: {formatDuration(getCallDurationSeconds(selectedCall))}</p>
                </article>
                <article className="mini-card">
                  <h4>Purchase</h4>
                  <p>{selectedCall.selected_plan_name || "Not selected"}</p>
                  <p>{selectedCall.payment_status || "Payment not started"}</p>
                </article>
              </div>

              <SectionCard
                title="Call history details"
                subtitle="Track how long the call lasted and when it moved through the flow."
              >
                <div className="calling-history-grid">
                  <article className="mini-card">
                    <h4>Started</h4>
                    <p>{formatDateTime(selectedCall.created_at)} IST</p>
                  </article>
                  <article className="mini-card">
                    <h4>Last updated</h4>
                    <p>{formatDateTime(selectedCall.updated_at)} IST</p>
                  </article>
                  <article className="mini-card">
                    <h4>Completed</h4>
                    <p>{formatDateTime(selectedCall.completed_at)} IST</p>
                  </article>
                  <article className="mini-card">
                    <h4>Total duration</h4>
                    <p>{formatDuration(getCallDurationSeconds(selectedCall))}</p>
                  </article>
                </div>
              </SectionCard>

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
                    <p><strong>Created:</strong> {formatDateTime(selectedCall.created_at)} IST</p>
                    <p><strong>Updated:</strong> {formatDateTime(selectedCall.updated_at)} IST</p>
                    <p><strong>Completed:</strong> {formatDateTime(selectedCall.completed_at)} IST</p>
                    <p><strong>Call duration:</strong> {formatDuration(getCallDurationSeconds(selectedCall))}</p>
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

            </div>
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default CallingBotAdminPage;
