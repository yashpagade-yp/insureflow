import { useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import { useSession } from "../context/SessionContext";
import {
  createPayment,
  getQuotes,
  selectAddOns,
  selectPlan,
  sendPaymentOtp,
  verifyPaymentOtp,
} from "../lib/api";

function QuotesPage() {
  const { session } = useSession();
  const [transactionId, setTransactionId] = useState("");
  const [quoteData, setQuoteData] = useState(null);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [selectedAddOns, setSelectedAddOns] = useState([]);
  const [paymentState, setPaymentState] = useState({ amount: "", paymentReference: "", otp: "" });
  const [status, setStatus] = useState({ type: "", message: "" });

  const loadQuotes = async () => {
    try {
      const response = await getQuotes(transactionId);
      setQuoteData(response);
      setSelectedPlanId(response.selected_plan_id || response.items?.[0]?.plan_id || "");
      setStatus({ type: "success", message: "Quotes loaded successfully." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const toggleAddOn = (addOn) => {
    setSelectedAddOns((currentState) => {
      const exists = currentState.some((item) => item.name === addOn.name);
      if (exists) {
        return currentState.filter((item) => item.name !== addOn.name);
      }
      return [...currentState, { name: addOn.name, price: addOn.price }];
    });
  };

  const savePlanSelection = async () => {
    try {
      await selectPlan({ transaction_id: transactionId, selected_plan_id: selectedPlanId });
      setStatus({ type: "success", message: "Plan selection saved." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const saveAddOnSelection = async () => {
    try {
      await selectAddOns({
        transaction_id: transactionId,
        selected_plan_id: selectedPlanId,
        selected_add_ons: selectedAddOns,
      });
      setStatus({ type: "success", message: "Add-ons saved." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const createCustomerPayment = async () => {
    try {
      const response = await createPayment({
        transaction_id: transactionId,
        user_id: session.userId,
        amount: Number(paymentState.amount),
      });

      setPaymentState((currentState) => ({
        ...currentState,
        paymentReference: response.payment_reference,
      }));
      setStatus({ type: "success", message: "Payment record created." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const sendOtpForPayment = async () => {
    try {
      await sendPaymentOtp(paymentState.paymentReference);
      setStatus({ type: "success", message: "Payment OTP sent." });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const verifyOtpForPayment = async () => {
    try {
      const response = await verifyPaymentOtp({
        transaction_id: transactionId,
        payment_reference: paymentState.paymentReference,
        otp: paymentState.otp,
      });
      setStatus({
        type: "success",
        message: response.policy_number
          ? `Payment verified. Policy issued: ${response.policy_number}`
          : response.message,
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    }
  };

  const selectedPlan =
    quoteData?.items?.find((item) => item.plan_id === selectedPlanId) || null;

  return (
    <div className="page-stack">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Quotes and payment</p>
        <h2>Move from quote selection to payment verification.</h2>
      </header>

      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <SectionCard title="Load quotes" subtitle="Enter a transaction ID to fetch provider quotes.">
        <div className="inline-form">
          <input
            className="field-input"
            value={transactionId}
            onChange={(event) => setTransactionId(event.target.value)}
            placeholder="Enter transaction ID"
          />
          <button type="button" className="primary-button" onClick={loadQuotes}>
            Fetch quotes
          </button>
        </div>
      </SectionCard>

      {!quoteData ? (
        <EmptyState
          title="No quotes loaded yet"
          description="Fetch a transaction first to view plans, add-ons, and payment steps."
        />
      ) : (
        <>
          <SectionCard title="Available plans" subtitle="Select one plan for this transaction.">
            <div className="card-grid">
              {quoteData.items.map((item) => (
                <article
                  key={item.plan_id}
                  className={item.plan_id === selectedPlanId ? "mini-card mini-card-selected" : "mini-card"}
                >
                  <h4>{item.plan_name}</h4>
                  <p>{item.company_name}</p>
                  <p>Coverage: Rs. {item.coverage_amount}</p>
                  <p>Total premium: Rs. {item.total_premium}</p>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setSelectedPlanId(item.plan_id)}
                  >
                    Choose this plan
                  </button>
                </article>
              ))}
            </div>
            <button type="button" className="primary-button" onClick={savePlanSelection}>
              Save selected plan
            </button>
          </SectionCard>

          <SectionCard title="Add-ons" subtitle="Select add-ons for the chosen plan if available.">
            {!selectedPlan || selectedPlan.available_add_ons.length === 0 ? (
              <EmptyState
                title="No add-ons available"
                description="The chosen plan currently has no optional add-ons."
              />
            ) : (
              <div className="stacked-fields">
                {selectedPlan.available_add_ons.map((addOn) => {
                  const checked = selectedAddOns.some((item) => item.name === addOn.name);
                  return (
                    <label key={addOn.name} className="addon-row">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleAddOn(addOn)}
                      />
                      <div>
                        <strong>{addOn.name}</strong>
                        <p>{addOn.description}</p>
                      </div>
                      <span>Rs. {addOn.price}</span>
                    </label>
                  );
                })}
                <button type="button" className="primary-button" onClick={saveAddOnSelection}>
                  Save selected add-ons
                </button>
              </div>
            )}
          </SectionCard>

          <SectionCard title="Payment flow" subtitle="Create payment, send payment OTP, and verify it.">
            <div className="form-grid">
              <label className="field-label">
                <span>Amount</span>
                <input
                  className="field-input"
                  type="number"
                  min="0"
                  value={paymentState.amount}
                  onChange={(event) =>
                    setPaymentState((currentState) => ({
                      ...currentState,
                      amount: event.target.value,
                    }))
                  }
                  placeholder="Enter payable amount"
                />
              </label>

              <label className="field-label">
                <span>Payment reference</span>
                <input
                  className="field-input"
                  value={paymentState.paymentReference}
                  onChange={(event) =>
                    setPaymentState((currentState) => ({
                      ...currentState,
                      paymentReference: event.target.value,
                    }))
                  }
                  placeholder="Generated payment reference"
                />
              </label>

              <label className="field-label">
                <span>Payment OTP</span>
                <input
                  className="field-input"
                  value={paymentState.otp}
                  onChange={(event) =>
                    setPaymentState((currentState) => ({
                      ...currentState,
                      otp: event.target.value,
                    }))
                  }
                  placeholder="Enter payment OTP"
                />
              </label>
            </div>

            <div className="button-row">
              <button type="button" className="primary-button" onClick={createCustomerPayment}>
                Create payment
              </button>
              <button type="button" className="secondary-button" onClick={sendOtpForPayment}>
                Send payment OTP
              </button>
              <button type="button" className="secondary-button" onClick={verifyOtpForPayment}>
                Verify payment OTP
              </button>
            </div>
          </SectionCard>
        </>
      )}
    </div>
  );
}

export default QuotesPage;
