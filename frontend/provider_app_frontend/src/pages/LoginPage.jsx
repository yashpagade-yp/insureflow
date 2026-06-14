import { useState } from "react";

import { useAuth } from "../context/AuthContext";

const initialFormState = {
  email: "",
  password: "",
};

function LoginPage() {
  const { startLogin } = useAuth();
  const [formState, setFormState] = useState(initialFormState);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setFormState((currentState) => ({ ...currentState, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      const response = await startLogin(formState);
      setStatus({
        type: "success",
        message: `${response.message} Check your inbox for the OTP.`,
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-layout">
      <section className="auth-hero">
        <p className="eyebrow-text">InsureFlow health insurance operations</p>
        <h1>Run health insurer onboarding from one focused admin console.</h1>
        <p className="auth-hero-copy">
          Use your provider-admin email, password, and OTP to access health
          insurer setup, mediator registration, and policy-plan management.
        </p>

        <div className="hero-grid">
          <article className="hero-tile">
            <h3>Insurer onboarding</h3>
            <p>Register mediators and health insurance providers with clean API-key handoff.</p>
          </article>
          <article className="hero-tile">
            <h3>Plan publishing</h3>
            <p>Define hospitalization, family floater, and rider-ready health plans in one workflow.</p>
          </article>
          <article className="hero-tile">
            <h3>Secure admin access</h3>
            <p>OTP-based verification keeps the live demo realistic, safe, and presentation-ready.</p>
          </article>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <p className="eyebrow-text">Provider admin sign in</p>
          <h2>Start secure login</h2>
          <p className="muted-copy">
            Enter your admin email and password to receive a verification OTP for the health insurance admin panel.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="field-label">
              <span>Email</span>
              <input
                className="field-input"
                type="email"
                name="email"
                value={formState.email}
                onChange={handleInputChange}
                placeholder="you@example.com"
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
                onChange={handleInputChange}
                placeholder="Enter password"
                required
              />
            </label>

            {status.message ? (
              <div
                className={
                  status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"
                }
              >
                {status.message}
              </div>
            ) : null}

            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "Sending OTP..." : "Send OTP"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}

export default LoginPage;
