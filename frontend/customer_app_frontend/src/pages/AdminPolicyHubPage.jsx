import { useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import {
  getPolicy,
  listAdminPolicies,
  listAdminTickets,
  respondToAdminTicket,
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

function AdminPolicyHubPage() {
  const [policyLookup, setPolicyLookup] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [resolutionForm, setResolutionForm] = useState({
    ticketId: "",
    ticket_status: "RESOLVED",
    admin_response: "",
  });
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(false);

  const activeTickets = useMemo(
    () =>
      tickets.filter(
        (ticket) => !["RESOLVED", "CLOSED"].includes(ticket.ticket_status)
      ),
    [tickets]
  );

  async function loadOpsData() {
    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const [policyResponse, ticketResponse] = await Promise.all([
        listAdminPolicies(),
        listAdminTickets(),
      ]);
      setPolicies(policyResponse.items ?? []);
      setTickets(ticketResponse.items ?? []);
      setStatus({
        type: "success",
        message: "Policies and ticket queues loaded successfully.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePolicyLookup() {
    if (!policyLookup) {
      return;
    }

    try {
      const response = await getPolicy(policyLookup);
      setSelectedPolicy(response);
      setStatus({ type: "success", message: "Policy loaded successfully." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  }

  async function handleResolveTicket(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });

    try {
      await respondToAdminTicket(resolutionForm.ticketId, {
        ticket_status: resolutionForm.ticket_status,
        admin_response: resolutionForm.admin_response,
      });
      setResolutionForm({
        ticketId: "",
        ticket_status: "RESOLVED",
        admin_response: "",
      });
      await loadOpsData();
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
        <p className="eyebrow-text">Admin policy and ticket center</p>
        <h2>Investigate policy outcomes, review support tickets, and close customer issues.</h2>
        <p className="page-copy">
          This page covers the customer-app admin’s post-purchase responsibility:
          inspect issued policies, check generated PDFs, review support tickets,
          respond to customers, and move tickets to resolved or closed.
        </p>
      </header>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard
        title="Policy and ticket queue"
        subtitle="Refresh the latest post-purchase operations data for admin review."
        actions={
          <button
            type="button"
            className="primary-button"
            onClick={loadOpsData}
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh policy & ticket data"}
          </button>
        }
      >
        <div className="banner-grid">
          <article className="hero-mini-card">
            <strong>{policies.length}</strong>
            <p>Policies currently visible to the admin operations team.</p>
          </article>
          <article className="hero-mini-card">
            <strong>{tickets.length}</strong>
            <p>Total support tickets loaded from the customer-side backend.</p>
          </article>
          <article className="hero-mini-card">
            <strong>{activeTickets.length}</strong>
            <p>Tickets still requiring admin action or final customer closure.</p>
          </article>
        </div>
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Policy lookup" subtitle="Inspect one issued policy in detail.">
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
                <p><strong>Payment reference:</strong> {selectedPolicy.payment_reference || "-"}</p>
                <p><strong>PDF URL:</strong> {selectedPolicy.pdf_url || "-"}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Resolve customer ticket" subtitle="Update one ticket after investigating the issue.">
          <form className="stacked-fields" onSubmit={handleResolveTicket}>
            <input
              className="field-input"
              value={resolutionForm.ticketId}
              onChange={(event) =>
                setResolutionForm((currentValue) => ({
                  ...currentValue,
                  ticketId: event.target.value,
                }))
              }
              placeholder="Ticket ID"
              required
            />
            <select
              className="field-input"
              value={resolutionForm.ticket_status}
              onChange={(event) =>
                setResolutionForm((currentValue) => ({
                  ...currentValue,
                  ticket_status: event.target.value,
                }))
              }
            >
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
            <textarea
              className="field-input field-textarea"
              rows="4"
              value={resolutionForm.admin_response}
              onChange={(event) =>
                setResolutionForm((currentValue) => ({
                  ...currentValue,
                  admin_response: event.target.value,
                }))
              }
              placeholder="Write the admin response or resolution update."
              required
            />
            <button type="submit" className="primary-button">
              Update ticket
            </button>
          </form>
        </SectionCard>
      </div>

      <SectionCard title="Open tickets first" subtitle="Prioritize unresolved or active customer issues.">
        {activeTickets.length === 0 ? (
          <EmptyState
            title="No active tickets loaded"
            description="Once support tickets are refreshed, active items that need admin handling will appear here."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Transaction</th>
                  <th>Status</th>
                  <th>Issue type</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {activeTickets.map((ticket) => (
                  <tr key={ticket.ticket_id}>
                    <td>{ticket.ticket_id}</td>
                    <td>{ticket.transaction_id}</td>
                    <td>{ticket.ticket_status}</td>
                    <td>{ticket.issue_type}</td>
                    <td>{formatDateTime(ticket.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Issued policy register" subtitle="Latest policy records available for customer-side operations.">
        {policies.length === 0 ? (
          <EmptyState
            title="No policies loaded"
            description="Refresh the policy queue to view the latest issued policy records."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Policy</th>
                  <th>Plan</th>
                  <th>Company</th>
                  <th>Status</th>
                  <th>PDF</th>
                </tr>
              </thead>
              <tbody>
                {policies.slice(0, 12).map((policy) => (
                  <tr key={policy.policy_number}>
                    <td>{policy.policy_number}</td>
                    <td>{policy.plan_name}</td>
                    <td>{policy.company_name}</td>
                    <td>{policy.policy_status}</td>
                    <td>{policy.pdf_url ? "Available" : "Pending"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default AdminPolicyHubPage;
