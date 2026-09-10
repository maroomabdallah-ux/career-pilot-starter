import {
  Activity,
  AlertTriangle,
  Coins,
  Cpu,
  Database,
  ChevronDown,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import AsyncState from "../components/common/AsyncState";
import { apiErrorMessage, careerApi } from "../services/careerApi";

const money = (value) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
  }).format(Number(value || 0));
const number = (value) =>
  new Intl.NumberFormat("en-US").format(Number(value || 0));
const tabs = ["user", "agent", "model", "request", "conversation"];

function Trend({ daily, field, color }) {
  const values = daily.map((x) => Number(x[field] || 0));
  const max = Math.max(...values, 1);
  const points = values
    .map(
      (value, index) =>
        `${(index / Math.max(values.length - 1, 1)) * 100},${38 - (value / max) * 34}`,
    )
    .join(" ");
  return (
    <svg
      className="usage-trend"
      viewBox="0 0 100 40"
      preserveAspectRatio="none"
      aria-label={`${field} trend`}
    >
      <polyline
        points={points || "0,38 100,38"}
        fill="none"
        stroke={color}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

function Table({ tab, rows }) {
  const name = (row) =>
    row.email ||
    row.agent_name ||
    row.model ||
    row.request_id ||
    row.conversation_id ||
    "No conversation";
  return (
    <div className="usage-table-wrap">
      <table className="usage-table">
        <thead>
          <tr>
            <th>{tab}</th>
            {tab === "request" && <th>Agents</th>}
            <th>Calls</th>
            <th>Tokens</th>
            <th>Cost</th>
            <th>Average/call</th>
            {tab === "model" && <th>Cache savings</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${name(row)}-${index}`}>
              <td>
                <strong>{name(row)}</strong>
                {row.user_id && <small>{row.user_id}</small>}
              </td>
              {tab === "request" && <td>{row.agents?.join(", ")}</td>}
              <td>{number(row.llm_calls)}</td>
              <td>{number(row.total_tokens)}</td>
              <td>{money(row.total_cost)}</td>
              <td>
                {money(
                  Number(row.total_cost || 0) / Math.max(row.llm_calls || 0, 1),
                )}
              </td>
              {tab === "model" && (
                <td>
                  {row.estimated_cache_savings == null
                    ? "Unknown pricing"
                    : money(row.estimated_cache_savings)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && (
        <p className="usage-empty">No tracked calls match these filters.</p>
      )}
    </div>
  );
}

function CostBars({ title, rows, labelKey }) {
  const max = Math.max(...rows.map((row) => Number(row.total_cost || 0)), 1);
  return (
    <article className="usage-cost-bars">
      <span>{title}</span>
      {rows.slice(0, 6).map((row) => (
        <div key={row[labelKey]}>
          <small>{row[labelKey]}</small>
          <i
            style={{ width: `${(Number(row.total_cost || 0) / max) * 100}%` }}
          />
          <b>{money(row.total_cost)}</b>
        </div>
      ))}
      {!rows.length && <p>No cost data yet.</p>}
    </article>
  );
}

export default function AdminAIUsagePage() {
  const [summary, setSummary] = useState(null);
  const [daily, setDaily] = useState([]);
  const [rows, setRows] = useState([]);
  const [agentCosts, setAgentCosts] = useState([]);
  const [modelCosts, setModelCosts] = useState([]);
  const [tab, setTab] = useState("user");
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [filters, setFilters] = useState({
    date_from: "",
    date_to: "",
    agent: "",
    model: "",
    user_id: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const params = useMemo(() => {
    const result = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v),
    );
    if (result.date_from) result.date_from = `${result.date_from}T00:00:00Z`;
    if (result.date_to) result.date_to = `${result.date_to}T23:59:59Z`;
    return result;
  }, [filters]);
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, d, b, agents, models] = await Promise.all([
        careerApi.getAIUsageSummary(params),
        careerApi.getAIUsageDaily(params),
        careerApi.getAIUsageBreakdown(tab, { ...params, page_size: 50 }),
        careerApi.getAIUsageBreakdown("agent", { ...params, page_size: 10 }),
        careerApi.getAIUsageBreakdown("model", { ...params, page_size: 10 }),
      ]);
      setSummary(s);
      setDaily(d);
      setRows(b.items);
      setAgentCosts(agents.items);
      setModelCosts(models.items);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [params, tab]);
  useEffect(() => {
    load();
  }, [load]);
  const cards = summary
    ? [
        ["Total LLM calls", number(summary.llm_calls), Activity],
        ["Total tokens", number(summary.total_tokens), Database],
        ["Total AI cost", money(summary.total_cost), Coins],
        ["Today's cost", money(summary.today_cost), Cpu],
        ["Month cost", money(summary.month_cost), Coins],
        ["Avg / call", money(summary.average_cost_per_call), Activity],
        ["Avg / request", money(summary.average_cost_per_request), Activity],
        ["Active AI users", number(summary.active_ai_users), Users],
      ]
    : [];
  const primaryCards = cards.slice(0, 4);
  const secondaryCards = cards.slice(4);
  return (
    <main className="page admin-usage-page">
      <header className="usage-header">
        <div>
          <span className="section-eyebrow">
            Administration · Actual provider usage
          </span>
          <h1>AI Usage & Cost Management</h1>
          <p>Token and USD accounting from individual CareerPilot LLM calls.</p>
        </div>
        <button className="button secondary" onClick={load}>
          Refresh data
        </button>
      </header>
      <details className="usage-filter-panel">
        <summary>
          Filters <span>Optional</span>
          <ChevronDown size={16} />
        </summary>
        <section className="usage-filters">
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) =>
              setFilters((x) => ({ ...x, date_from: e.target.value }))
            }
          />
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) =>
              setFilters((x) => ({ ...x, date_to: e.target.value }))
            }
          />
          <input
            placeholder="User UUID"
            value={filters.user_id}
            onChange={(e) =>
              setFilters((x) => ({ ...x, user_id: e.target.value }))
            }
          />
          <input
            placeholder="Agent"
            value={filters.agent}
            onChange={(e) =>
              setFilters((x) => ({ ...x, agent: e.target.value }))
            }
          />
          <input
            placeholder="Model"
            value={filters.model}
            onChange={(e) =>
              setFilters((x) => ({ ...x, model: e.target.value }))
            }
          />
        </section>
      </details>
      <AsyncState
        loading={loading}
        error={error ? { message: apiErrorMessage(error) } : null}
      >
        {summary && (
          <>
            <section className="usage-kpis">
              {primaryCards.map(([label, value, Icon]) => (
                <article key={label}>
                  <Icon size={17} />
                  <span>{label}</span>
                  <strong>{value}</strong>
                </article>
              ))}
            </section>
            <button
              className="usage-details-toggle"
              onClick={() => setDetailsOpen((value) => !value)}
              aria-expanded={detailsOpen}
            >
              {detailsOpen
                ? "Hide detailed analytics"
                : "Show detailed analytics"}
              <ChevronDown size={16} />
            </button>
            {(summary.unknown_pricing_calls > 0 ||
              summary.missing_usage_calls > 0 ||
              summary.failed_llm_calls > 0) && (
              <div className="usage-warning">
                <AlertTriangle size={18} />
                <div>
                  <strong>Accounting attention required</strong>
                  <p>
                    {summary.unknown_pricing_calls} unknown-pricing ·{" "}
                    {summary.missing_usage_calls} missing usage ·{" "}
                    {summary.failed_llm_calls} failed LLM calls
                  </p>
                </div>
              </div>
            )}
            {detailsOpen && (
              <div className="usage-details">
                <section className="usage-kpis usage-kpis-secondary">
                  {secondaryCards.map(([label, value, Icon]) => (
                    <article key={label}>
                      <Icon size={17} />
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </article>
                  ))}
                </section>
                <section className="usage-charts">
                  <article>
                    <span>Daily AI cost</span>
                    <strong>{money(summary.total_cost)}</strong>
                    <Trend daily={daily} field="total_cost" color="#2f80ed" />
                  </article>
                  <article>
                    <span>Daily tokens</span>
                    <strong>{number(summary.total_tokens)}</strong>
                    <Trend daily={daily} field="total_tokens" color="#6d5bd0" />
                  </article>
                  <article>
                    <span>Calls per day</span>
                    <strong>{number(summary.llm_calls)}</strong>
                    <Trend daily={daily} field="calls" color="#23a37a" />
                  </article>
                </section>
                <section className="usage-cost-breakdown">
                  <CostBars
                    title="Cost by agent"
                    rows={agentCosts}
                    labelKey="agent_name"
                  />
                  <CostBars
                    title="Cost by model"
                    rows={modelCosts}
                    labelKey="model"
                  />
                </section>
                <section className="usage-breakdown">
                  <header>
                    <div>
                      <span className="section-eyebrow">Usage breakdown</span>
                      <h2>Accounting dimensions</h2>
                    </div>
                    <div className="usage-tabs">
                      {tabs.map((x) => (
                        <button
                          className={tab === x ? "active" : ""}
                          onClick={() => setTab(x)}
                          key={x}
                        >
                          {x}s
                        </button>
                      ))}
                    </div>
                  </header>
                  <Table tab={tab} rows={rows} />
                </section>
              </div>
            )}
          </>
        )}
      </AsyncState>
    </main>
  );
}
