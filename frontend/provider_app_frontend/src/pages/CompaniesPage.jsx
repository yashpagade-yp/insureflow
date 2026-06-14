import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { createCompany, listCompanies } from "../lib/api";

const mediatorInitialState = {
  company_name: "InsureFlow",
  contact_person_name: "",
  contact_email: "",
  contact_phone: "",
};

const providerInitialState = {
  company_name: "",
  contact_person_name: "",
  contact_email: "",
  contact_phone: "",
};

function CompaniesPage() {
  const { auth } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [latestApiKey, setLatestApiKey] = useState("");
  const [formStatus, setFormStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmittingMediator, setIsSubmittingMediator] = useState(false);
  const [isSubmittingProvider, setIsSubmittingProvider] = useState(false);
  const [mediatorFormState, setMediatorFormState] = useState(mediatorInitialState);
  const [providerFormState, setProviderFormState] = useState(providerInitialState);

  const providerCompanies = useMemo(
    () => companies.filter((item) => item.company_type === "provider"),
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

  function handleMediatorChange(event) {
    const { name, value } = event.target;
    setMediatorFormState((currentState) => ({ ...currentState, [name]: value }));
  }

  function handleProviderChange(event) {
    const { name, value } = event.target;
    setProviderFormState((currentState) => ({ ...currentState, [name]: value }));
  }

  async function handleCreateCompany(companyType) {
    const isMediator = companyType === "mediator";
    const formState = isMediator ? mediatorFormState : providerFormState;
    const setSubmitting = isMediator ? setIsSubmittingMediator : setIsSubmittingProvider;
    const setFormState = isMediator ? setMediatorFormState : setProviderFormState;

    setFormStatus({ type: "", message: "" });
    setSubmitting(true);

    try {
      const response = await createCompany({
        ...formState,
        company_type: companyType,
        created_by_admin_id: auth.adminId,
      });

      setLatestApiKey(response.plain_api_key);
      setFormStatus({
        type: "success",
        message: `${response.company.company_name} created successfully.`,
      });
      setFormState(isMediator ? mediatorInitialState : providerInitialState);
      await loadCompanies();
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-stack">
      {formStatus.message ? (
        <div className={formStatus.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {formStatus.message}
        </div>
      ) : null}

      {latestApiKey ? (
        <div className="api-key-banner">
          <p className="eyebrow-text">One-time API key</p>
          <h3>Copy and preserve this key now</h3>
          <code>{latestApiKey}</code>
          <p className="muted-copy">
            This is shown only once after company creation. Use the mediator key for main backend integration.
          </p>
        </div>
      ) : null}

      <div className="content-grid content-grid-wide">
      <SectionCard
        title="Create mediator company"
        subtitle="Register the InsureFlow broker-side health-distribution mediator record first."
      >
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              handleCreateCompany("mediator");
            }}
          >
            <label className="field-label">
              <span>Company name</span>
              <input
                className="field-input"
                name="company_name"
                value={mediatorFormState.company_name}
                onChange={handleMediatorChange}
                required
              />
            </label>

            <label className="field-label">
              <span>Contact person</span>
              <input
                className="field-input"
                name="contact_person_name"
                value={mediatorFormState.contact_person_name}
                onChange={handleMediatorChange}
                placeholder="Mediator owner or admin"
              />
            </label>

            <label className="field-label">
              <span>Contact email</span>
              <input
                className="field-input"
                type="email"
                name="contact_email"
                value={mediatorFormState.contact_email}
                onChange={handleMediatorChange}
                placeholder="platform@example.com"
              />
            </label>

            <label className="field-label">
              <span>Contact phone</span>
              <input
                className="field-input"
                name="contact_phone"
                value={mediatorFormState.contact_phone}
                onChange={handleMediatorChange}
                placeholder="9999999999"
              />
            </label>

            <button className="primary-button" type="submit" disabled={isSubmittingMediator}>
              {isSubmittingMediator ? "Creating..." : "Create mediator company"}
            </button>
          </form>
        </SectionCard>

        <SectionCard
          title="Create provider company"
          subtitle="Register each health insurer before assigning plans to it."
        >
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              handleCreateCompany("provider");
            }}
          >
            <label className="field-label">
              <span>Company name</span>
              <input
                className="field-input"
                name="company_name"
                value={providerFormState.company_name}
                onChange={handleProviderChange}
                placeholder="Acme Health Insurance"
                required
              />
            </label>

            <label className="field-label">
              <span>Contact person</span>
              <input
                className="field-input"
                name="contact_person_name"
                value={providerFormState.contact_person_name}
                onChange={handleProviderChange}
                placeholder="Regional admin"
              />
            </label>

            <label className="field-label">
              <span>Contact email</span>
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
              <span>Contact phone</span>
              <input
                className="field-input"
                name="contact_phone"
                value={providerFormState.contact_phone}
                onChange={handleProviderChange}
                placeholder="8888888888"
              />
            </label>

            <button className="primary-button" type="submit" disabled={isSubmittingProvider}>
              {isSubmittingProvider ? "Creating..." : "Create provider company"}
            </button>
          </form>
        </SectionCard>
      </div>

      <SectionCard
        title="Registered companies"
        subtitle="Use this list to confirm which mediator and health insurer records already exist."
      >
        {isLoading ? (
          <p className="muted-copy">Loading companies...</p>
        ) : companies.length === 0 ? (
          <EmptyState
            title="No companies created yet"
            description="Create a mediator company and then add provider companies."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Type</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={`${company.company_name}-${company.company_type}`}>
                    <td>{company.company_name}</td>
                    <td>{company.company_type}</td>
                    <td>{company.contact_email || "-"}</td>
                    <td>{company.contact_phone || "-"}</td>
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

      <SectionCard
        title="Provider companies ready for plans"
        subtitle="These health insurers can be used in the plan creation form."
      >
        {providerCompanies.length === 0 ? (
          <EmptyState
            title="No provider companies yet"
            description="Create at least one provider company before publishing plans."
          />
        ) : (
          <div className="chip-list">
            {providerCompanies.map((company) => (
              <span key={company.company_name} className="info-chip">
                {company.company_name}
              </span>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default CompaniesPage;
