import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { createJourney } from "../lib/api";

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
        message: `Journey created. Transaction ID: ${response.transaction_id}`,
      });
      navigate("/customer/login", {
        state: {
          mobileNumber: formState.mobile_number,
          transactionId: response.transaction_id,
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
        <p className="eyebrow-text">Customer onboarding</p>
        <h1>Start a health insurance journey in one guided flow.</h1>
        <p className="page-copy">
          Enter the basic applicant and coverage information. After this, the customer can resume with OTP and continue to quotes.
        </p>
      </header>

      <section className="section-card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field-label">
            <span>Mobile number</span>
            <input
              className="field-input"
              name="mobile_number"
              value={formState.mobile_number}
              onChange={updateField}
              placeholder="9876543210"
              required
            />
          </label>

          <label className="field-label">
            <span>Insurance type</span>
            <select
              className="field-input"
              name="insurance_type"
              value={formState.insurance_type}
              onChange={updateField}
            >
              <option value="health">Health</option>
              <option value="life">Life</option>
              <option value="general">General</option>
            </select>
          </label>

          <label className="field-label">
            <span>First name</span>
            <input
              className="field-input"
              name="proposer_first_name"
              value={formState.proposer_first_name}
              onChange={updateField}
              placeholder="Yash"
            />
          </label>

          <label className="field-label">
            <span>Last name</span>
            <input
              className="field-input"
              name="proposer_last_name"
              value={formState.proposer_last_name}
              onChange={updateField}
              placeholder="Pagade"
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
              placeholder="customer@example.com"
            />
          </label>

          <label className="field-label">
            <span>Gender</span>
            <select
              className="field-input"
              name="proposer_gender"
              value={formState.proposer_gender}
              onChange={updateField}
            >
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </label>

          <label className="field-label">
            <span>City</span>
            <input className="field-input" name="city" value={formState.city} onChange={updateField} />
          </label>

          <label className="field-label">
            <span>State</span>
            <input className="field-input" name="state" value={formState.state} onChange={updateField} />
          </label>

          <label className="field-label">
            <span>Postal code</span>
            <input
              className="field-input"
              name="postal_code"
              value={formState.postal_code}
              onChange={updateField}
            />
          </label>

          <label className="field-label">
            <span>Requested sum insured</span>
            <input
              className="field-input"
              type="number"
              min="0"
              name="sum_insured_requested"
              value={formState.sum_insured_requested}
              onChange={updateField}
              placeholder="500000"
            />
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
              placeholder="1"
            />
          </label>

          <label className="field-label">
            <span>Premium preference</span>
            <input
              className="field-input"
              name="premium_preference"
              value={formState.premium_preference}
              onChange={updateField}
              placeholder="Balanced premium"
            />
          </label>

          <label className="field-label">
            <span>Occupation</span>
            <input
              className="field-input"
              name="occupation"
              value={formState.occupation}
              onChange={updateField}
              placeholder="Engineer"
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
              placeholder="1200000"
            />
          </label>

          {status.message ? (
            <div className={status.type === "error" ? "alert-box alert-error form-span-full" : "alert-box alert-success form-span-full"}>
              {status.message}
            </div>
          ) : null}

          <div className="form-actions form-span-full">
            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "Creating journey..." : "Create journey"}
            </button>
            <Link to="/customer/login" className="secondary-button">
              Already started? Resume with OTP
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}

export default JourneyPage;
