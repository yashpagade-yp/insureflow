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
        <p className="eyebrow-text">Provider operations system</p>
        <h1>Run the carrier side like a live command center.</h1>
        <p className="auth-hero-copy">
          Use your provider-admin credentials to enter the internal workspace for
          company onboarding, plan publishing, quote visibility, and payment-side
          monitoring.
        </p>

        <div className="hero-grid">
          <article className="hero-tile">
            <h3>Network control</h3>
            <p>Bring buyer companies and provider carriers into one governed network with clean activation status.</p>
          </article>
          <article className="hero-tile">
            <h3>Plan studio</h3>
            <p>Publish coverage products, riders, pricing, and benefits in a format ready for quote generation.</p>
          </article>
          <article className="hero-tile">
            <h3>Operational visibility</h3>
            <p>Track quotes and payments from the provider side without mixing this experience with the customer journey.</p>
          </article>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <p className="eyebrow-text">Provider admin sign in</p>
          <h2>Enter provider workspace</h2>
          <p className="muted-copy">
            Enter your provider-admin email and password to request a one-time verification code.
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
