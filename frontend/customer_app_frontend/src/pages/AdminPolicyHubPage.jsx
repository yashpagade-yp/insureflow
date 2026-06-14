import { useState } from "react";

import SectionCard from "../components/SectionCard";
import { attachPolicyPdf, getPolicy, issuePolicy } from "../lib/api";

const initialIssueState = {
  transaction_id: "",
  user_id: "",
  company_name: "",
  plan_name: "",
  coverage_amount: "",
  base_premium: "",
  add_on_name: "",
  add_on_price: "",
  add_on_total: "",
  tax_amount: "",
  total_premium: "",
  payment_reference: "",
  pdf_url: "",
  duration_years: "1",
};

function AdminPolicyHubPage() {
  const [issueState, setIssueState] = useState(initialIssueState);
  const [policyLookup, setPolicyLookup] = useState("");
  const [pdfAttachState, setPdfAttachState] = useState({ policyNumber: "", pdfUrl: "" });
  const [policyDetail, setPolicyDetail] = useState(null);
  const [status, setStatus] = useState({ type: "", message: "" });

  const updateIssueField = (event) => {
    const { name, value } = event.target;
    setIssueState((currentState) => ({ ...currentState, [name]: value }));
  };

  const submitPolicyIssue = async (event) => {
    event.preventDefault();

    try {
      const addOns = issueState.add_on_name
        ? [{ name: issueState.add_on_name, price: Number(issueState.add_on_price || 0) }]
        : [];

      const response = await issuePolicy({
        transaction_id: issueState.transaction_id,
        user_id: issueState.user_id,
        company_name: issueState.company_name,
        plan_name: issueState.plan_name,
        coverage_amount: Number(issueState.coverage_amount),
        base_premium: Number(issueState.base_premium),
        add_ons: addOns,
        add_on_total: Number(issueState.add_on_total || 0),
        tax_amount: Number(issueState.tax_amount || 0),
        total_premium: Number(issueState.total_premium || 0),
        payment_reference: issueState.payment_reference,
        pdf_url: issueState.pdf_url || null,
        duration_years: Number(issueState.duration_years || 1),
      });

      setPolicyDetail(response);
      setStatus({
        type: "success",
        message: `Policy issued successfully: ${response.policy_number}`,
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const lookupPolicy = async () => {
    try {
      const response = await getPolicy(policyLookup);
      setPolicyDetail(response);
      setStatus({ type: "success", message: "Policy fetched successfully." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const attachPdf = async () => {
    try {
      const response = await attachPolicyPdf(pdfAttachState.policyNumber, {
        pdf_url: pdfAttachState.pdfUrl,
      });
      setStatus({
        type: "success",
        message: `PDF attached for policy ${response.policy_number}.`,
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Policy issuance hub</p>
        <h2>Issue policies, fetch policy records, and attach policy PDFs.</h2>
      </header>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <div className="content-grid">
        <SectionCard title="Issue policy" subtitle="Manual admin policy issuance flow.">
          <form className="form-grid" onSubmit={submitPolicyIssue}>
            <label className="field-label"><span>Transaction ID</span><input className="field-input" name="transaction_id" value={issueState.transaction_id} onChange={updateIssueField} /></label>
            <label className="field-label"><span>User ID</span><input className="field-input" name="user_id" value={issueState.user_id} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Company name</span><input className="field-input" name="company_name" value={issueState.company_name} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Plan name</span><input className="field-input" name="plan_name" value={issueState.plan_name} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Coverage amount</span><input className="field-input" type="number" min="0" name="coverage_amount" value={issueState.coverage_amount} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Base premium</span><input className="field-input" type="number" min="0" name="base_premium" value={issueState.base_premium} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Add-on name</span><input className="field-input" name="add_on_name" value={issueState.add_on_name} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Add-on price</span><input className="field-input" type="number" min="0" name="add_on_price" value={issueState.add_on_price} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Add-on total</span><input className="field-input" type="number" min="0" name="add_on_total" value={issueState.add_on_total} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Tax amount</span><input className="field-input" type="number" min="0" name="tax_amount" value={issueState.tax_amount} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Total premium</span><input className="field-input" type="number" min="0" name="total_premium" value={issueState.total_premium} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Payment reference</span><input className="field-input" name="payment_reference" value={issueState.payment_reference} onChange={updateIssueField} /></label>
            <label className="field-label"><span>PDF URL</span><input className="field-input" name="pdf_url" value={issueState.pdf_url} onChange={updateIssueField} /></label>
            <label className="field-label"><span>Duration years</span><input className="field-input" type="number" min="1" name="duration_years" value={issueState.duration_years} onChange={updateIssueField} /></label>
            <div className="form-actions form-span-full">
              <button type="submit" className="primary-button">Issue policy</button>
            </div>
          </form>
        </SectionCard>

        <SectionCard title="Policy tools" subtitle="Fetch one policy and attach a PDF URL.">
          <div className="stacked-fields">
            <input className="field-input" value={policyLookup} onChange={(event) => setPolicyLookup(event.target.value)} placeholder="Enter policy number" />
            <button type="button" className="secondary-button" onClick={lookupPolicy}>Fetch policy</button>

            <input
              className="field-input"
              value={pdfAttachState.policyNumber}
              onChange={(event) =>
                setPdfAttachState((currentState) => ({
                  ...currentState,
                  policyNumber: event.target.value,
                }))
              }
              placeholder="Policy number for PDF attach"
            />
            <input
              className="field-input"
              value={pdfAttachState.pdfUrl}
              onChange={(event) =>
                setPdfAttachState((currentState) => ({
                  ...currentState,
                  pdfUrl: event.target.value,
                }))
              }
              placeholder="https://example.com/policy.pdf"
            />
            <button type="button" className="secondary-button" onClick={attachPdf}>
              Attach PDF
            </button>
          </div>
        </SectionCard>
      </div>

      {policyDetail ? (
        <SectionCard title="Policy detail" subtitle="Latest fetched or issued policy snapshot.">
          <div className="info-panel">
            <p><strong>Policy number:</strong> {policyDetail.policy_number}</p>
            <p><strong>Plan:</strong> {policyDetail.plan_name}</p>
            <p><strong>Company:</strong> {policyDetail.company_name}</p>
            <p><strong>Status:</strong> {policyDetail.policy_status}</p>
            <p><strong>Total premium:</strong> Rs. {policyDetail.total_premium}</p>
            <p><strong>PDF URL:</strong> {policyDetail.pdf_url || "-"}</p>
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}

export default AdminPolicyHubPage;
