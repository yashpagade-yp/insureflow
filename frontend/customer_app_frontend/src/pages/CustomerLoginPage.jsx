import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useSession } from "../context/SessionContext";

function CustomerLoginPage() {
  const location = useLocation();
  const { startCustomerLogin } = useSession();
  const [mobileNumber, setMobileNumber] = useState("");
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (location.state?.mobileNumber) {
      setMobileNumber(location.state.mobileNumber);
    }
  }, [location.state]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      const response = await startCustomerLogin({ mobile_number: mobileNumber });
      setStatus({ type: "success", message: response.message });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page auth-page-customer">
      <section className="auth-card">
        <p className="eyebrow-text">Customer resume flow</p>
        <h1>Login with mobile OTP</h1>
        <p className="page-copy">
          Use the mobile number linked to the insurance journey to resume forms, view quotes, and access policy records.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field-label">
            <span>Mobile number</span>
            <input
              className="field-input"
              value={mobileNumber}
              onChange={(event) => setMobileNumber(event.target.value)}
              placeholder="9876543210"
              required
            />
          </label>

          {status.message ? (
            <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
              {status.message}
            </div>
          ) : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Sending OTP..." : "Send OTP"}
          </button>

          <Link to="/journey/new" className="text-link">
            Start a new customer journey
          </Link>
        </form>
      </section>
    </div>
  );
}

export default CustomerLoginPage;
