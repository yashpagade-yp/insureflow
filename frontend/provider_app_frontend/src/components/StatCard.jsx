function StatCard({ label, value, helper }) {
  return (
    <article className="stat-card">
      <p className="stat-label">{label}</p>
      <h3 className="stat-value">{value}</h3>
      <p className="stat-helper">{helper}</p>
    </article>
  );
}

export default StatCard;
