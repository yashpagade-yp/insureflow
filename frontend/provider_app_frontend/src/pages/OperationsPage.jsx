import { useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import {
  getAdminPayment,
  getAdminQuote,
  listPayments,
  listQuotes,
} from "../lib/api";

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

function OperationsPage() {
  const [quotes, setQuotes] = useState([]);
  const [payments, setPayments] = useState([]);
  const [quoteLookup, setQuoteLookup] = useState("");
  const [paymentLookup, setPaymentLookup] = useState("");
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(false);

  async function loadOperations() {
    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const [quoteResponse, paymentResponse] = await Promise.all([
        listQuotes(),
        listPayments(),
      ]);
      setQuotes(quoteResponse.items ?? []);
      setPayments(paymentResponse.items ?? []);
      setStatus({
        type: "success",
        message: "Quote and payment activity loaded successfully.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleQuoteLookup() {
    if (!quoteLookup) {
      return;
    }

    try {
      const response = await getAdminQuote(quoteLookup);
      setSelectedQuote(response);
      setStatus({ type: "success", message: "Quote details loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  async function handlePaymentLookup() {
    if (!paymentLookup) {
      return;
    }

    try {
      const response = await getAdminPayment(paymentLookup);
      setSelectedPayment(response);
      setStatus({ type: "success", message: "Payment details loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  return (
    <div className="page-stack">
      <section className="command-subhero">
        <p className="eyebrow-text">Live operations</p>
        <h2>Inspect the provider-side quote and payment pipeline in real time.</h2>
        <p className="muted-copy">
          This is the operations layer of the provider app: transaction lookups, payment checks,
          and activity monitoring without customer-facing styling.
        </p>
      </section>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard
        title="Refresh provider operations"
        subtitle="Load the latest provider-side quote and payment queues."
        actions={
          <button
            type="button"
            className="primary-button"
            onClick={loadOperations}
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh operations"}
          </button>
        }
      >
        <div className="banner-grid">
          <article className="hero-mini-card">
            <strong>{quotes.length}</strong>
            <p>Quote journeys currently stored in provider operations.</p>
          </article>
          <article className="hero-mini-card">
            <strong>{payments.length}</strong>
            <p>Payment records currently stored in provider operations.</p>
          </article>
        </div>
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Quote lookup" subtitle="Inspect one transaction’s provider-side quote document.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={quoteLookup}
              onChange={(event) => setQuoteLookup(event.target.value)}
              placeholder="Enter transaction ID"
            />
            <button type="button" className="secondary-button" onClick={handleQuoteLookup}>
              Load quote
            </button>
            {selectedQuote ? (
              <div className="info-panel">
                <p><strong>Transaction:</strong> {selectedQuote.transaction_id}</p>
                <p><strong>Selected plan:</strong> {selectedQuote.selected_plan_id || "-"}</p>
                <p><strong>Quote items:</strong> {selectedQuote.items.length}</p>
                <p><strong>Updated:</strong> {formatDateTime(selectedQuote.updated_at)} IST</p>
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Payment lookup" subtitle="Inspect one payment reference from the provider side.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={paymentLookup}
              onChange={(event) => setPaymentLookup(event.target.value)}
              placeholder="Enter payment reference"
            />
            <button type="button" className="secondary-button" onClick={handlePaymentLookup}>
              Load payment
            </button>
            {selectedPayment ? (
              <div className="info-panel">
                <p><strong>Reference:</strong> {selectedPayment.payment_reference}</p>
                <p><strong>Status:</strong> {selectedPayment.payment_status}</p>
                <p><strong>Amount:</strong> Rs. {Number(selectedPayment.amount || 0).toLocaleString()}</p>
                <p><strong>Updated:</strong> {formatDateTime(selectedPayment.updated_at)} IST</p>
              </div>
            ) : null}
          </div>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Recent quote documents" subtitle="Latest provider-side quote journeys.">
          {quotes.length === 0 ? (
            <EmptyState
              title="No quotes loaded"
              description="Refresh operations to view provider-side quote documents."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Transaction</th>
                    <th>Selected plan</th>
                    <th>Quote items</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {quotes.map((quote) => (
                    <tr key={quote.transaction_id}>
                      <td>{quote.transaction_id}</td>
                      <td>{quote.selected_plan_id || "-"}</td>
                      <td>{quote.items.length}</td>
                      <td>{formatDateTime(quote.updated_at)} IST</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Recent payment records" subtitle="Latest provider-side payment activity.">
          {payments.length === 0 ? (
            <EmptyState
              title="No payments loaded"
              description="Refresh operations to view provider-side payment records."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Transaction</th>
                    <th>Status</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((payment) => (
                    <tr key={payment.payment_reference}>
                      <td>{payment.payment_reference}</td>
                      <td>{payment.transaction_id}</td>
                      <td>{payment.payment_status}</td>
                      <td>Rs. {Number(payment.amount || 0).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

export default OperationsPage;
