import { useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import {
  listAdminCompletedJourneys,
  listAdminPendingForms,
  listAdminPolicies,
  listAdminTickets,
  listAdminTransactions,
  listAdminUsers,
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

function AdminDashboardPage() {
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [pendingForms, setPendingForms] = useState([]);
  const [completedJourneys, setCompletedJourneys] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(false);

  const metrics = useMemo(
    () => [
      {
        label: "Customers",
        value: users.length,
        helper: "All customer records accessible to the customer-app admin",
      },
      {
        label: "Transactions",
        value: transactions.length,
        helper: "All customer-side journey records",
      },
      {
        label: "Pending forms",
        value: pendingForms.length,
        helper: "Incomplete journeys that may need customer follow-up",
      },
      {
        label: "Tickets",
        value: tickets.length,
        helper: "Raised customer support issues visible to the admin",
      },
    ],
    [pendingForms.length, tickets.length, transactions.length, users.length]
  );

  async function loadOverview() {
    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const [
        userResponse,
        transactionResponse,
        pendingResponse,
        completedResponse,
        policyResponse,
        ticketResponse,
      ] = await Promise.all([
        listAdminUsers(),
        listAdminTransactions(),
        listAdminPendingForms(),
        listAdminCompletedJourneys(),
        listAdminPolicies(),
        listAdminTickets(),
      ]);

      setUsers(userResponse.items ?? []);
      setTransactions(transactionResponse.items ?? []);
      setPendingForms(pendingResponse.items ?? []);
      setCompletedJourneys(completedResponse.items ?? []);
      setPolicies(policyResponse.items ?? []);
      setTickets(ticketResponse.items ?? []);
      setStatus({
        type: "success",
        message: "Admin operations data loaded successfully.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Customer-app admin operations</p>
        <h2>Monitor customers, transactions, pending forms, issued policies, and support signals.</h2>
        <p className="page-copy">
          This dashboard mirrors the admin responsibilities defined in `user_role_flow.md`:
          operational visibility over customers, transactions, incomplete journeys,
          completed purchases, issued policies, and raised support issues.
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
        title="Load admin overview"
        subtitle="Fetch all high-level operational datasets from the customer-side backend."
        actions={
          <button
            type="button"
            className="primary-button"
            onClick={loadOverview}
            disabled={isLoading}
          >
            {isLoading ? "Loading..." : "Refresh admin overview"}
          </button>
        }
      >
        <div className="banner-grid">
          <article className="hero-mini-card">
            <strong>Customer records</strong>
            <p>Track who has entered the system and which accounts are active.</p>
          </article>
          <article className="hero-mini-card">
            <strong>Pending forms</strong>
            <p>Watch incomplete journeys and identify customers stuck mid-flow.</p>
          </article>
          <article className="hero-mini-card">
            <strong>Completed journeys</strong>
            <p>Confirm which transactions successfully reached purchase completion.</p>
          </article>
        </div>
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Customer records" subtitle="All customer accounts visible to the admin dashboard.">
          {users.length === 0 ? (
            <EmptyState
              title="No customers loaded"
              description="Use refresh to load customer records and monitor the user base."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Mobile</th>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {users.slice(0, 8).map((user) => (
                    <tr key={user.id}>
                      <td>{`${user.first_name} ${user.last_name}`.trim() || "-"}</td>
                      <td>{user.mobile_number}</td>
                      <td>{user.user_role}</td>
                      <td>{user.is_active ? "Active" : "Inactive"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Pending forms" subtitle="Journeys that did not reach policy purchase yet.">
          {pendingForms.length === 0 ? (
            <EmptyState
              title="No pending forms loaded"
              description="When customers stop mid-journey, their transactions will appear here."
            />
          ) : (
            <div className="list-stack">
              {pendingForms.slice(0, 6).map((transaction) => (
                <article key={transaction.transaction_id} className="list-card">
                  <div>
                    <h4>{transaction.transaction_id}</h4>
                    <p>User: {transaction.user_id}</p>
                  </div>
                  <span className="info-chip">{transaction.current_status}</span>
                </article>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Completed journeys" subtitle="Transactions that reached the purchased state.">
          {completedJourneys.length === 0 ? (
            <EmptyState
              title="No completed journeys loaded"
              description="Purchased journeys will appear here after successful payment verification and policy issuance."
            />
          ) : (
            <div className="list-stack">
              {completedJourneys.slice(0, 6).map((transaction) => (
                <article key={transaction.transaction_id} className="list-card">
                  <div>
                    <h4>{transaction.transaction_id}</h4>
                    <p>Selected plan: {transaction.selected_plan_id || "-"}</p>
                  </div>
                  <span className="info-chip">{transaction.current_status}</span>
                </article>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Support signals" subtitle="Recent tickets raised by customers after purchase issues.">
          {tickets.length === 0 ? (
            <EmptyState
              title="No tickets loaded"
              description="Customer-raised post-purchase issues will appear here once the admin refreshes data."
            />
          ) : (
            <div className="list-stack">
              {tickets.slice(0, 6).map((ticket) => (
                <article key={ticket.ticket_id} className="list-card">
                  <div>
                    <h4>{ticket.ticket_id}</h4>
                    <p>{ticket.issue_type} · {ticket.transaction_id}</p>
                  </div>
                  <span className="info-chip">{ticket.ticket_status}</span>
                </article>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Issued policies snapshot" subtitle="Latest policy records available to the customer-app admin.">
        {policies.length === 0 ? (
          <EmptyState
            title="No policies loaded"
            description="Issued policies will appear here after the admin overview refresh."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Policy</th>
                  <th>Customer</th>
                  <th>Company</th>
                  <th>Status</th>
                  <th>Issued at</th>
                </tr>
              </thead>
              <tbody>
                {policies.slice(0, 10).map((policy) => (
                  <tr key={policy.policy_number}>
                    <td>{policy.policy_number}</td>
                    <td>{policy.user_id}</td>
                    <td>{policy.company_name}</td>
                    <td>{policy.policy_status}</td>
                    <td>{formatDateTime(policy.issued_at)}</td>
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

export default AdminDashboardPage;
