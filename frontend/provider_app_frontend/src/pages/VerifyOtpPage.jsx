import { useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function VerifyOtpPage() {
  const location = useLocation();
  const { pendingLogin, verifyOtp } = useAuth();
  const [otp, setOtp] = useState("");
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const targetEmail = useMemo(
    () => pendingLogin?.email || location.state?.email || "",
    [location.state?.email, pendingLogin?.email]
  );

  if (!targetEmail) {
    return <Navigate to="/login" replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      await verifyOtp({ email: targetEmail, otp });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="otp-layout">
      <div className="otp-card">
        <p className="eyebrow-text">Second factor verification</p>
        <h1>Enter the OTP sent to your email</h1>
        <p className="muted-copy">
          We sent a provider-admin verification code to <strong>{targetEmail}</strong>.
        </p>
        {pendingLogin?.otpExpiresAt ? (
          <p className="muted-copy">
            OTP expires at: {new Date(pendingLogin.otpExpiresAt).toLocaleString()}
          </p>
        ) : null}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field-label">
            <span>OTP Code</span>
            <input
              className="field-input field-input-large"
              type="text"
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
              inputMode="numeric"
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
      </div>
    </div>
  );
}

export default VerifyOtpPage;
