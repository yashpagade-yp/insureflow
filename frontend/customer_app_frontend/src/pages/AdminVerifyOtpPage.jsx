import { useState } from "react";
import { Navigate } from "react-router-dom";

import { useSession } from "../context/SessionContext";

function AdminVerifyOtpPage() {
  const { pendingAuth, verifyAdminLogin } = useSession();
  const [otp, setOtp] = useState("");
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const email = pendingAuth?.email;

  if (!email) {
    return <Navigate to="/admin/login" replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      await verifyAdminLogin({ email, otp });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page auth-page-admin">
      <section className="auth-card auth-card-admin">
        <p className="eyebrow-text">Admin OTP verification</p>
        <h1>Complete admin login</h1>
        <p className="page-copy">
          We sent a login OTP to <strong>{email}</strong>.
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
            {isSubmitting ? "Verifying..." : "Verify admin OTP"}
          </button>
        </form>
      </section>
    </div>
  );
}

export default AdminVerifyOtpPage;
