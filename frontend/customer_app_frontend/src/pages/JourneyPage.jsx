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

const journeyNotes = [
  "The form is short and focused on the details needed to generate matching plans.",
  "You can compare plans before moving to payment.",
  "After payment verification, your policy will be issued and saved to your account.",
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
    <div className="public-page customer-journey-page">
      <section className="journey-hero-card">
        <div className="journey-hero-copy">
          <p className="eyebrow-text">Health insurance application</p>
          <h1>Start with a few details and we will prepare plans that fit your needs.</h1>
          <p className="page-copy">
            This form is designed to stay clear and easy to complete. Once you submit it,
            we will show matching plans, optional add-ons, and the payment step.
          </p>
        </div>

        <div className="journey-hero-side">
          <div className="journey-summary-card">
            <p className="eyebrow-text">What happens next</p>
            <div className="journey-summary-steps">
              <span>1. Submit your application details</span>
              <span>2. Review matched plans</span>
              <span>3. Choose add-ons and verify payment</span>
              <span>4. Receive your policy in your account</span>
            </div>
          </div>
        </div>
      </section>

      <section className="customer-journey-layout">
        <section className="section-card">
          <div className="section-head">
            <div>
              <p className="eyebrow-text">Application form</p>
              <h3>Tell us about the applicant and your preferred coverage</h3>
              <p>
                Complete the form below to generate your quote options. Keep your
                contact details accurate so the right policy is linked to your journey.
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
              <span>Email address</span>
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
                <p>This helps align the application with your city and address region.</p>
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
                    {option.label} - {option.helper}
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

        <aside className="journey-side-panel">
          <section className="section-card">
            <div className="section-head">
              <div>
                <p className="eyebrow-text">Application guide</p>
                <h3>Keep the process easy</h3>
              </div>
            </div>

            <div className="stacked-fields">
              {journeyNotes.map((item) => (
                <div key={item} className="journey-note-card">
                  {item}
                </div>
              ))}
            </div>
          </section>
        </aside>
      </section>
    </div>
  );
}

export default JourneyPage;
