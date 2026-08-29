"use client";
import { useEffect, useMemo, useState } from "react";

type Product = {
  id: number;
  name: string;
  price: number;
  category: string;
  tags: string[];
  use_cases: string[];
  compatible_products: number[];
  upsell_products: number[];
  inventory: number;
};

type DashboardMetrics = {
  total_orders: number;
  created_orders: number;
  successful_payments: number;
  failed_payments: number;
  recovered_payments: number;
  revenue: number;
  recovered_revenue: number;
  average_order_value: number;
  payment_conversion_rate: number;
  policy_blocks: number;
};

type Activity = {
  id: number;
  action: string;
  entity_id: string;
  policy_result: string | null;
  external_result: string | null;
  error: string | null;
  recovery: string | null;
};

type Status = "success" | "warning" | "danger" | "neutral";

function activityStatus(event: Activity): Status {
  if (event.error) return "danger";
  if (event.recovery) return "warning";
  if (event.external_result?.toLowerCase().includes("fail")) return "danger";
  if (event.external_result?.toLowerCase().includes("success")) return "success";
  if (event.policy_result?.toLowerCase().includes("block")) return "danger";
  return "neutral";
}

const statusDot: Record<Status, string> = {
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  neutral: "bg-accent",
};

const statusBorder: Record<Status, string> = {
  success: "border-l-success",
  warning: "border-l-warning",
  danger: "border-l-danger",
  neutral: "border-l-accent",
};

function inr(value: number) {
  return `₹${value.toLocaleString("en-IN")}`;
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activity, setActivity] = useState<Activity[]>([]);
  const [now, setNow] = useState<string>("");

 useEffect(() => {
  const loadProducts = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/products");
      if (!response.ok) throw new Error("Failed to load products");

      const data = await response.json();
      setProducts(data);
    } catch (err) {
      console.error(err);
      setError("Could not connect to the RazorGrow backend.");
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/dashboard/overview");
      if (!response.ok) throw new Error("Failed to load dashboard");

      const data = await response.json();
      setMetrics(data.metrics);
      setActivity(data.activity);
    } catch (err) {
      console.error(err);
    } finally {
      setDashboardLoading(false);
    }
  };

  loadProducts();
  loadDashboard();
}, []);

