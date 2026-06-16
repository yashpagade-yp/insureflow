import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { useSession } from "../context/SessionContext";
import {
  createTicket,
  getLatestIncompleteJourney,
  getPolicy,
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
  const [policyLookup, setPolicyLookup] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [ticketForm, setTicketForm] = useState({
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

  const latestSupportTransactionId = useMemo(
    () =>
      resumeJourney?.transaction_id ||
      policies[0]?.transaction_id ||
      transactions[0]?.transaction_id ||
      "",
    [policies, resumeJourney, transactions]
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

      setResumeJourney(resumeResult.status === "fulfilled" ? resumeResult.value : null);

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

  async function handleCreateTicket(event) {
    event.preventDefault();
    setIsTicketSubmitting(true);
    setStatus({ type: "", message: "" });

    try {
      if (!latestSupportTransactionId) {
        throw new Error("No active or recent policy journey is available for ticket creation right now.");
      }

      await createTicket(session.userId, {
        transaction_id: latestSupportTransactionId,
        issue_type: ticketForm.issue_type,
        description: ticketForm.description,
      });
      setTicketForm({ issue_type: "", description: "" });
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
        <p className="eyebrow-text">My insurance account</p>
        <h2>Resume your journey, access issued policies, and get support when you need it.</h2>
        <p className="page-copy">
          This customer dashboard is focused only on your active insurance journey,
          completed policy purchases, and support needs.
        </p>
      </header>

      <div className="stats-grid">
        <StatCard
          label="Incomplete journey"
          value={resumeJourney ? "Available" : "None"}
          helper="Resume your purchase from the latest saved step"
        />
        <StatCard
          label="Issued policies"
          value={policies.length}
          helper="Policies created after successful payment"
        />
        <StatCard
          label="Open tickets"
          value={openTickets.length}
          helper="Support requests still waiting for resolution"
        />
      </div>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard
        title="My account overview"
        subtitle="Refresh your latest purchase progress, policy records, and ticket status in one action."
        actions={
          <button
            type="button"
            className="primary-button"
            onClick={refreshCustomerData}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh account"}
          </button>
        }
      >
        {resumeJourney ? (
          <div className="highlight-strip">
            <div>
              <strong>Resume journey</strong>
              <p className="muted-copy">
                Continue from your latest saved step: {resumeJourney.form_step || "Saved progress"}
              </p>
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
              Resume policy journey
            </Link>
          </div>
        ) : (
          <EmptyState
            title="No incomplete journey"
            description="You do not have a saved unfinished purchase right now. You can still view issued policies and raise support tickets below."
          />
        )}
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Issued policies" subtitle="Policies that are already purchased and available in your account.">
          <div className="stacked-fields">
            <div className="inline-form">
              <input
                className="field-input"
                value={policyLookup}
                onChange={(event) => setPolicyLookup(event.target.value)}
                placeholder="Enter policy number to find one policy"
              />
              <button type="button" className="secondary-button" onClick={handlePolicyLookup}>
                Find policy
              </button>
            </div>

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

            {policies.length === 0 ? (
              <EmptyState
                title="No issued policies yet"
                description="Once your payment is verified and policy issuance is complete, your purchased policy will appear here."
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
                    <p><strong>Issued:</strong> {formatDateTime(policy.issued_at)}</p>
                    {policy.pdf_url ? (
                      <a
                        className="text-link"
                        href={`${import.meta.env.VITE_MAIN_API_BASE_URL ?? "http://127.0.0.1:8000"}${policy.pdf_url}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        View policy PDF →
                      </a>
                    ) : null}
                  </article>
                ))}
              </div>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Raise a support ticket" subtitle="Tell us the issue type and describe what went wrong.">
          <form className="stacked-fields" onSubmit={handleCreateTicket}>
            <input
              className="field-input"
              value={ticketForm.issue_type}
              onChange={(event) =>
                setTicketForm((currentValue) => ({
                  ...currentValue,
                  issue_type: event.target.value,
                }))
              }
              placeholder="Issue type, for example: payment_issue"
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
              placeholder="Describe the issue clearly so support can investigate it quickly."
              required
            />
            <button type="submit" className="primary-button" disabled={isTicketSubmitting}>
              {isTicketSubmitting ? "Submitting..." : "Create ticket"}
            </button>
          </form>
        </SectionCard>
      </div>

      <SectionCard title="My tickets" subtitle="Track existing tickets and add more details to an open request if needed.">
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
                  <th>Status</th>
                  <th>Issue</th>
                  <th>Admin response</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.ticket_id}>
                    <td>{ticket.ticket_id}</td>
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
            placeholder="Add more context to an open ticket"
          />
          <button type="submit" className="secondary-button">
            Update ticket
          </button>
        </form>
      </SectionCard>
    </div>
  );
}

export default CustomerDashboardPage;
