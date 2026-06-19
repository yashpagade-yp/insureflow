import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useSession } from "../context/SessionContext";

const loginHighlights = [
  "Resume an incomplete insurance application.",
  "Check policy and payment progress with your mobile number.",
  "Access customer support and policy records after purchase.",
];

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
      <section className="auth-shell">
        <div className="auth-panel auth-panel-soft">
          <p className="eyebrow-text">Customer login</p>
          <h1>Return to your insurance journey with a mobile OTP.</h1>
          <p className="page-copy">
            Use the mobile number linked to your application so we can help you
            resume your journey, view policy progress, or access support records.
          </p>

          <div className="auth-benefits">
            {loginHighlights.map((item) => (
              <div key={item} className="auth-benefit-item">
                {item}
              </div>
            ))}
          </div>
        </div>

        <section className="auth-card auth-card-compact">
          <p className="eyebrow-text">Secure sign in</p>
          <h2>Send OTP</h2>
          <p className="page-copy">
            We will send a login OTP to your registered mobile number.
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

            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "Sending OTP..." : "Send OTP"}
            </button>

            <Link to="/journey/new" className="text-link">
              Start a new application
            </Link>
          </form>
        </section>
      </section>
    </div>
  );
}

export default CustomerLoginPage;