useEffect(() => {
  const updateTime = () => {
    setNow(
      new Date().toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
      })
    );
  };

  updateTime();

  const interval = setInterval(updateTime, 60_000);

  return () => clearInterval(interval);
}, []);

  const filteredProducts = useMemo(() => {
    const query = search.toLowerCase().trim();
    if (!query) return products;
    return products.filter(
      (product) =>
        product.name.toLowerCase().includes(query) ||
        product.category.toLowerCase().includes(query) ||
        product.tags.some((tag) => tag.toLowerCase().includes(query)) ||
        product.use_cases.some((useCase) => useCase.toLowerCase().includes(query))
    );
  }, [products, search]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-bg text-text-dim font-mono text-sm">
        <span className="w-1.5 h-1.5 rounded-full bg-accent pulse-dot mr-3" />
        booting agent console…
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-bg px-6">
        <div className="border border-danger/40 bg-danger-soft rounded-xl px-6 py-5 text-danger font-mono text-sm max-w-md text-center">
          {error}
        </div>
      </main>
    );
  }

  const metricCards = metrics
    ? [
        { label: "Revenue", value: inr(metrics.revenue), tone: "text-text" },
        { label: "Recovered Revenue", value: inr(metrics.recovered_revenue), tone: "text-success" },
        { label: "Avg. Order Value", value: inr(metrics.average_order_value), tone: "text-text" },
        { label: "Payment Conversion", value: `${metrics.payment_conversion_rate}%`, tone: "text-accent" },
      ]
    : [];

  return (
    <main className="min-h-screen bg-bg text-text font-sans px-6 py-10 md:px-12 md:py-14">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-10 rise-in">
          <div>
            <p className="font-mono text-xs tracking-widest text-accent uppercase mb-2">
              RazorGrow · Autonomous Revenue Agent
            </p>
            <h1 className="font-display text-3xl md:text-4xl font-semibold tracking-tight">
              Merchant Console
            </h1>
            <p className="text-text-dim mt-1.5 text-sm">
              Payment recovery, policy checks, and catalog intelligence — running on Razorpay.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto border border-success/30 bg-success-soft rounded-full px-3.5 py-1.5 font-mono text-xs text-success">
            <span className="w-1.5 h-1.5 rounded-full bg-success pulse-dot" />
            AGENT OPERATIONAL{now ? ` · ${now} IST` : ""}
          </div>
        </header>

        {/* Metrics ledger strip */}
        <section className="mb-12 rise-in" style={{ animationDelay: "60ms" }}>
          {dashboardLoading ? (
            <p className="text-text-dim font-mono text-sm">reading ledger…</p>
          ) : metrics ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-border rounded-xl overflow-hidden border border-border">
              {metricCards.map((card) => (
                <div key={card.label} className="bg-surface px-5 py-5">
                  <p className="text-xs uppercase tracking-wider text-text-dim">{card.label}</p>
                  <p className={`font-mono text-2xl md:text-[26px] font-semibold mt-2 ${card.tone}`}>
                    {card.value}
                  </p>
                </div>
              ))}
              <div className="bg-surface px-5 py-5 col-span-2 lg:col-span-4 flex flex-wrap gap-x-8 gap-y-2 border-t border-border">
                <span className="font-mono text-xs text-text-dim">
                  Orders <span className="text-text">{metrics.total_orders}</span>
                </span>
                <span className="font-mono text-xs text-text-dim">
                  Successful <span className="text-success">{metrics.successful_payments}</span>
                </span>
                <span className="font-mono text-xs text-text-dim">
                  Failed <span className="text-danger">{metrics.failed_payments}</span>
                </span>
                <span className="font-mono text-xs text-text-dim">
                  Recovered <span className="text-warning">{metrics.recovered_payments}</span>
                </span>
                <span className="font-mono text-xs text-text-dim">
                  Policy blocks <span className="text-text">{metrics.policy_blocks}</span>
                </span>
              </div>
            </div>
          ) : (
            <p className="text-text-dim font-mono text-sm">Dashboard unavailable.</p>
          )}
        </section>

        {/* Agent Activity — signature terminal ledger */}
        <section className="mb-14 rise-in" style={{ animationDelay: "120ms" }}>
          <div className="flex items-baseline justify-between mb-4">
            <div>
              <h2 className="font-display text-lg font-semibold">Agent Activity</h2>
              <p className="text-text-dim text-sm mt-0.5">
                Live decisions and payment recovery actions
              </p>
            </div>
            <span className="font-mono text-xs text-text-dim hidden md:inline">
              {activity.length} events
            </span>
          </div>

          <div className="border border-border rounded-xl bg-surface overflow-hidden">
            <div className="max-h-[420px] overflow-y-auto ledger-scroll divide-y divide-border">
              {activity.length === 0 ? (
                <p className="px-5 py-6 text-text-dim font-mono text-sm">
                  no agent activity found.
                </p>
              ) : (
                activity.map((event) => {
                  const status = activityStatus(event);
                  return (
                    <div
                      key={event.id}
                      className={`border-l-2 ${statusBorder[status]} px-5 py-3.5 hover:bg-surface-2/60 transition-colors`}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${statusDot[status]}`} />
                          <span className="font-mono text-sm text-text">{event.action}</span>
                          <span className="font-mono text-xs text-text-dim">
                            → {event.entity_id}
                          </span>
                        </div>
                        <span className="font-mono text-xs text-text-dim shrink-0">
                          #{String(event.id).padStart(4, "0")}
                        </span>
                      </div>

                      {(event.policy_result || event.external_result || event.recovery || event.error) && (
                        <div className="flex flex-wrap gap-x-5 gap-y-1 mt-1.5 pl-4 font-mono text-xs">
                          {event.policy_result && (
                            <span className="text-text-dim">
                              policy: <span className="text-text">{event.policy_result}</span>
                            </span>
                          )}
                          {event.external_result && (
                            <span className="text-text-dim">
                              result: <span className="text-text">{event.external_result}</span>
                            </span>
                          )}
                          {event.recovery && (
                            <span className="text-warning">recovery: {event.recovery}</span>
                          )}
                          {event.error && <span className="text-danger">error: {event.error}</span>}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </section>

        {/* Product Catalog */}
        <section className="rise-in" style={{ animationDelay: "180ms" }}>
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-5">
            <div>
              <h2 className="font-display text-lg font-semibold">Product Catalog</h2>
              <p className="text-text-dim text-sm mt-0.5">
                {filteredProducts.length} of {products.length} products
              </p>
            </div>

            <div className="relative w-full md:w-80">
              <input
                type="text"
                placeholder="Search name, category, tag…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="w-full bg-surface border border-border rounded-lg pl-4 pr-4 py-2.5 text-sm text-text placeholder:text-text-dim outline-none focus:border-accent focus:ring-2 focus:ring-accent/20 transition-shadow"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProducts.map((product) => (
              <article
                key={product.id}
                className="border border-border bg-surface rounded-xl p-5 flex flex-col hover:border-accent/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-display text-base font-semibold leading-snug">
                    {product.name}
                  </h3>
                  <span className="font-mono text-xs text-text-dim shrink-0 mt-1">
                    {product.category}
                  </span>
                </div>

                <p className="font-mono text-xl text-accent font-semibold mt-2">
                  {inr(product.price)}
                </p>

                <p className="text-xs text-text-dim mt-2">
                  {product.inventory > 0 ? (
                    <span className="text-success">{product.inventory} in stock</span>
                  ) : (
                    <span className="text-danger">out of stock</span>
                  )}
                </p>

                {product.use_cases.length > 0 && (
                  <p className="text-sm text-text-dim mt-3 leading-relaxed">
                    {product.use_cases.join(" · ")}
                  </p>
                )}

                {product.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {product.tags.map((tag) => (
                      <span
                        key={tag}
                        className="font-mono text-[11px] text-text-dim border border-border rounded-full px-2 py-0.5"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <button
                  onClick={async () => {
                    try {
                      const response = await fetch(
                        `http://127.0.0.1:8000/products/${product.id}`
                      );
                      if (!response.ok) {
                        alert("Could not load product details.");
                        return;
                      }
                      const details = await response.json();
                      alert(
                        `${details.name}\n\n` +
                          `Price: ${inr(details.price)}\n` +
                          `Category: ${details.category}\n` +
                          `Inventory: ${details.inventory}`
                      );
                    } catch (err) {
                      console.error(err);
                      alert("Could not connect to the RazorGrow backend.");
                    }
                  }}
                  className="mt-4 text-sm font-medium text-accent border border-accent/30 rounded-lg py-2 hover:bg-accent-soft transition-colors"
                >
                  View details
                </button>
              </article>
            ))}
          </div>

          {filteredProducts.length === 0 && (
            <p className="text-text-dim text-sm mt-10 text-center font-mono">
              no products match “{search}”.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}