import { useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { useSession } from "../context/SessionContext";
import {
  getLatestIncompleteJourney,
  getPaymentStatus,
  getTransaction,
  listUserPolicies,
  listUserTransactions,
} from "../lib/api";

function CustomerDashboardPage() {
  const { session } = useSession();
  const [resumeJourney, setResumeJourney] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [lookupState, setLookupState] = useState({ transactionId: "", paymentReference: "" });
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(false);

  const loadCustomerData = async () => {
    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const [resumeResponse, transactionResponse, policyResponse] = await Promise.all([
        getLatestIncompleteJourney(session.mobileNumber),
        listUserTransactions(session.userId),
        listUserPolicies(session.userId),
      ]);

      setResumeJourney(resumeResponse);
      setTransactions(transactionResponse.items ?? []);
      setPolicies(policyResponse.items ?? []);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const lookupTransaction = async () => {
    if (!lookupState.transactionId) {
      return;
    }

    try {
      const response = await getTransaction(lookupState.transactionId);
      setSelectedTransaction(response);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const lookupPayment = async () => {
    if (!lookupState.paymentReference) {
      return;
    }

    try {
      const response = await getPaymentStatus(lookupState.paymentReference);
      setPaymentStatus(response);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Customer dashboard</p>
        <h2>Track your health insurance journey.</h2>
      </header>

      <div className="stats-grid">
        <StatCard label="Transactions" value={transactions.length} helper="Saved or completed journey records" />
        <StatCard label="Policies" value={policies.length} helper="Issued policy documents linked to your account" />
        <StatCard label="Resume step" value={resumeJourney?.form_step || "-"} helper="Latest saved form progress" />
      </div>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard
        title="Load my account data"
        subtitle="Fetch resume journey, transaction history, and issued policies."
        actions={
          <button type="button" className="primary-button" onClick={loadCustomerData} disabled={isLoading}>
            {isLoading ? "Loading..." : "Refresh data"}
          </button>
        }
      >
        {resumeJourney ? (
          <div className="detail-strip">
            <strong>Latest incomplete transaction:</strong> {resumeJourney.transaction_id} | step: {resumeJourney.form_step} | status: {resumeJourney.current_status}
          </div>
        ) : (
          <EmptyState
            title="No resume data loaded yet"
            description="Use refresh to fetch the latest journey, transactions, and policies for this mobile number."
          />
        )}
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Transaction quick lookup" subtitle="Inspect one transaction by ID.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={lookupState.transactionId}
              onChange={(event) =>
                setLookupState((currentState) => ({
                  ...currentState,
                  transactionId: event.target.value,
                }))
              }
              placeholder="Enter transaction ID"
            />
            <button type="button" className="secondary-button" onClick={lookupTransaction}>
              Fetch transaction
            </button>
            {selectedTransaction ? (
              <div className="info-panel">
                <p><strong>Status:</strong> {selectedTransaction.current_status}</p>
                <p><strong>Selected plan:</strong> {selectedTransaction.selected_plan_id || "-"}</p>
                <p><strong>Last active:</strong> {selectedTransaction.last_active_at}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Payment quick lookup" subtitle="Check payment status by reference.">
          <div className="stacked-fields">
            <input
              className="field-input"
              value={lookupState.paymentReference}
              onChange={(event) =>
                setLookupState((currentState) => ({
                  ...currentState,
                  paymentReference: event.target.value,
                }))
              }
              placeholder="Enter payment reference"
            />
            <button type="button" className="secondary-button" onClick={lookupPayment}>
              Fetch payment
            </button>
            {paymentStatus ? (
              <div className="info-panel">
                <p><strong>Status:</strong> {paymentStatus.payment_status}</p>
                <p><strong>Amount:</strong> Rs. {paymentStatus.amount}</p>
                <p><strong>Gateway URL:</strong> {paymentStatus.gateway_url || "-"}</p>
              </div>
            ) : null}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Issued policies" subtitle="Policies linked to this customer account.">
        {policies.length === 0 ? (
          <EmptyState
            title="No policies loaded"
            description="After payment and policy issuance, policy records will appear here."
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

export default CustomerDashboardPage;
