import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { useSession } from "../context/SessionContext";
import {
  createTicket,
  getLatestIncompleteJourney,
  getPaymentStatus,
  getPolicy,
  getTransaction,
  listUserPolicies,
  listUserTickets,
  listUserTransactions,
  updateUserTicket,
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
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

function CustomerDashboardPage() {
  const { session } = useSession();
  const [resumeJourney, setResumeJourney] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [transactionLookup, setTransactionLookup] = useState("");
  const [policyLookup, setPolicyLookup] = useState("");
  const [paymentLookup, setPaymentLookup] = useState("");
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [ticketForm, setTicketForm] = useState({
    transaction_id: "",
    issue_type: "",
    description: "",
  });
  const [ticketUpdate, setTicketUpdate] = useState({
    ticketId: "",
    description: "",
  });
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isTicketSubmitting, setIsTicketSubmitting] = useState(false);

  const openTickets = useMemo(
    () => tickets.filter((ticket) => !["RESOLVED", "CLOSED"].includes(ticket.ticket_status)),
    [tickets]
  );

  async function refreshCustomerData() {
    setIsRefreshing(true);
    setStatus({ type: "", message: "" });

    try {
      const results = await Promise.allSettled([
        getLatestIncompleteJourney(session.mobileNumber),
        listUserTransactions(session.userId),
        listUserPolicies(session.userId),
        listUserTickets(session.userId),
      ]);

      const [resumeResult, transactionsResult, policiesResult, ticketsResult] = results;

      if (resumeResult.status === "fulfilled") {
        setResumeJourney(resumeResult.value);
      } else {
        setResumeJourney(null);
      }

      if (transactionsResult.status === "fulfilled") {
        setTransactions(transactionsResult.value.items ?? []);
      }

      if (policiesResult.status === "fulfilled") {
        setPolicies(policiesResult.value.items ?? []);
      }

      if (ticketsResult.status === "fulfilled") {
        setTickets(ticketsResult.value.items ?? []);
      }

      setStatus({
        type: "success",
        message: "Customer account data refreshed successfully.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsRefreshing(false);
    }
  }

  async function handleTransactionLookup() {
    if (!transactionLookup) {
      return;
    }

    try {
      const response = await getTransaction(transactionLookup);
      setSelectedTransaction(response);
      setStatus({ type: "success", message: "Transaction loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  async function handlePolicyLookup() {
    if (!policyLookup) {
      return;
    }

    try {
      const response = await getPolicy(policyLookup);
      setSelectedPolicy(response);
      setStatus({ type: "success", message: "Policy loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  async function handlePaymentLookup() {
    if (!paymentLookup) {
      return;
    }

    try {
      const response = await getPaymentStatus(paymentLookup);
      setPaymentStatus(response);
      setStatus({ type: "success", message: "Payment status loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  async function handleCreateTicket(event) {
    event.preventDefault();
    setIsTicketSubmitting(true);
    setStatus({ type: "", message: "" });

    try {
      await createTicket(session.userId, ticketForm);
      setTicketForm({ transaction_id: "", issue_type: "", description: "" });
      await refreshCustomerData();
      setStatus({
        type: "success",
        message: "Support ticket created successfully.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsTicketSubmitting(false);
    }
  }

  async function handleUpdateTicket(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });

    try {
      await updateUserTicket(session.userId, ticketUpdate.ticketId, {
        description: ticketUpdate.description,
      });
      setTicketUpdate({ ticketId: "", description: "" });
      await refreshCustomerData();
      setStatus({
        type: "success",
        message: "Ticket updated successfully.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Returning customer workspace</p>
        <h2>Resume your insurance journey, track your records, and raise support issues.</h2>
        <p className="page-copy">
          This space follows the exact customer return flow from the role document:
          resume the latest journey, inspect transactions, access issued policies,
          download PDFs, and raise a ticket if something went wrong after payment.
        </p>
      </header>

      <div className="stats-grid">
        <StatCard
          label="Latest journey step"
          value={resumeJourney?.form_step || "-"}
          helper="Saved progress for the latest incomplete journey"
        />
        <StatCard
          label="Transactions"
          value={transactions.length}
          helper="All customer journey records linked to this mobile number"
        />
        <StatCard
          label="Issued policies"
          value={policies.length}
          helper="Policies created after successful payment verification"
        />
        <StatCard
          label="Open tickets"
          value={openTickets.length}
          helper="Support issues still waiting for resolution or closure"
        />
      </div>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard
        title="Journey control center"
        subtitle="Refresh your saved progress, transaction history, policy records, and ticket state in one action."
        actions={
          <button
            type="button"
            className="primary-button"
            onClick={refreshCustomerData}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh account data"}
          </button>
        }
      >
        {resumeJourney ? (
          <div className="highlight-strip">
            <div>
              <strong>Latest incomplete transaction:</strong> {resumeJourney.transaction_id}
            </div>
            <div>
              <strong>Current step:</strong> {resumeJourney.form_step}
            </div>
            <div>
              <strong>Status:</strong> {resumeJourney.current_status}
            </div>
            <Link
              to="/customer/app/quotes"
              state={{
                transactionId: resumeJourney.transaction_id,
                userId: session.userId,
                mobileNumber: session.mobileNumber,
              }}
              className="secondary-button"
            >
              Resume purchase flow
            </Link>
          </div>
        ) : (
          <EmptyState
            title="No incomplete journey right now"
            description="If a purchase is already complete, you can still use the tools below to inspect transactions, payments, policies, and tickets."
          />
        )}
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Transaction lookup" subtitle="Check one journey by transaction ID.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={transactionLookup}
              onChange={(event) => setTransactionLookup(event.target.value)}
              placeholder="Enter transaction ID"
            />
            <button type="button" className="secondary-button" onClick={handleTransactionLookup}>
              Load transaction
            </button>
            {selectedTransaction ? (
              <div className="info-panel">
                <p><strong>Status:</strong> {selectedTransaction.current_status}</p>
                <p><strong>Selected plan ID:</strong> {selectedTransaction.selected_plan_id || "-"}</p>
                <p><strong>Last active:</strong> {formatDateTime(selectedTransaction.last_active_at)}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Payment lookup" subtitle="Check payment status with the payment reference.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={paymentLookup}
              onChange={(event) => setPaymentLookup(event.target.value)}
              placeholder="Enter payment reference"
            />
            <button type="button" className="secondary-button" onClick={handlePaymentLookup}>
              Load payment status
            </button>
            {paymentStatus ? (
              <div className="info-panel">
                <p><strong>Status:</strong> {paymentStatus.payment_status}</p>
                <p><strong>Amount:</strong> {formatCurrency(paymentStatus.amount)}</p>
                <p><strong>Updated at:</strong> {formatDateTime(paymentStatus.updated_at)}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Policy lookup" subtitle="Fetch one policy and open its PDF if available.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={policyLookup}
              onChange={(event) => setPolicyLookup(event.target.value)}
              placeholder="Enter policy number"
            />
            <button type="button" className="secondary-button" onClick={handlePolicyLookup}>
              Load policy
            </button>
            {selectedPolicy ? (
              <div className="info-panel">
                <p><strong>Plan:</strong> {selectedPolicy.plan_name}</p>
                <p><strong>Company:</strong> {selectedPolicy.company_name}</p>
                <p><strong>Status:</strong> {selectedPolicy.policy_status}</p>
                <p><strong>Total premium:</strong> {formatCurrency(selectedPolicy.total_premium)}</p>
                {selectedPolicy.pdf_url ? (
                  <a
                    className="text-link"
                    href={`${import.meta.env.VITE_MAIN_API_BASE_URL ?? "http://127.0.0.1:8000"}${selectedPolicy.pdf_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open policy PDF →
                  </a>
                ) : (
                  <p><strong>PDF:</strong> Not available yet</p>
                )}
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Raise a support ticket" subtitle="Use this when payment succeeded but the journey result looks wrong.">
          <form className="stacked-fields" onSubmit={handleCreateTicket}>
            <input
              className="field-input"
              value={ticketForm.transaction_id}
              onChange={(event) =>
                setTicketForm((currentValue) => ({
                  ...currentValue,
                  transaction_id: event.target.value,
                }))
              }
              placeholder="Transaction ID linked to the issue"
              required
            />
            <input
              className="field-input"
              value={ticketForm.issue_type}
              onChange={(event) =>
                setTicketForm((currentValue) => ({
                  ...currentValue,
                  issue_type: event.target.value,
                }))
              }
              placeholder="Issue type, e.g. payment_issue"
              required
            />
            <textarea
              className="field-input field-textarea"
              rows="4"
              value={ticketForm.description}
              onChange={(event) =>
                setTicketForm((currentValue) => ({
                  ...currentValue,
                  description: event.target.value,
                }))
              }
              placeholder="Describe the issue clearly so the admin can investigate quickly."
              required
            />
            <button type="submit" className="primary-button" disabled={isTicketSubmitting}>
              {isTicketSubmitting ? "Submitting..." : "Create ticket"}
            </button>
          </form>
        </SectionCard>
      </div>

      <SectionCard title="My tickets" subtitle="Update open tickets and watch for admin responses.">
        {tickets.length === 0 ? (
          <EmptyState
            title="No tickets raised yet"
            description="If you face a post-purchase issue, create a ticket and it will become visible to the customer-app admin."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Transaction</th>
                  <th>Status</th>
                  <th>Issue</th>
                  <th>Admin response</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.ticket_id}>
                    <td>{ticket.ticket_id}</td>
                    <td>{ticket.transaction_id}</td>
                    <td>{ticket.ticket_status}</td>
                    <td>{ticket.issue_type}</td>
                    <td>{ticket.admin_response || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <form className="inline-form" onSubmit={handleUpdateTicket}>
          <input
            className="field-input"
            value={ticketUpdate.ticketId}
            onChange={(event) =>
              setTicketUpdate((currentValue) => ({
                ...currentValue,
                ticketId: event.target.value,
              }))
            }
            placeholder="Ticket ID to update"
          />
          <input
            className="field-input"
            value={ticketUpdate.description}
            onChange={(event) =>
              setTicketUpdate((currentValue) => ({
                ...currentValue,
                description: event.target.value,
              }))
            }
            placeholder="Add more context to your existing open ticket"
          />
          <button type="submit" className="secondary-button">
            Update open ticket
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Transaction history" subtitle="All journeys linked to this customer account.">
        {transactions.length === 0 ? (
          <EmptyState
            title="No transactions loaded"
            description="Use the refresh button above to load your transaction history from the backend."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Transaction</th>
                  <th>Status</th>
                  <th>Selected plan</th>
                  <th>Last active</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction) => (
                  <tr key={transaction.transaction_id}>
                    <td>{transaction.transaction_id}</td>
                    <td>{transaction.current_status}</td>
                    <td>{transaction.selected_plan_id || "-"}</td>
                    <td>{formatDateTime(transaction.last_active_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Issued policies" subtitle="Every policy issued for this customer account.">
        {policies.length === 0 ? (
          <EmptyState
            title="No issued policies loaded"
            description="Once payment is verified and policy issuance completes, your policy will appear here."
          />
        ) : (
          <div className="card-grid">
            {policies.map((policy) => (
              <article key={policy.policy_number} className="mini-card">
                <p className="eyebrow-text">{policy.company_name}</p>
                <h4>{policy.plan_name}</h4>
                <p><strong>Policy:</strong> {policy.policy_number}</p>
                <p><strong>Status:</strong> {policy.policy_status}</p>
                <p><strong>Total:</strong> {formatCurrency(policy.total_premium)}</p>
                {policy.pdf_url ? (
                  <a
                    className="text-link"
                    href={`${import.meta.env.VITE_MAIN_API_BASE_URL ?? "http://127.0.0.1:8000"}${policy.pdf_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View PDF →
                  </a>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default CustomerDashboardPage;
