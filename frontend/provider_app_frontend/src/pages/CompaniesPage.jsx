import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { createCompany, listCompanies } from "../lib/api";

const providerInitialState = {
  company_name: "",
  contact_person_name: "",
  contact_email: "",
  contact_phone: "",
};

const mediatorContactInitialState = {
  contact_person_name: "",
  contact_email: "",
  contact_phone: "",
};

function CompaniesPage() {
  const { auth } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [latestApiKey, setLatestApiKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [formStatus, setFormStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmittingMediator, setIsSubmittingMediator] = useState(false);
  const [isSubmittingProvider, setIsSubmittingProvider] = useState(false);
  const [mediatorContact, setMediatorContact] = useState(mediatorContactInitialState);
  const [providerFormState, setProviderFormState] = useState(providerInitialState);

  const mediatorCompany = useMemo(
    () => companies.find((c) => c.company_type === "mediator"),
    [companies]
  );

  const providerCompanies = useMemo(
    () => companies.filter((c) => c.company_type === "provider"),
    [companies]
  );

  useEffect(() => {
    loadCompanies();
  }, []);

  async function loadCompanies() {
    setIsLoading(true);
    try {
      const response = await listCompanies();
      setCompanies(response.items ?? []);
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  }

  function handleMediatorContactChange(event) {
    const { name, value } = event.target;
    setMediatorContact((s) => ({ ...s, [name]: value }));
  }

  function handleProviderChange(event) {
    const { name, value } = event.target;
    setProviderFormState((s) => ({ ...s, [name]: value }));
  }

  async function handleRegisterMediator(event) {
    event.preventDefault();
    setFormStatus({ type: "", message: "" });
    setIsSubmittingMediator(true);
    try {
      const response = await createCompany({
        company_name: "InsureFlow",
        company_type: "mediator",
        created_by_admin_id: auth.adminId,
        ...mediatorContact,
      });
      setLatestApiKey(response.plain_api_key);
      setFormStatus({
        type: "success",
        message: "InsureFlow registered as mediator. Copy the API key below.",
      });
      setMediatorContact(mediatorContactInitialState);
      await loadCompanies();
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmittingMediator(false);
    }
  }

  async function handleCreateProvider(event) {
    event.preventDefault();
    setFormStatus({ type: "", message: "" });
    setIsSubmittingProvider(true);
    try {
      const response = await createCompany({
        ...providerFormState,
        company_type: "provider",
        created_by_admin_id: auth.adminId,
      });
      setFormStatus({
        type: "success",
        message: `${response.company.company_name} registered as provider.`,
      });
      setProviderFormState(providerInitialState);
      await loadCompanies();
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmittingProvider(false);
    }
  }

  return (
    <div className="page-stack">
      {formStatus.message ? (
        <div className={formStatus.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {formStatus.message}
        </div>
      ) : null}

      {/* ── One-time API key banner ──────────────────────────────────────── */}
      {latestApiKey ? (
        <div className="api-key-banner">
          <p className="eyebrow-text">⚠ One-time API key — copy now</p>
          <h3>InsureFlow Mediator API Key</h3>
          <code>{latestApiKey}</code>
          <p className="muted-copy" style={{ marginTop: "0.6rem" }}>
            This key is shown <strong>only once</strong>. Paste it into the
            main backend <code>.env</code> as <code>INSUREFLOW_API_KEY</code>{" "}
            to enable broker-to-provider communication.
          </p>
          <button
            type="button"
            className="primary-button"
            style={{ marginTop: "0.9rem" }}
            onClick={() => {
              navigator.clipboard.writeText(latestApiKey);
              setCopied(true);
              setTimeout(() => setCopied(false), 2500);
            }}
          >
            {copied ? "✓ Copied!" : "Copy API key"}
          </button>
        </div>
      ) : null}

      <div className="content-grid content-grid-wide">
        {/* ── Section 1: Register InsureFlow as Mediator (one-time) ────── */}
        <SectionCard
          title="Register InsureFlow as Mediator"
          subtitle="One-time setup. Links the InsureFlow platform as the broker mediator and generates the API key for provider communication."
        >
          {mediatorCompany ? (
            <div className="already-registered-box">
              <span className="registered-icon">✓</span>
              <div>
                <p className="registered-title">InsureFlow is already registered</p>
                <p className="muted-copy" style={{ margin: 0, fontSize: "0.88rem" }}>
                  Status: <strong>{mediatorCompany.is_active ? "Active" : "Inactive"}</strong>
                  {mediatorCompany.contact_email ? ` · ${mediatorCompany.contact_email}` : ""}
                </p>
                <p className="muted-copy" style={{ margin: "0.4rem 0 0", fontSize: "0.85rem" }}>
                  The API key was shown once at registration. If you need a new key,
                  contact your system administrator.
                </p>
              </div>
            </div>
          ) : (
            <form className="form-grid" onSubmit={handleRegisterMediator}>
              <div className="field-label field-span-full">
                <span>Mediator company name</span>
                <input
                  className="field-input field-input-locked"
                  value="InsureFlow"
                  readOnly
                  title="The mediator company is always InsureFlow"
                />
                <p className="field-hint">Pre-set — InsureFlow is the platform mediator.</p>
              </div>

              <label className="field-label">
                <span>Company person <span className="optional-tag">optional</span></span>
                <input
                  className="field-input"
                  name="contact_person_name"
                  value={mediatorContact.contact_person_name}
                  onChange={handleMediatorContactChange}
                  placeholder="e.g. Platform admin"
                />
              </label>

              <label className="field-label">
                <span>Company email <span className="optional-tag">optional</span></span>
                <input
                  className="field-input"
                  type="email"
                  name="contact_email"
                  value={mediatorContact.contact_email}
                  onChange={handleMediatorContactChange}
                  placeholder="platform@insureflow.in"
                />
              </label>

              <label className="field-label">
                <span>Company phone <span className="optional-tag">optional</span></span>
                <input
                  className="field-input"
                  name="contact_phone"
                  value={mediatorContact.contact_phone}
                  onChange={handleMediatorContactChange}
                  placeholder="9999999999"
                />
              </label>

              <div className="field-span-full">
                <button
                  className="primary-button"
                  type="submit"
                  disabled={isSubmittingMediator}
                >
                  {isSubmittingMediator ? "Registering…" : "Register InsureFlow & get API key"}
                </button>
              </div>
            </form>
          )}
        </SectionCard>

        {/* ── Section 2: Register Provider Insurance Company ─────────── */}
        <SectionCard
          title="Register Insurance Provider"
          subtitle="Add an insurance company (e.g. Star Health, HDFC ERGO) to publish plans under."
        >
          <form className="form-grid" onSubmit={handleCreateProvider}>
            <label className="field-label field-span-full">
              <span>Company name</span>
              <input
                className="field-input"
                name="company_name"
                value={providerFormState.company_name}
                onChange={handleProviderChange}
                placeholder="e.g. Star Health Insurance"
                required
              />
            </label>

            <label className="field-label">
              <span>Company person <span className="optional-tag">optional</span></span>
              <input
                className="field-input"
                name="contact_person_name"
                value={providerFormState.contact_person_name}
                onChange={handleProviderChange}
                placeholder="e.g. Regional admin"
              />
            </label>

            <label className="field-label">
              <span>Company email <span className="optional-tag">optional</span></span>
              <input
                className="field-input"
                type="email"
                name="contact_email"
                value={providerFormState.contact_email}
                onChange={handleProviderChange}
                placeholder="provider@example.com"
              />
            </label>

            <label className="field-label">
              <span>Company phone <span className="optional-tag">optional</span></span>
              <input
                className="field-input"
                name="contact_phone"
                value={providerFormState.contact_phone}
                onChange={handleProviderChange}
                placeholder="8888888888"
              />
            </label>

            <div className="field-span-full">
              <button
                className="primary-button"
                type="submit"
                disabled={isSubmittingProvider}
              >
                {isSubmittingProvider ? "Registering…" : "Register provider company"}
              </button>
            </div>
          </form>
        </SectionCard>
      </div>

      {/* ── All registered companies table ──────────────────────────── */}
      <SectionCard
        title="Registered companies"
        subtitle="All mediator and provider companies currently in the system."
      >
        {isLoading ? (
          <p className="muted-copy">Loading companies…</p>
        ) : companies.length === 0 ? (
          <EmptyState
            title="No companies yet"
            description="Register InsureFlow as mediator first, then add provider companies."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Role</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={`${company.company_name}-${company.company_type}`}>
                    <td>{company.company_name}</td>
                    <td>
                      <span className={company.company_type === "mediator" ? "role-pill role-mediator" : "role-pill role-provider"}>
                        {company.company_type === "mediator" ? "Mediator" : "Provider"}
                      </span>
                    </td>
                    <td>{company.contact_email || "—"}</td>
                    <td>{company.contact_phone || "—"}</td>
                    <td>
                      <span className={company.is_active ? "status-pill status-active" : "status-pill"}>
                        {company.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      {/* ── Provider companies ready for plans ──────────────────────── */}
      {providerCompanies.length > 0 && (
        <SectionCard
          title="Provider companies available for plans"
          subtitle="These insurers can be selected when creating insurance plans."
        >
          <div className="chip-list">
            {providerCompanies.map((company) => (
              <span key={company.company_name} className="info-chip">
                {company.company_name}
              </span>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

export default CompaniesPage;
