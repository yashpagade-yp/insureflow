import { Navigate, useLocation } from "react-router-dom";
import { useState } from "react";

import { useSession } from "../context/SessionContext";

function CustomerVerifyOtpPage() {
  const location = useLocation();
  const { pendingAuth, verifyCustomerLogin } = useSession();
  const [otp, setOtp] = useState("");
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const mobileNumber = pendingAuth?.mobileNumber || location.state?.mobileNumber;

  if (!mobileNumber) {
    return <Navigate to="/customer/login" replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      await verifyCustomerLogin({ mobile_number: mobileNumber, otp });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page auth-page-customer">
      <section className="auth-card">
        <p className="eyebrow-text">Verify customer OTP</p>
        <h1>Enter the code sent to your mobile</h1>
        <p className="page-copy">
          We generated an OTP for <strong>{mobileNumber}</strong>. Use it to continue the customer journey.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field-label">
            <span>OTP code</span>
            <input
              className="field-input"
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
              placeholder="Enter OTP"
              required
            />
          </label>

          {status.message ? (
            <div className="alert-box alert-error">{status.message}</div>
          ) : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Verifying..." : "Verify and continue"}
          </button>
        </form>
      </section>
    </div>
  );
}

export default CustomerVerifyOtpPage;
