import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createJourney } from "../lib/api";
import { storeJourneyDraft } from "../lib/storage";

const initialFormState = {
  mobile_number: "",
  insurance_type: "health",
  proposer_first_name: "",
  proposer_last_name: "",
  proposer_email: "",
  proposer_gender: "",
  city: "",
  state: "",
  postal_code: "",
  sum_insured_requested: "",
  policy_term_years: "",
  premium_preference: "",
  occupation: "",
  annual_income: "",
  form_step: "basic-details",
  is_form_completed: false,
};

const coverageOptions = [
  { value: "300000", label: "Rs. 3 lakh", helper: "Entry-level protection" },
  { value: "500000", label: "Rs. 5 lakh", helper: "Balanced family cover" },
  { value: "1000000", label: "Rs. 10 lakh", helper: "Higher medical cushion" },
  { value: "1500000", label: "Rs. 15 lakh", helper: "Broader protection" },
];

function JourneyPage() {
  const navigate = useNavigate();
  const [formState, setFormState] = useState(initialFormState);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (event) => {
    const { name, value } = event.target;
    setFormState((currentState) => ({ ...currentState, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      const response = await createJourney({
        ...formState,
        form_step: "completed",
        is_form_completed: true,
        sum_insured_requested: Number(formState.sum_insured_requested || 0),
        policy_term_years: Number(formState.policy_term_years || 0),
        annual_income: Number(formState.annual_income || 0),
        insured_members: [],
        existing_insurance_details: {},
        medical_history: {},
        additional_answers: {},
      });

      setStatus({
        type: "success",
        message: "Application submitted successfully. Preparing your matching plans.",
      });
      storeJourneyDraft({
        transactionId: response.transaction_id,
        userId: response.user_id,
        mobileNumber: formState.mobile_number,
        insuranceType: formState.insurance_type,
        sumInsuredRequested: Number(formState.sum_insured_requested || 0),
        policyTermYears: Number(formState.policy_term_years || 0),
        proposerName: `${formState.proposer_first_name} ${formState.proposer_last_name}`.trim(),
        city: formState.city,
        state: formState.state,
      });
      navigate("/journey/quotes", {
        state: {
          transactionId: response.transaction_id,
          userId: response.user_id,
          mobileNumber: formState.mobile_number,
          insuranceType: formState.insurance_type,
          sumInsuredRequested: Number(formState.sum_insured_requested),
          proposerName: `${formState.proposer_first_name} ${formState.proposer_last_name}`.trim(),
        },
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="public-page">
      <header className="page-header">
        <p className="eyebrow-text">Health insurance application</p>
        <h1>Tell us about yourself and we will match plans that fit your needs.</h1>
        <p className="page-copy">
          Start with your personal and coverage details. Once this form is submitted,
          you can review quotes, choose a plan, and continue to payment.
        </p>
      </header>

      <section className="journey-overview-card">
        <div className="journey-overview-copy">
          <p className="eyebrow-text">Why health cover matters</p>
          <h2>Choose protection that keeps medical care affordable when life feels uncertain.</h2>
          <p>
            The right health insurance plan helps you manage hospital costs,
            secure your family, and stay prepared for unexpected treatment expenses.
          </p>
        </div>
        <div className="journey-overview-steps">
          <span>Cashless hospital support</span>
          <span>Protection against rising medical costs</span>
          <span>Coverage options for different budgets</span>
          <span>Optional add-ons for stronger protection</span>
          <span>Easy access to your policy after purchase</span>
        </div>
      </section>

      <section className="section-card">
        <div className="section-head">
          <div>
            <p className="eyebrow-text">Application form</p>
            <h3>Start your health cover request</h3>
            <p>
              Complete the form below to generate your quote options. Keep your
              contact details correct so the right policy can be linked to your journey.
            </p>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="form-section form-span-full">
            <div className="form-section-heading">
              <h4>Applicant details</h4>
              <p>Basic information about the person starting the insurance request.</p>
            </div>
          </div>

          <label className="field-label">
            <span>Mobile number</span>
            <input
              className="field-input"
              name="mobile_number"
              value={formState.mobile_number}
              onChange={updateField}
              placeholder="Enter 10-digit mobile number"
              required
            />
          </label>

          <label className="field-label">
            <span>First name</span>
            <input
              className="field-input"
              name="proposer_first_name"
              value={formState.proposer_first_name}
              onChange={updateField}
              placeholder="Enter first name"
              required
            />
          </label>

          <label className="field-label">
            <span>Last name</span>
            <input
              className="field-input"
              name="proposer_last_name"
              value={formState.proposer_last_name}
              onChange={updateField}
              placeholder="Enter last name"
              required
            />
          </label>

          <label className="field-label">
            <span>Email</span>
            <input
              className="field-input"
              type="email"
              name="proposer_email"
              value={formState.proposer_email}
              onChange={updateField}
              placeholder="name@example.com"
              required
            />
          </label>

          <label className="field-label">
            <span>Gender</span>
            <select
              className="field-input"
              name="proposer_gender"
              value={formState.proposer_gender}
              onChange={updateField}
              required
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </label>

          <div className="form-section form-span-full">
            <div className="form-section-heading">
              <h4>Location details</h4>
              <p>This helps us align the application with your city and address region.</p>
            </div>
          </div>

          <label className="field-label">
            <span>City</span>
            <input
              className="field-input"
              name="city"
              value={formState.city}
              onChange={updateField}
              placeholder="Enter city"
              required
            />
          </label>

          <label className="field-label">
            <span>State</span>
            <input
              className="field-input"
              name="state"
              value={formState.state}
              onChange={updateField}
              placeholder="Enter state"
              required
            />
          </label>

          <label className="field-label">
            <span>Postal code</span>
            <input
              className="field-input"
              name="postal_code"
              value={formState.postal_code}
              onChange={updateField}
              placeholder="Enter postal code"
              required
            />
          </label>

          <div className="form-section form-span-full">
            <div className="form-section-heading">
              <h4>Coverage preferences</h4>
              <p>Select your preferred sum insured and a few details that help us prepare better quotes.</p>
            </div>
          </div>

          <label className="field-label">
            <span>Requested sum insured</span>
            <select
              className="field-input"
              name="sum_insured_requested"
              value={formState.sum_insured_requested}
              onChange={updateField}
              required
            >
              <option value="">Select cover amount</option>
              {coverageOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label} · {option.helper}
                </option>
              ))}
            </select>
          </label>

          <label className="field-label">
            <span>Policy term in years</span>
            <input
              className="field-input"
              type="number"
              min="1"
              name="policy_term_years"
              value={formState.policy_term_years}
              onChange={updateField}
              placeholder="For example: 1"
              required
            />
          </label>

          <label className="field-label">
            <span>Premium preference</span>
            <input
              className="field-input"
              name="premium_preference"
              value={formState.premium_preference}
              onChange={updateField}
              placeholder="For example: Balanced cover"
              required
            />
          </label>

          <label className="field-label">
            <span>Occupation</span>
            <input
              className="field-input"
              name="occupation"
              value={formState.occupation}
              onChange={updateField}
              placeholder="For example: Engineer"
              required
            />
          </label>

          <label className="field-label">
            <span>Annual income</span>
            <input
              className="field-input"
              type="number"
              min="0"
              name="annual_income"
              value={formState.annual_income}
              onChange={updateField}
              placeholder="For example: 1200000"
              required
            />
          </label>

          {status.message ? (
            <div
              className={
                status.type === "error"
                  ? "alert-box alert-error form-span-full"
                  : "alert-box alert-success form-span-full"
              }
            >
              {status.message}
            </div>
          ) : null}

          <div className="form-actions form-span-full">
            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "Preparing your quotes..." : "Continue to quotes"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default JourneyPage;
