import { useState } from "react";

import { useSession } from "../context/SessionContext";

function AdminLoginPage() {
  const { startAdminLogin } = useSession();
  const [formState, setFormState] = useState({ email: "", password: "" });
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
      const response = await startAdminLogin(formState);
      setStatus({ type: "success", message: response.message });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page auth-page-admin">
      <section className="auth-card auth-card-admin">
        <p className="eyebrow-text">Admin access</p>
        <h1>Login for customer operations</h1>
        <p className="page-copy">
          Admins use email, password, and OTP to handle issued policies, transactions, and user-side operational tasks.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field-label">
            <span>Email</span>
            <input
              className="field-input"
              type="email"
              name="email"
              value={formState.email}
              onChange={updateField}
              required
            />
          </label>

          <label className="field-label">
            <span>Password</span>
            <input
              className="field-input"
              type="password"
              name="password"
              value={formState.password}
              onChange={updateField}
              required
            />
          </label>

          {status.message ? (
            <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
              {status.message}
            </div>
          ) : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Sending OTP..." : "Send admin OTP"}
          </button>
        </form>
      </section>
    </div>
  );
}

export default AdminLoginPage;
