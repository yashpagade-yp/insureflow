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
  sendPaymentOtp,
  verifyPaymentOtp,
} from "../lib/api";
import {
  getStoredJourneyDraft,
  removeStoredJourneyDraft,
  storeJourneyDraft,
} from "../lib/storage";

const FLOW_STEPS = ["Choose plan", "Add add-ons", "Payment", "Policy"];
const PAYMENT_METHODS = [
  {
    id: "upi",
    label: "UPI",
    detail: "Pay instantly using any UPI app",
    badge: "Popular",
  },
  {
    id: "card",
    label: "Credit or debit card",
    detail: "Visa, Mastercard, RuPay and Amex supported",
    badge: "Secure",
  },
  {
    id: "netbanking",
    label: "Net banking",
    detail: "Use your bank account through online banking",
    badge: "Trusted",
  },
  {
    id: "wallet",
    label: "Wallet",
    detail: "Use your preferred wallet balance for payment",
    badge: "Fast",
  },
];

function formatCurrency(value) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

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
            <span className="journey-step-index">{isComplete ? "OK" : index + 1}</span>
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
    paymentMethod: storedDraft?.paymentMethod || "",
    paymentStage: storedDraft?.paymentStage || "method-selection",
    otp: "",
    plainOtp: storedDraft?.plainOtp || "",
    otpExpiresAt: storedDraft?.otpExpiresAt || "",
  });
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(storedDraft?.currentStep || 0);
  const [policyNumber, setPolicyNumber] = useState(storedDraft?.policyNumber || "");

  useEffect(() => {
    storeJourneyDraft({
      ...journeyMeta,
      selectedPlanId,
      selectedAddOns,
      paymentReference: paymentState.paymentReference,
      paymentMethod: paymentState.paymentMethod,
      paymentStage: paymentState.paymentStage,
      plainOtp: paymentState.plainOtp,
      otpExpiresAt: paymentState.otpExpiresAt,
      currentStep,
      policyNumber,
    });
  }, [
    currentStep,
    journeyMeta,
    paymentState.otpExpiresAt,
    paymentState.paymentMethod,
    paymentState.paymentReference,
    paymentState.paymentStage,
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
        message: "Start your application first so we can prepare your matching plans.",
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

      const sortedPlans = [...eligiblePlans].sort(
        (left, right) => Number(left.total_premium) - Number(right.total_premium)
      );

      const nextSelectedPlanId =
        storedDraft?.selectedPlanId ||
        response.selected_plan_id ||
        sortedPlans[0]?.plan_id ||
        response.items?.[0]?.plan_id ||
        "";

      setSelectedPlanId(nextSelectedPlanId);
    } catch (error) {
      if (error.message?.includes("Quote not found")) {
        removeStoredJourneyDraft();
        setQuoteData(null);
        setJourneyMeta((currentValue) => ({
          ...currentValue,
          transactionId: "",
          userId: session?.userId || "",
          mobileNumber: session?.mobileNumber || "",
          proposerName: "",
          insuranceType: "health",
          sumInsuredRequested: 0,
        }));
        setStatus({
          type: "error",
          message:
            "This old journey is no longer available. Please start a fresh application or resume your latest saved policy journey.",
        });
        return;
      }

      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const visiblePlans = useMemo(() => {
    const items = quoteData?.items ?? [];
    return [...items].sort(
      (left, right) => Number(left.total_premium) - Number(right.total_premium)
    );
  }, [quoteData]);

  const selectedPlan = useMemo(
    () => visiblePlans.find((item) => item.plan_id === selectedPlanId) ?? null,
    [visiblePlans, selectedPlanId]
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
        selected_add_ons: selectedAddOns.map((item) => ({
          name: item.name,
          price: item.price,
        })),
      });
      setPaymentState((currentValue) => ({
        ...currentValue,
        paymentReference: "",
        paymentMethod: "",
        paymentStage: "method-selection",
        otp: "",
        plainOtp: "",
        otpExpiresAt: "",
      }));
      setCurrentStep(2);
      setStatus({
        type: "success",
        message: "Your add-ons are saved. You can continue to payment.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPaymentMethod = async (paymentMethodId) => {
    if (!paymentState.mobileNumber) {
      setStatus({
        type: "error",
        message: "Enter the mobile number for payment verification.",
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
        paymentMethod: paymentMethodId,
        paymentStage: "otp-verification",
        plainOtp: otpResponse.plain_otp || "",
        otpExpiresAt: otpResponse.otp_expires_at || "",
        otp: "",
      }));

      setStatus({
        type: "success",
        message:
          "Payment request created successfully. OTP verification is now ready for this selected payment method.",
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
        message: "Choose a payment method first, then enter the OTP to finish payment.",
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
        message: "Payment successful. Your policy has been issued.",
      });
      removeStoredJourneyDraft();
      } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToPaymentMethods = () => {
    setPaymentState((currentValue) => ({
      ...currentValue,
      paymentStage: "method-selection",
      otp: "",
    }));
  };

  const handleResendPaymentOtp = async () => {
    if (!paymentState.paymentReference || !paymentState.paymentMethod) {
      setStatus({
        type: "error",
        message: "Choose a payment method before requesting another OTP.",
      });
      return;
    }

    setIsLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const otpResponse = await sendPaymentOtp(paymentState.paymentReference);
      setPaymentState((currentValue) => ({
        ...currentValue,
        plainOtp: otpResponse.plain_otp || currentValue.plainOtp,
        otpExpiresAt: otpResponse.otp_expires_at || "",
        otp: "",
      }));
      setStatus({
        type: "success",
        message: "A fresh OTP has been generated for your selected payment method.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  if (!journeyMeta.transactionId && !quoteData) {
    return (
      <div className="page-stack customer-flow-page">
        <header className="page-header page-header-tight">
          <p className="eyebrow-text">Health plans</p>
          <h2>Start your application first to unlock your personalised quotes.</h2>
        </header>

        <SectionCard
          title="No active application found"
          subtitle="We could not find a draft journey to show matching plans right now."
        >
          <EmptyState
            title="Start with the insurance form"
            description="Complete the customer application first. After that, this page will show your matching plans, add-ons, payment step, and issued policy flow."
          />
          <div className="button-row customer-flow-actions">
            <Link to="/journey/new" className="primary-button">
              Start application
            </Link>
            <Link to="/customer/login" className="ghost-button">
              Customer login
            </Link>
          </div>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-stack customer-flow-page">
      <header className="page-header page-header-tight">
        <p className="eyebrow-text">Plan comparison and checkout</p>
        <h2>Choose your health cover with confidence.</h2>
        <p className="page-copy">
          Review matching plans, add optional protection, and complete your purchase
          with a clear step-by-step flow.
        </p>
      </header>

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

      {quoteData ? (
        <section className="journey-overview-card journey-overview-card-compact">
          <div className="journey-overview-copy">
            <p className="eyebrow-text">Your application</p>
            <h3>{journeyMeta.proposerName || "Customer application"}</h3>
            <p className="muted-copy">
              Requested coverage: {formatCurrency(journeyMeta.sumInsuredRequested || 0)}
            </p>
          </div>
          <div className="journey-overview-steps">
            <span>{visiblePlans.length} plans available to compare</span>
            <span>Optional add-ons shown only after plan selection</span>
            <span>Secure checkout with step-by-step payment verification</span>
          </div>
        </section>
      ) : null}

      {quoteData ? <StepBar currentStep={currentStep} /> : null}

      {!quoteData ? (
        <SectionCard
          title="Preparing your matching plans"
          subtitle="Please wait while we gather the best matching plans for your application."
        >
          <div className="button-row customer-flow-actions">
            <button
              type="button"
              className="primary-button"
              onClick={() => loadQuotes(journeyMeta.transactionId)}
              disabled={isLoading}
            >
              {isLoading ? "Loading plans..." : "Load my plans"}
            </button>
            <Link to="/journey/new" className="ghost-button">
              Back to form
            </Link>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 0 ? (
        <SectionCard
          title="Available plans"
          subtitle="These plans are matched to the details you submitted in your insurance application."
        >
          <div className="customer-plan-grid">
            {visiblePlans.map((item) => {
              const isEligible =
                !journeyMeta.sumInsuredRequested ||
                Number(item.coverage_amount) <= Number(journeyMeta.sumInsuredRequested);
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
                      <p className="eyebrow-text">{item.company_name}</p>
                      <h3>{item.plan_name}</h3>
                    </div>
                    <span className="quote-price-badge">
                      {formatCurrency(item.total_premium)}
                    </span>
                  </div>

                  <div className="customer-plan-metrics">
                    <div>
                      <span>Coverage</span>
                      <strong>{formatCurrency(item.coverage_amount)}</strong>
                    </div>
                    <div>
                      <span>Base premium</span>
                      <strong>{formatCurrency(item.base_premium)}</strong>
                    </div>
                    <div>
                      <span>Policy term</span>
                      <strong>
                        {item.duration_years} year{item.duration_years > 1 ? "s" : ""}
                      </strong>
                    </div>
                  </div>

                  <div className="quote-benefits-block">
                    <strong className="quote-section-title">Key benefits</strong>
                    <div className="chip-list">
                      {item.benefits?.length ? (
                        item.benefits.slice(0, 5).map((benefit) => (
                          <span key={benefit} className="info-chip">
                            {benefit}
                          </span>
                        ))
                      ) : (
                        <span className="info-chip">Benefits available on plan details</span>
                      )}
                    </div>
                  </div>

                  <div className="quote-plan-footer">
                    <span>{item.available_add_ons?.length || 0} optional add-ons</span>
                    <span>{formatCurrency(item.tax_amount)} tax included</span>
                  </div>
                </article>
              );
            })}
          </div>

          <div className="button-row customer-flow-actions">
            <Link to="/journey/new" className="ghost-button">
              Back to application
            </Link>
            <button
              type="button"
              className="primary-button"
              onClick={handleConfirmPlan}
              disabled={!selectedPlanId || isLoading}
            >
              {isLoading ? "Saving plan..." : "Continue with this plan"}
            </button>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 1 ? (
        <SectionCard
          title="Optional add-ons"
          subtitle="Add extra protection only if you want it for your selected plan."
        >
          <div className="selected-plan-summary">
            <p className="eyebrow-text">Selected plan</p>
            <h3>{selectedPlan?.plan_name || "Chosen plan"}</h3>
            <p className="muted-copy">
              {selectedPlan?.company_name || ""} - Base premium {formatCurrency(basePremium)}
            </p>
          </div>

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
                    <strong>{formatCurrency(addOn.price)}</strong>
                  </label>
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="No add-ons available"
              description="This plan can be purchased directly without any extra rider selection."
            />
          )}

          <div className="button-row customer-flow-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => setCurrentStep(0)}
            >
              Back to plans
            </button>
            <button
              type="button"
              className="primary-button"
              onClick={handleSaveAddOns}
              disabled={isLoading}
            >
              {isLoading ? "Saving add-ons..." : "Continue to payment"}
            </button>
          </div>
        </SectionCard>
      ) : null}

      {quoteData && currentStep === 2 ? (
        <SectionCard
          title="Secure checkout"
          subtitle="Choose how you want to pay, then continue to OTP verification in a realistic purchase flow."
        >
          <div className="payment-layout">
            <div className="payment-summary-card">
              <p className="eyebrow-text">Plan summary</p>
              <h3>{selectedPlan?.plan_name || "Selected plan"}</h3>
              <p className="muted-copy">
                {selectedPlan?.company_name || "Provider company"}
              </p>

              <div className="payment-line-item">
                <span>Base premium</span>
                <strong>{formatCurrency(basePremium)}</strong>
              </div>

              {selectedAddOns.map((addOn) => (
                <div key={addOn.name} className="payment-line-item">
                  <span>{addOn.name}</span>
                  <strong>{formatCurrency(addOn.price)}</strong>
                </div>
              ))}

              <div className="payment-line-item">
                <span>Tax</span>
                <strong>{formatCurrency(selectedPlan?.tax_amount || 0)}</strong>
              </div>

              <div className="payment-total-row">
                <span>Total payable</span>
                <strong>{formatCurrency(totalPremium)}</strong>
              </div>

              <div className="payment-trust-stack">
                <div className="payment-trust-chip">256-bit secure checkout</div>
                <div className="payment-trust-chip">Insurer-ready payment flow</div>
                <div className="payment-trust-chip">OTP verification required</div>
              </div>
            </div>

            <div className="payment-action-card">
              <label className="field-label">
                <span>Mobile number</span>
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

              {paymentState.paymentStage === "method-selection" ? (
                <>
                  <div className="payment-methods-header">
                    <div>
                      <p className="eyebrow-text">Choose payment method</p>
                      <h3>Select one secure payment option</h3>
                      <p className="muted-copy">
                        Continue with the method that feels most familiar for your insurance purchase.
                      </p>
                    </div>
                  </div>

                  <div className="payment-method-grid">
                    {PAYMENT_METHODS.map((method) => (
                      <button
                        key={method.id}
                        type="button"
                        className={
                          paymentState.paymentMethod === method.id
                            ? "payment-method-card payment-method-card-active"
                            : "payment-method-card"
                        }
                        onClick={() => handleSelectPaymentMethod(method.id)}
                        disabled={isLoading}
                      >
                        <div className="payment-method-head">
                          <strong>{method.label}</strong>
                          <span className="payment-method-badge">{method.badge}</span>
                        </div>
                        <p>{method.detail}</p>
                      </button>
                    ))}
                  </div>

                  <div className="payment-checkout-note">
                    <strong>Checkout note</strong>
                    <p>
                      After you choose a payment method, the payment request will be created and the verification step will open separately.
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="payment-otp-stage-card">
                    <p className="eyebrow-text">OTP verification</p>
                    <h3>
                      {PAYMENT_METHODS.find(
                        (method) => method.id === paymentState.paymentMethod
                      )?.label || "Selected payment method"}
                    </h3>
                    <p className="muted-copy">
                      Your payment request is created. Continue with OTP verification to complete the purchase.
                    </p>
                    <div className="payment-otp-meta">
                      <span>
                        Payment reference: {paymentState.paymentReference || "-"}
                      </span>
                      <span>
                        OTP status: {paymentState.otpExpiresAt ? "Generated in backend" : "Pending"}
                      </span>
                    </div>
                  </div>

                  <label className="field-label">
                    <span>Enter OTP</span>
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

                  <div className="payment-checkout-note payment-checkout-note-soft">
                    <strong>Demo behavior</strong>
                    <p>
                      OTP is handled by the backend flow. This customer screen no longer shows the OTP directly.
                    </p>
                  </div>
                </>
              )}

              <div className="button-row customer-flow-actions">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() =>
                    paymentState.paymentStage === "method-selection"
                      ? setCurrentStep(1)
                      : handleBackToPaymentMethods()
                  }
                >
                  {paymentState.paymentStage === "method-selection"
                    ? "Back to add-ons"
                    : "Back to payment methods"}
                </button>

                {paymentState.paymentStage === "method-selection" ? null : (
                  <>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={handleResendPaymentOtp}
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
                      {isLoading ? "Verifying..." : "Complete payment"}
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
          title="Your policy is ready"
          subtitle="Payment is complete and your purchase journey has been successfully finished."
        >
          <div className="completion-card">
            <div>
              <p className="eyebrow-text">Purchase complete</p>
              <h3>
                {policyNumber
                  ? `Policy number: ${policyNumber}`
                  : "Policy issued successfully"}
              </h3>
              <p className="muted-copy">
                You can now log in later with your mobile number and OTP to view your
                dashboard and access policy details.
              </p>
            </div>

            <div className="button-row customer-flow-actions">
              <Link
                to="/customer/login"
                className="ghost-button"
                state={{ mobileNumber: journeyMeta.mobileNumber }}
              >
                Customer login
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
