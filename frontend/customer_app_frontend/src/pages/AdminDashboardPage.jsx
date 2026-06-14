import { useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { getTransaction, getUserProfile, listUserPolicies, listUserTransactions } from "../lib/api";

function AdminDashboardPage() {
  const [userId, setUserId] = useState("");
  const [transactionId, setTransactionId] = useState("");
  const [userProfile, setUserProfile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [transactionDetail, setTransactionDetail] = useState(null);
  const [status, setStatus] = useState({ type: "", message: "" });

  const fetchUserBundle = async () => {
    try {
      const [profileResponse, transactionsResponse, policiesResponse] = await Promise.all([
        getUserProfile(userId),
        listUserTransactions(userId),
        listUserPolicies(userId),
      ]);

      setUserProfile(profileResponse);
      setTransactions(transactionsResponse.items ?? []);
      setPolicies(policiesResponse.items ?? []);
      setStatus({ type: "success", message: "Admin customer bundle loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const fetchTransaction = async () => {
    try {
      const response = await getTransaction(transactionId);
      setTransactionDetail(response);
      setStatus({ type: "success", message: "Transaction loaded." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Admin operations dashboard</p>
        <h2>Inspect customer progress and lookup transaction records.</h2>
      </header>

      <div className="stats-grid">
        <StatCard label="Loaded transactions" value={transactions.length} helper="Transactions fetched for current user lookup" />
        <StatCard label="Loaded policies" value={policies.length} helper="Issued policies fetched for current user lookup" />
        <StatCard label="Current user" value={userProfile?.first_name || "-"} helper={userProfile?.mobile_number || "No user loaded yet"} />
      </div>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <div className="content-grid">
        <SectionCard title="User bundle lookup" subtitle="Fetch profile, transactions, and policies by user ID.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="Enter user ID"
            />
            <button type="button" className="primary-button" onClick={fetchUserBundle}>
              Load user bundle
            </button>
            {userProfile ? (
              <div className="info-panel">
                <p><strong>Name:</strong> {userProfile.first_name} {userProfile.last_name}</p>
                <p><strong>Role:</strong> {userProfile.user_role}</p>
                <p><strong>Mobile:</strong> {userProfile.mobile_number}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Transaction lookup" subtitle="Fetch one transaction by transaction ID.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={transactionId}
              onChange={(event) => setTransactionId(event.target.value)}
              placeholder="Enter transaction ID"
            />
            <button type="button" className="primary-button" onClick={fetchTransaction}>
              Load transaction
            </button>
            {transactionDetail ? (
              <div className="info-panel">
                <p><strong>Status:</strong> {transactionDetail.current_status}</p>
                <p><strong>User ID:</strong> {transactionDetail.user_id}</p>
                <p><strong>Selected plan:</strong> {transactionDetail.selected_plan_id || "-"}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="User policies" subtitle="Policy records from the current admin lookup.">
        {policies.length === 0 ? (
          <EmptyState
            title="No policies loaded"
            description="Fetch a user bundle first to see issued policies."
          />
        ) : (
          <div className="card-grid">
            {policies.map((policy) => (
              <article key={policy.policy_number} className="mini-card">
                <h4>{policy.plan_name}</h4>
                <p>{policy.company_name}</p>
                <p>Policy no: {policy.policy_number}</p>
                <p>Status: {policy.policy_status}</p>
              </article>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default AdminDashboardPage;
