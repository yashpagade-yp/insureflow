import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import {
  activateProviderCompany,
  createBuyerCompany,
  createProviderCompany,
  deactivateProviderCompany,
  listBuyerCompanies,
  listProviderCompanies,
} from "../lib/api";

const buyerInitialState = {
  company_name: "",
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
  const [buyerCompanies, setBuyerCompanies] = useState([]);
  const [providerCompanies, setProviderCompanies] = useState([]);
  const [latestApiKey, setLatestApiKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [formStatus, setFormStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmittingBuyer, setIsSubmittingBuyer] = useState(false);
  const [isSubmittingProvider, setIsSubmittingProvider] = useState(false);
  const [buyerFormState, setBuyerFormState] = useState(buyerInitialState);
  const [providerFormState, setProviderFormState] = useState(providerInitialState);
  const [statusActionByCompanyId, setStatusActionByCompanyId] = useState({});

  const allCompanies = useMemo(
    () => [...buyerCompanies, ...providerCompanies],
    [buyerCompanies, providerCompanies]
  );

  useEffect(() => {
    loadCompanies();
  }, []);

  async function loadCompanies() {
    setIsLoading(true);
    try {
      const [buyerResponse, providerResponse] = await Promise.all([
        listBuyerCompanies(),
        listProviderCompanies(),
      ]);
      setBuyerCompanies(buyerResponse.items ?? []);
      setProviderCompanies(providerResponse.items ?? []);
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setIsLoading(false);
    }
  }

  function handleBuyerChange(event) {
    const { name, value } = event.target;
    setBuyerFormState((state) => ({ ...state, [name]: value }));
  }

  function handleProviderChange(event) {
    const { name, value } = event.target;
    setProviderFormState((state) => ({ ...state, [name]: value }));
  }

  async function handleCreateBuyerCompany(event) {
    event.preventDefault();
    setFormStatus({ type: "", message: "" });
    setIsSubmittingBuyer(true);
    try {
      const response = await createBuyerCompany({
        ...buyerFormState,
        created_by_admin_id: auth.adminId,
      });
      setLatestApiKey(response.plain_api_key ?? "");
      setFormStatus({
        type: "success",
        message: `${response.company.company_name} created as a buyer company. Copy the API key below now.`,
      });
      setBuyerFormState(buyerInitialState);
      await loadCompanies();
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmittingBuyer(false);
    }
  }

  async function handleCreateProviderCompany(event) {
    event.preventDefault();
    setFormStatus({ type: "", message: "" });
    setIsSubmittingProvider(true);
    try {
      const response = await createProviderCompany({
        ...providerFormState,
        created_by_admin_id: auth.adminId,
      });
      setFormStatus({
        type: "success",
        message: `${response.company.company_name} created as a provider company.`,
      });
      setProviderFormState(providerInitialState);
      await loadCompanies();
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmittingProvider(false);
    }
  }

  async function handleProviderStatusChange(companyId, shouldActivate) {
    setFormStatus({ type: "", message: "" });
    setStatusActionByCompanyId((state) => ({ ...state, [companyId]: true }));
    try {
      const response = shouldActivate
        ? await activateProviderCompany(companyId)
        : await deactivateProviderCompany(companyId);
      setFormStatus({
        type: "success",
        message: response.message,
      });
      await loadCompanies();
    } catch (error) {
      setFormStatus({ type: "error", message: error.message });
    } finally {
      setStatusActionByCompanyId((state) => ({ ...state, [companyId]: false }));
    }
  }

  return (
    <div className="page-stack">
      {formStatus.message ? (
        <div
          className={
            formStatus.type === "error"
              ? "alert-box alert-error"
              : "alert-box alert-success"
          }
        >
          {formStatus.message}
        </div>
      ) : null}

      {latestApiKey ? (
        <div className="api-key-banner">
          <p className="eyebrow-text">One-time API key</p>
          <h3>Buyer company API key</h3>
          <code>{latestApiKey}</code>
          <p className="muted-copy" style={{ marginTop: "0.6rem" }}>
            This key is shown only once. Copy it now and store it in the buyer
            company system that will call provider-side APIs.
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
            {copied ? "Copied" : "Copy API key"}
          </button>
        </div>
      ) : null}

      <div className="content-grid content-grid-wide">
        <SectionCard
          title="Create Buyer Company"
          subtitle="Create and register buyer or mediator companies that will communicate with provider-side APIs through their API keys."
        >
          <form className="form-grid" onSubmit={handleCreateBuyerCompany}>
            <label className="field-label field-span-full">
              <span>Buyer company name</span>
              <input
                className="field-input"
                name="company_name"
                value={buyerFormState.company_name}
                onChange={handleBuyerChange}
                placeholder="e.g. InsureFlow"
                required
              />
            </label>

            <label className="field-label">
              <span>Owner / contact person <span className="optional-tag">optional</span></span>
              <input
                className="field-input"
                name="contact_person_name"
                value={buyerFormState.contact_person_name}
                onChange={handleBuyerChange}
                placeholder="e.g. Platform admin"
              />
            </label>

            <label className="field-label">
              <span>Company email <span className="optional-tag">optional</span></span>
              <input
                className="field-input"
                type="email"
                name="contact_email"
                value={buyerFormState.contact_email}
                onChange={handleBuyerChange}
                placeholder="buyer@example.com"
              />
            </label>

            <label className="field-label">
              <span>Company phone <span className="optional-tag">optional</span></span>
              <input
                className="field-input"
                name="contact_phone"
                value={buyerFormState.contact_phone}
                onChange={handleBuyerChange}
                placeholder="9999999999"
              />
            </label>

            <div className="field-span-full">
              <button
                className="primary-button"
                type="submit"
                disabled={isSubmittingBuyer}
              >
                {isSubmittingBuyer ? "Creating..." : "Create buyer company"}
              </button>
            </div>
          </form>
        </SectionCard>

        <SectionCard
          title="Create Provider Company"
          subtitle="Create insurance provider companies that can publish plans and be activated or deactivated by the provider admin."
        >
          <form className="form-grid" onSubmit={handleCreateProviderCompany}>
            <label className="field-label field-span-full">
              <span>Provider company name</span>
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
              <span>Owner / contact person <span className="optional-tag">optional</span></span>
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
                {isSubmittingProvider ? "Creating..." : "Create provider company"}
              </button>
            </div>
          </form>
        </SectionCard>
      </div>

      <SectionCard
        title="Buyer Companies"
        subtitle="Registered buyer or mediator companies that communicate with provider-side APIs using API keys."
      >
        {isLoading ? (
          <p className="muted-copy">Loading buyer companies...</p>
        ) : buyerCompanies.length === 0 ? (
          <EmptyState
            title="No buyer companies yet"
            description="Create the first buyer company to register it for provider-side API communication."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Code</th>
                  <th>Contact person</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {buyerCompanies.map((company) => (
                  <tr key={company.id}>
                    <td>{company.company_name}</td>
                    <td>{company.company_code}</td>
                    <td>{company.contact_person_name || "-"}</td>
                    <td>{company.contact_email || "-"}</td>
                    <td>{company.contact_phone || "-"}</td>
                    <td>
                      <span
                        className={
                          company.is_active
                            ? "status-pill status-active"
                            : "status-pill"
                        }
                      >
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
        title="Provider Companies"
        subtitle="Provider-side insurance companies. The provider admin can activate or deactivate these companies."
      >
        {isLoading ? (
          <p className="muted-copy">Loading provider companies...</p>
        ) : providerCompanies.length === 0 ? (
          <EmptyState
            title="No provider companies yet"
            description="Create the first provider insurance company to publish plans under it."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Code</th>
                  <th>Contact person</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {providerCompanies.map((company) => (
                  <tr key={company.id}>
                    <td>{company.company_name}</td>
                    <td>{company.company_code}</td>
                    <td>{company.contact_person_name || "-"}</td>
                    <td>{company.contact_email || "-"}</td>
                    <td>{company.contact_phone || "-"}</td>
                    <td>
                      <span
                        className={
                          company.is_active
                            ? "status-pill status-active"
                            : "status-pill"
                        }
                      >
                        {company.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={Boolean(statusActionByCompanyId[company.id])}
                        onClick={() =>
                          handleProviderStatusChange(company.id, !company.is_active)
                        }
                      >
                        {statusActionByCompanyId[company.id]
                          ? "Saving..."
                          : company.is_active
                            ? "Deactivate"
                            : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="All Companies"
        subtitle="Combined provider-side view of buyer companies and provider companies."
      >
        {isLoading ? (
          <p className="muted-copy">Loading companies...</p>
        ) : allCompanies.length === 0 ? (
          <EmptyState
            title="No companies registered yet"
            description="Create buyer companies and provider companies from the separate sections above."
          />
        ) : (
          <div className="chip-list">
            {allCompanies.map((company) => (
              <span key={`${company.company_type}-${company.id}`} className="info-chip">
                {company.company_name} · {company.company_type}
              </span>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default CompaniesPage;
