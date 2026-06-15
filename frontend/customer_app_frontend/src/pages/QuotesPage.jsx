import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import { useSession } from "../context/SessionContext";
import {
  createPayment,
  getQuotes,
  selectAddOns,
  selectPlan,
  verifyPaymentOtp,
  sendPaymentOtp,
} from "../lib/api";
import {
  getStoredJourneyDraft,
  removeStoredJourneyDraft,
  storeJourneyDraft,
} from "../lib/storage";

const FLOW_STEPS = ["View plans", "Add-ons", "Payment", "Complete"];

function StepBar({ currentStep }) {
  return (
    <div className="journey-stepbar">
      {FLOW_STEPS.map((label, index) => {
        const isComplete = currentStep > index;
        const isCurrent = currentStep === index;

        return (
          <div
            key={label}
            className={`journey-step ${
              isComplete ? "journey-step-complete" : ""
            } ${isCurrent ? "journey-step-current" : ""}`}
          >
            <span className="journey-step-index">
              {isComplete ? "✓" : index + 1}
            </span>
            <span>{label}</span>
          </div>
        );
      })}
    </div>
  );
}

function QuotesPage() {
  const location = useLocation();
  const { session } = useSession();

  const storedDraft = getStoredJourneyDraft();
  const routerState = location.state || {};

  const initialJourney = {
    transactionId: routerState.transactionId || storedDraft?.transactionId || "",
    userId: routerState.userId || storedDraft?.userId || session?.userId || "",
    mobileNumber:
      routerState.mobileNumber ||
      storedDraft?.mobileNumber ||
      session?.mobileNumber ||
      "",
    proposerName: routerState.proposerName || storedDraft?.proposerName || "",
    insuranceType:
      routerState.insuranceType || storedDraft?.insuranceType || "health",
    sumInsuredRequested:
      routerState.sumInsuredRequested || storedDraft?.sumInsuredRequested || 0,
  };

  const [journeyMeta, setJourneyMeta] = useState(initialJourney);
  const [quoteData, setQuoteData] = useState(null);
  const [selectedPlanId, setSelectedPlanId] = useState(
    storedDraft?.selectedPlanId || ""
  );
  const [selectedAddOns, setSelectedAddOns] = useState(
    storedDraft?.selectedAddOns || []
  );
  const [paymentState, setPaymentState] = useState({
    paymentReference: storedDraft?.paymentReference || "",
    mobileNumber: initialJourney.mobileNumber,
    otp: "",
    plainOtp: storedDraft?.plainOtp || "",
    otpExpiresAt: storedDraft?.otpExpiresAt || "",
  });
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(storedDraft?.currentStep || 0);
  const [policyNumber, setPolicyNumber] = useState(
    storedDraft?.policyNumber || ""
  );

  useEffect(() => {
    storeJourneyDraft({
      ...journeyMeta,
      selectedPlanId,
      selectedAddOns,
      paymentReference: paymentState.paymentReference,
      plainOtp: paymentState.plainOtp,
      otpExpiresAt: paymentState.otpExpiresAt,
      currentStep,
      policyNumber,
    });
  }, [
    currentStep,
    journeyMeta,
    paymentState.otpExpiresAt,
    paymentState.paymentReference,
    paymentState.plainOtp,
    policyNumber,
    selectedAddOns,
    selectedPlanId,
  ]);

  useEffect(() => {
    if (journeyMeta.transactionId && !quoteData) {
      void loadQuotes(journeyMeta.transactionId);
    }
  }, [journeyMeta.transactionId, quoteData]);

  const loadQuotes = async (transactionId) => {
    if (!transactionId) {
      setStatus({
        type: "error",
        message: "Create or resume a journey first to fetch quotes.",
      });
      return;
    }

    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const response = await getQuotes(transactionId);
      setQuoteData(response);

      const eligiblePlans =
        response.items?.filter(
          (item) =>
            !journeyMeta.sumInsuredRequested ||
            Number(item.coverage_amount) <= Number(journeyMeta.sumInsuredRequested)
        ) ?? [];

      const nextSelectedPlanId =
        storedDraft?.selectedPlanId ||
        response.selected_plan_id ||
        eligiblePlans[0]?.plan_id ||
        response.items?.[0]?.plan_id ||
        "";

      setSelectedPlanId(nextSelectedPlanId);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const selectedPlan = useMemo(
    () => quoteData?.items?.find((item) => item.plan_id === selectedPlanId) ?? null,
    [quoteData, selectedPlanId]
  );

  const basePremium = Number(selectedPlan?.base_premium || 0);
  const addOnsTotal = selectedAddOns.reduce(
    (sum, addOn) => sum + Number(addOn.price || 0),
    0
  );
  const totalPremium = basePremium + addOnsTotal;

  const toggleAddOn = (addOn) => {
    setSelectedAddOns((currentValue) => {
      const exists = currentValue.some((item) => item.name === addOn.name);

      if (exists) {
        return currentValue.filter((item) => item.name !== addOn.name);
      }

      return [
        ...currentValue,
        { name: addOn.name, description: addOn.description, price: addOn.price },
      ];
    });
  };

  const handleConfirmPlan = async () => {
    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      await selectPlan({
        transaction_id: journeyMeta.transactionId,
        selected_plan_id: selectedPlanId,
      });
      setCurrentStep(1);
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveAddOns = async () => {
    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      await selectAddOns({
        transaction_id: journeyMeta.transactionId,
        selected_plan_id: selectedPlanId,
        selected_add_ons: selectedAddOns,
      });
      setCurrentStep(2);
      setStatus({
        type: "success",
        message: "Add-ons saved. Continue to payment.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendPaymentOtp = async () => {
    if (!paymentState.mobileNumber) {
      setStatus({
        type: "error",
        message: "Enter the mobile number that should receive the payment OTP.",
      });
      return;
    }

    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      let paymentReference = paymentState.paymentReference;

      if (!paymentReference) {
        const createPaymentResponse = await createPayment({
          transaction_id: journeyMeta.transactionId,
          user_id: journeyMeta.userId || session?.userId,
          amount: totalPremium,
        });
        paymentReference = createPaymentResponse.payment_reference;
      }

      const otpResponse = await sendPaymentOtp(paymentReference);

      setPaymentState((currentValue) => ({
        ...currentValue,
        paymentReference,
        plainOtp: otpResponse.plain_otp || "",
        otpExpiresAt: otpResponse.otp_expires_at || "",
      }));

      setStatus({
        type: "success",
        message: otpResponse.plain_otp
          ? "Payment OTP sent. In dev mode, the OTP is shown below as well."
          : "Payment OTP sent to the registered mobile number.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyPaymentOtp = async () => {
    if (!paymentState.paymentReference || !paymentState.otp) {
      setStatus({
        type: "error",
        message: "Send the OTP first, then enter it to complete payment.",
      });
      return;
    }

    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const response = await verifyPaymentOtp({
        transaction_id: journeyMeta.transactionId,
        payment_reference: paymentState.paymentReference,
        otp: paymentState.otp,
      });

      setPolicyNumber(response.policy_number || "");
      setCurrentStep(3);
      setStatus({
        type: "success",
        message:
          "Payment verified and policy issued successfully. You can now access your policy details.",
      });
      removeStoredJourneyDraft();
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-stack customer-flow-page">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Customer purchase flow</p>
        <h2>Move from quote selection to policy issuance in one guided journey.</h2>
        <p className="page-copy">
          Review quotes, choose one plan, optionally add riders, verify payment
          by OTP, and complete the policy purchase without leaving the flow.
        </p>
      </header>

      <section className="journey-overview-card journey-overview-card-compact">
        <div className="journey-overview-copy">
          <p className="eyebrow-text">Current journey</p>
          <h3>
            {journeyMeta.proposerName || "Customer journey"}{" "}
            {journeyMeta.mobileNumber ? `• ${journeyMeta.mobileNumber}` : ""}
          </h3>
          <p>
            Transaction ID:{" "}
            <strong>{journeyMeta.transactionId || "Create or resume a journey"}</strong>
          </p>
        </div>
        <div className="journey-overview-steps">
          <span>{journeyMeta.insuranceType} insurance</span>
          <span>
            Sum insured: ₹
            {Number(journeyMeta.sumInsuredRequested || 0).toLocaleString()}
          </span>
        </div>
      </section>

      {status.message ? (
        <div
          className={
            status.type === "error"
              ? "alert-box alert-error"
              : "alert-box alert-success"
          }
        >
          {status.message}
        </div>
      ) : null}

      {quoteData ? <StepBar currentStep={currentStep} /> : null}

      {!quoteData ? (
        <SectionCard
          title="Load provider quotes"
          subtitle="Continue from a created journey or use a saved transaction to fetch plans."
        >
          <div className="stacked-fields">
            <label className="field-label">
              <span>Transaction ID</span>
              <input
                className="field-input"
                value={journeyMeta.transactionId}
                onChange={(event) =>
                  setJourneyMeta((currentValue) => ({
                    ...currentValue,
                    transactionId: event.target.value,
                  }))
                }
                placeholder="Enter transaction ID"
              />
            </label>

            <div className="button-row customer-flow-actions">
              <Link to="/journey/new" className="ghost-button">
                Start a new journey
              </Link>
              <Link
                to="/customer/login"
                className="ghost-button"
                state={{ mobileNumber: journeyMeta.mobileNumber }}
              >
                Resume with OTP
              </Link>
              <button
                type="button"
                className="primary-button"
                onClick={() => loadQuotes(journeyMeta.transactionId)}
                disabled={isLoading}
              >
                {isLoading ? "Loading..." : "Fetch quotes"}
              </button>
            </div>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 0 ? (
        <SectionCard
          title="Choose your plan"
          subtitle="Compare plans returned by the provider network and confirm the best fit."
        >
          {journeyMeta.sumInsuredRequested ? (
            <div className="coverage-filter-note">
              Plans above your requested sum insured are shown for visibility,
              but only eligible plans are selectable.
            </div>
          ) : null}

          <div className="customer-plan-grid">
            {quoteData.items.map((item) => {
              const isEligible =
                !journeyMeta.sumInsuredRequested ||
                Number(item.coverage_amount) <=
                  Number(journeyMeta.sumInsuredRequested);
              const isSelected = item.plan_id === selectedPlanId;

              return (
                <article
                  key={item.plan_id}
                  className={`customer-plan-card ${
                    isSelected ? "customer-plan-card-selected" : ""
                  } ${!isEligible ? "quotes-plan-disabled" : ""}`}
                  onClick={() => isEligible && setSelectedPlanId(item.plan_id)}
                >
                  <div className="customer-plan-header">
                    <div>
                      <h3>{item.plan_name}</h3>
                      <p>{item.company_name}</p>
                    </div>
                    <span className="info-chip">{item.quote_status}</span>
                  </div>

                  <div className="customer-plan-metrics">
                    <div>
                      <span>Coverage</span>
                      <strong>₹{Number(item.coverage_amount).toLocaleString()}</strong>
                    </div>
                    <div>
                      <span>Base premium</span>
                      <strong>₹{Number(item.base_premium).toLocaleString()}</strong>
                    </div>
                    <div>
                      <span>Duration</span>
                      <strong>{item.duration_years} years</strong>
                    </div>
                  </div>

                  {item.benefits.length ? (
                    <div className="chip-list">
                      {item.benefits.slice(0, 4).map((benefit) => (
                        <span key={benefit} className="info-chip">
                          {benefit}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>

          <div className="button-row customer-flow-actions">
            <Link to="/journey/new" className="ghost-button">
              ← Back to form
            </Link>
            <button
              type="button"
              className="primary-button"
              onClick={handleConfirmPlan}
              disabled={!selectedPlanId || isLoading}
            >
              {isLoading ? "Saving..." : "Confirm selected plan"}
            </button>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 1 ? (
        <SectionCard
          title="Select optional add-ons"
          subtitle="Choose only the riders you actually want to add to the selected plan."
        >
          {selectedPlan?.available_add_ons?.length ? (
            <div className="stacked-fields">
              {selectedPlan.available_add_ons.map((addOn) => {
                const checked = selectedAddOns.some(
                  (item) => item.name === addOn.name
                );

                return (
                  <label key={addOn.name} className="addon-card">
                    <div className="addon-card-main">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleAddOn(addOn)}
                      />
                      <div>
                        <strong>{addOn.name}</strong>
                        <p className="muted-copy">{addOn.description}</p>
                      </div>
                    </div>
                    <strong>₹{Number(addOn.price).toLocaleString()}</strong>
                  </label>
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="No add-ons on this plan"
              description="This plan can be purchased directly without any optional add-ons."
            />
          )}

          <div className="button-row customer-flow-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => setCurrentStep(0)}
            >
              ← Back to plan selection
            </button>
            <button
              type="button"
              className="primary-button"
              onClick={handleSaveAddOns}
              disabled={isLoading}
            >
              {isLoading ? "Saving..." : "Continue to payment"}
            </button>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 2 ? (
        <SectionCard
          title="Payment verification"
          subtitle="We create the payment automatically and then verify it using OTP."
        >
          <div className="payment-layout">
            <div className="payment-summary-card">
              <p className="eyebrow-text">Insurance summary</p>
              <h3>{selectedPlan?.plan_name || "Selected plan"}</h3>
              <p className="muted-copy">
                {selectedPlan?.company_name || "Provider company"}
              </p>

              <div className="payment-line-item">
                <span>Base premium</span>
                <strong>₹{basePremium.toLocaleString()}</strong>
              </div>

              {selectedAddOns.map((addOn) => (
                <div key={addOn.name} className="payment-line-item">
                  <span>+ {addOn.name}</span>
                  <strong>₹{Number(addOn.price).toLocaleString()}</strong>
                </div>
              ))}

              <div className="payment-total-row">
                <span>Total payable</span>
                <strong>₹{totalPremium.toLocaleString()}</strong>
              </div>
            </div>

            <div className="payment-action-card">
              <label className="field-label">
                <span>Mobile number for payment OTP</span>
                <input
                  className="field-input"
                  value={paymentState.mobileNumber}
                  onChange={(event) =>
                    setPaymentState((currentValue) => ({
                      ...currentValue,
                      mobileNumber: event.target.value,
                    }))
                  }
                  placeholder="Enter mobile number"
                />
              </label>

              {paymentState.paymentReference ? (
                <div className="payment-reference-banner">
                  <strong>Payment reference</strong>
                  <span>{paymentState.paymentReference}</span>
                </div>
              ) : null}

              {paymentState.plainOtp ? (
                <div className="payment-otp-preview">
                  <p className="eyebrow-text">Dev OTP preview</p>
                  <h3>{paymentState.plainOtp}</h3>
                  <p className="muted-copy">
                    Use this OTP directly in dev mode instead of checking SMS.
                  </p>
                </div>
              ) : null}

              {paymentState.paymentReference ? (
                <label className="field-label">
                  <span>Enter payment OTP</span>
                  <input
                    className="field-input field-input-large"
                    value={paymentState.otp}
                    onChange={(event) =>
                      setPaymentState((currentValue) => ({
                        ...currentValue,
                        otp: event.target.value,
                      }))
                    }
                    placeholder="Enter OTP"
                  />
                </label>
              ) : null}

              <div className="button-row customer-flow-actions">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setCurrentStep(1)}
                >
                  ← Back to add-ons
                </button>

                {!paymentState.paymentReference ? (
                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleSendPaymentOtp}
                    disabled={isLoading}
                  >
                    {isLoading
                      ? "Sending OTP..."
                      : `Send OTP for ₹${totalPremium.toLocaleString()}`}
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={handleSendPaymentOtp}
                      disabled={isLoading}
                    >
                      Resend OTP
                    </button>
                    <button
                      type="button"
                      className="primary-button"
                      onClick={handleVerifyPaymentOtp}
                      disabled={!paymentState.otp || isLoading}
                    >
                      {isLoading ? "Verifying..." : "Verify OTP"}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 3 ? (
        <SectionCard
          title="Policy issued successfully"
          subtitle="The customer journey is complete and the policy record has been created."
        >
          <div className="completion-card">
            <div>
              <p className="eyebrow-text">Completed</p>
              <h3>Policy number: {policyNumber}</h3>
              <p className="muted-copy">
                Transaction {journeyMeta.transactionId} has moved from quote
                selection to policy issuance successfully.
              </p>
            </div>

            <div className="button-row customer-flow-actions">
              <Link
                to="/customer/login"
                className="ghost-button"
                state={{ mobileNumber: journeyMeta.mobileNumber }}
              >
                Resume later with OTP
              </Link>
              <Link to="/" className="primary-button">
                Back to home
              </Link>
            </div>
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}

export default QuotesPage;
