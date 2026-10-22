"use client";

import { useEffect, useState } from "react";

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

type Metrics = {
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

type DashboardOverview = {
  metrics: Metrics;
  activity: Activity[];
};

type ApprovalRequest = {
  id: number;
  merchant_id: number;
  order_id: number;
  status: string;
  requested_at: string;
  expires_at: string | null;
  decided_at: string | null;
  decided_by_user_id: number | null;
  decision_reason: string | null;
};

type ExecutionSummary = {
  id: number;
  session_id: string;
  correlation_id: string;
  intent: string | null;
  status: string;
  created_at: string | null;
  completed_at: string | null;
  total_latency_ms: number | null;
  tool_calls_count: number;
};

type TraceToolCall = {
  id: number;
  tool_name: string;
  input_data: any;
  output_data: any;
  status: string;
  latency_ms: number;
  policy_result: string | null;
  created_at: string | null;
};

type ExecutionTrace = {
  execution_id: number;
  merchant_id: number;
  session_id: string;
  correlation_id: string;
  intent: string | null;
  status: string;
  created_at: string | null;
  completed_at: string | null;
  total_latency_ms: number | null;
  tool_calls_count: number;
  tool_calls: TraceToolCall[];
};

const API = "http://127.0.0.1:8000";
const ACCESS_TOKEN_KEY = "razorgrow_access_token";

function money(value: number) {
  return `₹${value.toLocaleString("en-IN")}`;
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");

  const [dashboard, setDashboard] =
    useState<DashboardOverview | null>(null);

  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);

  const [approvalsLoading, setApprovalsLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [dashboardLoading, setDashboardLoading] = useState(true);

  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Agent Observability & Trace states
  const [executions, setExecutions] = useState<ExecutionSummary[]>([]);
  const [executionsLoading, setExecutionsLoading] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState<ExecutionTrace | null>(null);
  const [traceLoading, setTraceLoading] = useState(false);

  // AI Agent live chat simulation
  const [chatMessage, setChatMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatReply, setChatReply] = useState<any | null>(null);

  // IMPORTANT:
  // Keep the actual token in React state instead of repeatedly
  // reading localStorage inside different effects.
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const [loggedIn, setLoggedIn] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  /*
   * Restore authentication after a page refresh.
   *
   * We do NOT read localStorage inside useState because that can cause
   * a Next.js hydration mismatch.
   */
  useEffect(() => {
    const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);

    if (token) {
      setAccessToken(token);
      setLoggedIn(true);
    } else {
      setAccessToken(null);
      setLoggedIn(false);
    }

    setAuthChecked(true);
  }, []);

  /*
   * Load dashboard data only after authentication has been checked
   * AND a real access token exists.
   */
  useEffect(() => {
    if (!authChecked || !accessToken || !loggedIn) {
      return;
    }

    const token = accessToken;

    console.log(
      "Dashboard auth token present:",
      token ? `${token.slice(0, 10)}...` : "NO TOKEN",
    );

    const authHeaders = {
      Authorization: `Bearer ${token}`,
    };

    setLoading(true);
    setDashboardLoading(true);
    setApprovalsLoading(true);
    setError("");

    Promise.all([
      fetch(`${API}/products`, {
        headers: authHeaders,
      }).then(async (response) => {
        if (!response.ok) {
          const body = await response.text();

          console.error(
            "Products API failed:",
            response.status,
            body,
          );

          throw new Error(
            `Products API failed: ${response.status}`,
          );
        }

        return response.json();
      }),

      fetch(`${API}/dashboard/overview?limit=10`, {
        headers: authHeaders,
      }).then(async (response) => {
        if (!response.ok) {
          const body = await response.text();

          console.error(
            "Dashboard API failed:",
            response.status,
            body,
          );

          /*
           * If the backend rejects the token, stop treating the
           * browser as authenticated.
           */
          if (response.status === 401) {
            window.localStorage.removeItem(
              ACCESS_TOKEN_KEY,
            );

            setAccessToken(null);
            setLoggedIn(false);
          }

          throw new Error(
            `Dashboard API failed: ${response.status}`,
          );
        }

        return response.json();
      }),

      fetch(`${API}/approvals`, {
        headers: authHeaders,
      }).then(async (response) => {
        if (!response.ok) {
          const body = await response.text();

          console.error(
            "Approvals API failed:",
            response.status,
            body,
          );

          if (response.status === 401) {
            window.localStorage.removeItem(
              ACCESS_TOKEN_KEY,
            );

            setAccessToken(null);
            setLoggedIn(false);
          }

          throw new Error(
            `Approvals API failed: ${response.status}`,
          );
        }

        return response.json();
      }),
    ])
      .then(
        ([
          productData,
          dashboardData,
          approvalData,
        ]) => {
          setProducts(productData);
          setDashboard(dashboardData);
          setApprovals(approvalData);
          loadExecutions(token);
        },
      )
      .catch((err) => {
        console.error("RazorGrow data loading error:", err);

        /*
         * Don't overwrite the login state error when a 401
         * has already moved us back to the login screen.
         */
        if (
          window.localStorage.getItem(
            ACCESS_TOKEN_KEY,
          )
        ) {
          setError(
            "Could not connect to the RazorGrow backend.",
          );
        }
      })
      .finally(() => {
        setLoading(false);
        setDashboardLoading(false);
        setApprovalsLoading(false);
      });
  }, [authChecked, accessToken, loggedIn]);

  const loadExecutions = async (tokenToUse?: string) => {
    const token = tokenToUse || accessToken;
    if (!token) return;
    setExecutionsLoading(true);
    try {
      const response = await fetch(`${API}/agent/executions?limit=15`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setExecutions(data);
      }
    } catch (err) {
      console.error("Failed to load executions:", err);
    } finally {
      setExecutionsLoading(false);
    }
  };

  const viewTrace = async (id: number) => {
    if (!accessToken) return;
    setTraceLoading(true);
    try {
      const response = await fetch(`${API}/agent/executions/${id}/trace`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.ok) {
        const trace = await response.json();
        setSelectedTrace(trace);
      }
    } catch (err) {
      console.error("Failed to fetch execution trace:", err);
    } finally {
      setTraceLoading(false);
    }
  };

  const sendAgentChat = async (promptText?: string) => {
    const prompt = promptText || chatMessage;
    if (!prompt.trim() || !accessToken) return;
    setChatLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/agent/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ message: prompt }),
      });
      if (!response.ok) {
        throw new Error(`Agent chat failed: ${response.status}`);
      }
      const data = await response.json();
      setChatReply(data);
      setChatMessage("");
      loadExecutions();
      if (data.execution_id) {
        viewTrace(data.execution_id);
      }
    } catch (err) {
      console.error(err);
      setError("Agent interaction failed.");
    } finally {
      setChatLoading(false);
    }
  };

  const filteredProducts = products.filter(
    (product) => {
      const query = search.toLowerCase().trim();

      if (!query) {
        return true;
      }

      return (
        product.name.toLowerCase().includes(query) ||
        product.category.toLowerCase().includes(query) ||
        product.tags.some((tag) =>
          tag.toLowerCase().includes(query),
        ) ||
        product.use_cases.some((useCase) =>
          useCase.toLowerCase().includes(query),
        )
      );
    },
  );

  /*
   * Prevent hydration mismatch.
   */
  if (!authChecked) {
    return null;
  }

  /*
   * Login screen.
   */
  if (!loggedIn) {
    return (
      <main style={styles.page}>
        <section style={styles.loginCard}>
          <div style={styles.brand}>RazorGrow</div>

          <p style={styles.subtitle}>
            Sign in to access the merchant dashboard.
          </p>

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            style={styles.search}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            style={styles.search}
          />

          <button
            type="button"
            disabled={loginLoading}
            onClick={async () => {
              setLoginLoading(true);
              setError("");

              try {
                const response = await fetch(
                  `${API}/auth/login`,
                  {
                    method: "POST",
                    headers: {
                      "Content-Type":
                        "application/json",
                    },
                    body: JSON.stringify({
                      email,
                      password,
                    }),
                  },
                );

                if (!response.ok) {
                  const body =
                    await response.text();

                  console.error(
                    "Login API failed:",
                    response.status,
                    body,
                  );

                  throw new Error(
                    `Login failed: ${response.status}`,
                  );
                }

                const data =
                  await response.json();

                const token =
                  data.access_token;

                if (!token) {
                  throw new Error(
                    "Login response did not contain an access token",
                  );
                }

                /*
                 * Store the token first.
                 */
                window.localStorage.setItem(
                  ACCESS_TOKEN_KEY,
                  token,
                );

                /*
                 * Then update React state.
                 * This causes the authenticated data
                 * loading effect to run.
                 */
                setAccessToken(token);
                setLoggedIn(true);
              } catch (err) {
                console.error(err);

                setError(
                  "Invalid email or password.",
                );
              } finally {
                setLoginLoading(false);
              }
            }}
            style={styles.button}
          >
            {loginLoading
              ? "Signing in..."
              : "Sign in"}
          </button>

          {error && (
            <div style={styles.error}>
              {error}
            </div>
          )}
        </section>
      </main>
    );
  }

  /*
   * Loading state.
   */
  if (loading) {
    return (
      <main style={styles.page}>
        <p>Loading RazorGrow...</p>
      </main>
    );
  }

  /*
   * Error state.
   */
  if (error) {
    return (
      <main style={styles.page}>
        <div style={styles.error}>
          {error}
        </div>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      {/* Header */}
      <header style={styles.header}>
        <div>
          <div style={styles.brand}>
            RazorGrow
          </div>

          <div style={styles.subtitle}>
            Autonomous AI Revenue Agent
          </div>
        </div>

        <div style={styles.status}>
          <span style={styles.statusDot}></span>
          System operational
        </div>
      </header>

      {/* Dashboard */}
      <section style={styles.dashboard}>
        <div style={styles.sectionHeader}>
          <div>
            <h1 style={styles.title}>
              Merchant Dashboard
            </h1>

            <p style={styles.muted}>
              Revenue intelligence, payment recovery
              and agent activity
            </p>
          </div>
        </div>

        {dashboardLoading ? (
          <p>Loading metrics...</p>
        ) : dashboard ? (
          <>
            <div style={styles.metricsGrid}>
              <MetricCard
                label="Revenue"
                value={money(
                  dashboard.metrics.revenue,
                )}
              />

              <MetricCard
                label="Recovered Revenue"
                value={money(
                  dashboard.metrics
                    .recovered_revenue,
                )}
              />

              <MetricCard
                label="Average Order"
                value={money(
                  dashboard.metrics
                    .average_order_value,
                )}
              />

              <MetricCard
                label="Payment Conversion"
                value={`${dashboard.metrics.payment_conversion_rate}%`}
              />
            </div>

            <div style={styles.secondaryGrid}>
              <MetricCard
                label="Total Orders"
                value={dashboard.metrics.total_orders.toString()}
              />

              <MetricCard
                label="Successful Payments"
                value={dashboard.metrics.successful_payments.toString()}
              />

              <MetricCard
                label="Recovered Payments"
                value={dashboard.metrics.recovered_payments.toString()}
              />

              <MetricCard
                label="Policy Blocks"
                value={dashboard.metrics.policy_blocks.toString()}
              />
            </div>

            {/* Agent Activity */}
            <div style={styles.activityCard}>
              <div style={styles.activityHeader}>
                <div>
                  <h2 style={styles.cardTitle}>
                    Agent Activity
                  </h2>

                  <p style={styles.muted}>
                    Recent autonomous decisions and
                    payment events
                  </p>
                </div>

                <span style={styles.liveBadge}>
                  LIVE DATA
                </span>
              </div>

              {dashboard.activity.map(
                (activity) => (
                  <div
                    key={activity.id}
                    style={styles.activityRow}
                  >
                    <div
                      style={styles.activityMain}
                    >
                      <strong>
                        {formatAction(
                          activity.action,
                        )}
                      </strong>

                      <span
                        style={styles.entity}
                      >
                        Entity #
                        {activity.entity_id}
                      </span>
                    </div>

                    <div
                      style={
                        styles.activityResult
                      }
                    >
                      {activity.policy_result && (
                        <span
                          style={
                            styles.approved
                          }
                        >
                          {
                            activity.policy_result
                          }
                        </span>
                      )}

                      {activity.external_result && (
                        <span
                          style={
                            styles.external
                          }
                        >
                          {
                            activity.external_result
                          }
                        </span>
                      )}

                      {activity.recovery && (
                        <span
                          style={
                            styles.recovery
                          }
                        >
                          {activity.recovery}
                        </span>
                      )}

                      {activity.error && (
                        <span
                          style={styles.failed}
                        >
                          {activity.error}
                        </span>
                      )}
                    </div>
                  </div>
                ),
              )}
            </div>
          </>
        ) : null}
      </section>

      {/* Approval Center */}
      <section style={styles.catalog}>
        <div>
          <h2 style={styles.title}>
            Approval Center
          </h2>

          <p style={styles.muted}>
            Review and manage merchant approval
            requests.
          </p>
        </div>

        {approvalsLoading ? (
          <p>Loading approvals...</p>
        ) : approvals.length === 0 ? (
          <div style={styles.activityCard}>
            <div style={styles.activityRow}>
              <span>
                No approval requests.
              </span>
            </div>
          </div>
        ) : (
          <div style={styles.activityCard}>
            {approvals.map((approval) => (
              <div
                key={approval.id}
                style={styles.activityRow}
              >
                <div
                  style={styles.activityMain}
                >
                  <strong>
                    Approval #{approval.id}
                  </strong>

                  <span
                    style={styles.entity}
                  >
                    Order #{approval.order_id}
                  </span>

                  <span
                    style={styles.entity}
                  >
                    Status: {approval.status}
                  </span>
                </div>

                {approval.status ===
                  "PENDING" && (
                  <div
                    style={
                      styles.approvalActions
                    }
                  >
                    <button
                      type="button"
                      style={styles.button}
                      onClick={async () => {
                        setError("");

                        try {
                          const response =
                            await fetch(
                              `${API}/approvals/${approval.id}/approve`,
                              {
                                method: "POST",
                                headers: {
                                  "Content-Type":
                                    "application/json",
                                  Authorization: `Bearer ${accessToken ?? ""}`,
                                },
                                body: JSON.stringify(
                                  {},
                                ),
                              },
                            );

                          if (!response.ok) {
                            const body =
                              await response.text();

                            console.error(
                              "Approval failed:",
                              response.status,
                              body,
                            );

                            throw new Error(
                              "Approval failed",
                            );
                          }

                          const updated =
                            await response.json();

                          setApprovals(
                            (current) =>
                              current.map(
                                (item) =>
                                  item.id ===
                                  updated.id
                                    ? updated
                                    : item,
                              ),
                          );
                        } catch (err) {
                          console.error(err);

                          setError(
                            "Could not approve the request.",
                          );
                        }
                      }}
                    >
                      Approve
                    </button>

                    <button
                      type="button"
                      style={styles.button}
                      onClick={async () => {
                        setError("");

                        try {
                          const response =
                            await fetch(
                              `${API}/approvals/${approval.id}/reject`,
                              {
                                method: "POST",
                                headers: {
                                  "Content-Type":
                                    "application/json",
                                  Authorization: `Bearer ${accessToken ?? ""}`,
                                },
                                body: JSON.stringify(
                                  {},
                                ),
                              },
                            );

                          if (!response.ok) {
                            const body =
                              await response.text();

                            console.error(
                              "Rejection failed:",
                              response.status,
                              body,
                            );

                            throw new Error(
                              "Rejection failed",
                            );
                          }

                          const updated =
                            await response.json();

                          setApprovals(
                            (current) =>
                              current.map(
                                (item) =>
                                  item.id ===
                                  updated.id
                                    ? updated
                                    : item,
                              ),
                          );
                        } catch (err) {
                          console.error(err);

                          setError(
                            "Could not reject the request.",
                          );
                        }
                      }}
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Agent Observability & Trace Reconstructor */}
      <section style={styles.catalog}>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={styles.title}>Agent Observability & Live Traces</h2>
              <p style={styles.muted}>
                Interact with the AI Revenue Agent, inspect tool call pipelines, and verify explainable execution traces.
              </p>
            </div>
            <button
              type="button"
              style={{ ...styles.button, background: "#f3f4f6", marginTop: 0 }}
              onClick={() => loadExecutions()}
            >
              Refresh Traces
            </button>
          </div>
        </div>

        {/* Live Conversation Tester */}
        <div style={styles.activityCard}>
          <div style={styles.activityHeader}>
            <div>
              <h3 style={styles.cardTitle}>Live AI Revenue Agent Tester</h3>
              <p style={styles.muted}>
                Test shopping intent, grounded recommendations, and upsell generation in real-time.
              </p>
            </div>
            <span style={styles.liveBadge}>INTERACTIVE</span>
          </div>

          <div style={{ padding: 20 }}>
            {/* Sample Prompts */}
            <div style={{ marginBottom: 14, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 13, color: "#6b7280", fontWeight: 600 }}>Try scenario:</span>
              {[
                "I need a laptop for programming under ₹70,000",
                "Suggest a keyboard under ₹5,000",
                "I want a wireless mouse under ₹2,000",
              ].map((sample) => (
                <button
                  key={sample}
                  type="button"
                  style={{
                    padding: "6px 12px",
                    borderRadius: 999,
                    border: "1px solid #d1d5db",
                    background: "#f9fafb",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    setChatMessage(sample);
                    sendAgentChat(sample);
                  }}
                >
                  "{sample}"
                </button>
              ))}
            </div>

            {/* Input bar */}
            <div style={{ display: "flex", gap: 10 }}>
              <input
                type="text"
                placeholder="Ask the revenue agent (e.g. 'Laptop for coding under ₹70,000')..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    sendAgentChat();
                  }
                }}
                style={{ ...styles.search, margin: 0, flex: 1 }}
              />
              <button
                type="button"
                disabled={chatLoading}
                onClick={() => sendAgentChat()}
                style={{
                  ...styles.button,
                  background: "#0f172a",
                  color: "#fff",
                  padding: "0 24px",
                  marginTop: 0,
                }}
              >
                {chatLoading ? "Thinking..." : "Send to Agent"}
              </button>
            </div>

            {/* Agent Reply Box */}
            {chatReply && (
              <div
                style={{
                  marginTop: 18,
                  padding: 16,
                  borderRadius: 10,
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontWeight: 700, color: "#1e293b", fontSize: 14 }}>
                    Agent Response
                  </span>
                  <span style={{ fontSize: 12, color: "#64748b" }}>
                    Latency: {chatReply.total_latency_ms.toFixed(1)} ms | Execution #{chatReply.execution_id}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: "#334155" }}>
                  {chatReply.reply}
                </p>

                {chatReply.recommended_product && (
                  <div
                    style={{
                      marginTop: 12,
                      display: "flex",
                      gap: 16,
                      background: "#fff",
                      padding: 12,
                      borderRadius: 8,
                      border: "1px solid #cbd5e1",
                    }}
                  >
                    <div>
                      <span style={{ fontSize: 11, textTransform: "uppercase", color: "#64748b", fontWeight: 700 }}>
                        Grounded Recommendation
                      </span>
                      <div style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>
                        {chatReply.recommended_product.name}
                      </div>
                      <div style={{ color: "#059669", fontWeight: 800 }}>
                        {money(chatReply.recommended_product.price)}
                      </div>
                    </div>

                    {chatReply.upsell_product && (
                      <div style={{ borderLeft: "1px solid #e2e8f0", paddingLeft: 16 }}>
                        <span style={{ fontSize: 11, textTransform: "uppercase", color: "#2563eb", fontWeight: 700 }}>
                          Compatible Upsell
                        </span>
                        <div style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>
                          {chatReply.upsell_product.name}
                        </div>
                        <div style={{ color: "#2563eb", fontWeight: 800 }}>
                          +{money(chatReply.upsell_product.price)}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Selected Trace Details (Trace Reconstructor) */}
        {selectedTrace && (
          <div style={{ ...styles.activityCard, borderColor: "#3b82f6", boxShadow: "0 4px 12px rgba(59,130,246,0.1)" }}>
            <div style={{ ...styles.activityHeader, background: "#eff6ff" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <h3 style={{ ...styles.cardTitle, color: "#1e40af" }}>
                    Execution Trace #{selectedTrace.execution_id}
                  </h3>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: 999,
                      background: selectedTrace.status === "completed" ? "#dcfce7" : "#fee2e2",
                      color: selectedTrace.status === "completed" ? "#166534" : "#991b1b",
                    }}
                  >
                    {selectedTrace.status.toUpperCase()}
                  </span>
                </div>
                <p style={{ ...styles.muted, color: "#3b82f6" }}>
                  Correlation ID: {selectedTrace.correlation_id} | Total Latency: {selectedTrace.total_latency_ms?.toFixed(1) || 0} ms | Tool Calls: {selectedTrace.tool_calls_count}
                </p>
              </div>
              <button
                type="button"
                style={{ ...styles.button, marginTop: 0 }}
                onClick={() => setSelectedTrace(null)}
              >
                Close Trace
              </button>
            </div>

            <div style={{ padding: 20 }}>
              <div style={{ marginBottom: 16 }}>
                <strong>User Intent:</strong>{" "}
                <span style={{ color: "#334155" }}>"{selectedTrace.intent || "N/A"}"</span>
              </div>

              <h4 style={{ margin: "0 0 12px", fontSize: 14, color: "#475569", textTransform: "uppercase" }}>
                Reconstructed Tool Call Pipeline:
              </h4>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {selectedTrace.tool_calls.map((call, idx) => (
                  <div
                    key={call.id}
                    style={{
                      border: "1px solid #e2e8f0",
                      borderRadius: 8,
                      padding: 14,
                      background: "#fafafa",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span
                          style={{
                            background: "#0f172a",
                            color: "#fff",
                            fontSize: 11,
                            fontWeight: 700,
                            borderRadius: 4,
                            padding: "2px 6px",
                          }}
                        >
                          Step {idx + 1}
                        </span>
                        <strong style={{ fontSize: 15 }}>{call.tool_name}</strong>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12 }}>
                        <span style={{ color: "#64748b" }}>{call.latency_ms.toFixed(1)} ms</span>
                        <span
                          style={{
                            color: call.status === "success" ? "#059669" : "#dc2626",
                            fontWeight: 700,
                          }}
                        >
                          {call.status.toUpperCase()}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <div>
                        <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600, marginBottom: 4 }}>
                          SANITIZED INPUT:
                        </div>
                        <pre
                          style={{
                            margin: 0,
                            padding: 8,
                            borderRadius: 6,
                            background: "#f1f5f9",
                            fontSize: 12,
                            maxHeight: 120,
                            overflowY: "auto",
                          }}
                        >
                          {JSON.stringify(call.input_data, null, 2)}
                        </pre>
                      </div>

                      <div>
                        <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600, marginBottom: 4 }}>
                          OUTPUT / RESULT:
                        </div>
                        <pre
                          style={{
                            margin: 0,
                            padding: 8,
                            borderRadius: 6,
                            background: "#f1f5f9",
                            fontSize: 12,
                            maxHeight: 120,
                            overflowY: "auto",
                          }}
                        >
                          {JSON.stringify(call.output_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Recent Executions Table */}
        <div style={styles.activityCard}>
          <div style={styles.activityHeader}>
            <div>
              <h3 style={styles.cardTitle}>Recent Agent Executions</h3>
              <p style={styles.muted}>
                Historical trace records for audit and compliance inspection.
              </p>
            </div>
            {executionsLoading && <span style={styles.muted}>Loading...</span>}
          </div>

          {executions.length === 0 ? (
            <div style={styles.activityRow}>
              <span>No agent executions recorded yet. Try a scenario above!</span>
            </div>
          ) : (
            executions.map((exec) => (
              <div key={exec.id} style={styles.activityRow}>
                <div style={styles.activityMain}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <strong>Execution #{exec.id}</strong>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 6px",
                        borderRadius: 999,
                        background: exec.status === "completed" ? "#ecfdf5" : "#fef2f2",
                        color: exec.status === "completed" ? "#047857" : "#b91c1c",
                        fontWeight: 700,
                      }}
                    >
                      {exec.status.toUpperCase()}
                    </span>
                  </div>
                  <span style={styles.entity}>
                    "{exec.intent ? (exec.intent.length > 50 ? exec.intent.slice(0, 50) + "..." : exec.intent) : "N/A"}"
                  </span>
                  <span style={{ fontSize: 12, color: "#64748b" }}>
                    Correlation: {exec.correlation_id}
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <span style={{ fontSize: 13, color: "#64748b" }}>
                    {exec.tool_calls_count} tools • {exec.total_latency_ms?.toFixed(1) || 0} ms
                  </span>
                  <button
                    type="button"
                    style={{ ...styles.button, marginTop: 0, padding: "6px 12px", fontSize: 13 }}
                    onClick={() => viewTrace(exec.id)}
                  >
                    Inspect Trace
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Product Catalog */}
      <section style={styles.catalog}>
        <div>
          <h2 style={styles.title}>
            Merchant Catalog
          </h2>

          <p style={styles.muted}>
            Discover products and demonstrate the
            revenue-agent flow.
          </p>
        </div>

        <input
          type="text"
          placeholder="Search products..."
          value={search}
          onChange={(event) =>
            setSearch(event.target.value)
          }
          style={styles.search}
        />

        <div style={styles.productGrid}>
          {filteredProducts.map((product) => (
            <article
              key={product.id}
              style={styles.productCard}
            >
              <div style={styles.productTop}>
                <span
                  style={styles.category}
                >
                  {product.category}
                </span>

                <span
                  style={styles.inventory}
                >
                  Stock: {product.inventory}
                </span>
              </div>

              <h3
                style={styles.productName}
              >
                {product.name}
              </h3>

              <p style={styles.price}>
                {money(product.price)}
              </p>

              <p
                style={styles.productInfo}
              >
                <strong>
                  Use cases:
                </strong>{" "}
                {product.use_cases.join(
                  ", ",
                )}
              </p>

              <p
                style={styles.productInfo}
              >
                <strong>Tags:</strong>{" "}
                {product.tags.join(", ")}
              </p>

              <button
                onClick={async () => {
                  try {
                    const response =
                      await fetch(
                        `${API}/products/${product.id}`,
                        {
                          headers: {
                            Authorization: `Bearer ${accessToken ?? ""}`,
                          },
                        },
                      );

                    if (!response.ok) {
                      alert(
                        "Could not load product details.",
                      );
                      return;
                    }

                    const details =
                      await response.json();

                    alert(
                      `${details.name}\n\n` +
                        `Price: ${money(
                          details.price,
                        )}\n` +
                        `Category: ${details.category}\n` +
                        `Inventory: ${details.inventory}`,
                    );
                  } catch (err) {
                    console.error(err);

                    alert(
                      "Could not load product details.",
                    );
                  }
                }}
                style={styles.button}
              >
                View details
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={styles.metricCard}>
      <div style={styles.metricLabel}>
        {label}
      </div>

      <div style={styles.metricValue}>
        {value}
      </div>
    </div>
  );
}

function formatAction(action: string) {
  return action
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

const styles: Record<
  string,
  React.CSSProperties
> = {
  page: {
    minHeight: "100vh",
    padding: "32px",
    background: "#f7f8fa",
    color: "#171717",
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
  },

  header: {
    maxWidth: 1200,
    margin: "0 auto 32px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  brand: {
    fontSize: 28,
    fontWeight: 800,
  },

  subtitle: {
    marginTop: 4,
    color: "#666",
    fontSize: 14,
  },

  status: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 12px",
    borderRadius: 999,
    background: "#fff",
    border: "1px solid #ddd",
    fontSize: 13,
    fontWeight: 600,
  },

  statusDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "#16a34a",
  },

  dashboard: {
    maxWidth: 1200,
    margin: "0 auto",
  },

  sectionHeader: {
    marginBottom: 24,
  },

  title: {
    margin: 0,
    fontSize: 24,
    fontWeight: 750,
  },

  muted: {
    marginTop: 6,
    color: "#6b7280",
    fontSize: 14,
  },

  metricsGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 16,
  },

  secondaryGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(180px, 1fr))",
    gap: 16,
    marginTop: 16,
  },

  metricCard: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 14,
    padding: 20,
    boxShadow:
      "0 1px 2px rgba(0,0,0,0.04)",
  },

  metricLabel: {
    color: "#6b7280",
    fontSize: 13,
    fontWeight: 600,
  },

  metricValue: {
    marginTop: 8,
    fontSize: 25,
    fontWeight: 800,
  },

  activityCard: {
    marginTop: 24,
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 14,
    overflow: "hidden",
  },

  activityHeader: {
    padding: 20,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #eee",
  },

  cardTitle: {
    margin: 0,
    fontSize: 18,
  },

  liveBadge: {
    fontSize: 11,
    fontWeight: 800,
    padding: "6px 9px",
    borderRadius: 999,
    background: "#ecfdf5",
    color: "#047857",
  },

  activityRow: {
    padding: "15px 20px",
    borderBottom: "1px solid #f0f0f0",
    display: "flex",
    justifyContent: "space-between",
    gap: 20,
    flexWrap: "wrap",
  },

  activityMain: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },

  entity: {
    color: "#888",
    fontSize: 12,
  },

  activityResult: {
    display: "flex",
    gap: 7,
    alignItems: "center",
    flexWrap: "wrap",
  },

  approved: {
    padding: "5px 8px",
    borderRadius: 6,
    background: "#ecfdf5",
    color: "#047857",
    fontSize: 11,
    fontWeight: 700,
  },

  external: {
    padding: "5px 8px",
    borderRadius: 6,
    background: "#eff6ff",
    color: "#1d4ed8",
    fontSize: 11,
    fontWeight: 700,
  },

  recovery: {
    padding: "5px 8px",
    borderRadius: 6,
    background: "#fff7ed",
    color: "#c2410c",
    fontSize: 11,
    fontWeight: 700,
  },

  failed: {
    padding: "5px 8px",
    borderRadius: 6,
    background: "#fef2f2",
    color: "#b91c1c",
    fontSize: 11,
    fontWeight: 700,
  },

  catalog: {
    maxWidth: 1200,
    margin: "48px auto 0",
  },

  search: {
    width: "100%",
    boxSizing: "border-box",
    padding: 14,
    marginTop: 20,
    border: "1px solid #d1d5db",
    borderRadius: 10,
    background: "#fff",
    fontSize: 15,
  },

  productGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(280px, 1fr))",
    gap: 20,
    marginTop: 24,
  },

  productCard: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 14,
    padding: 20,
  },

  productTop: {
    display: "flex",
    justifyContent: "space-between",
    gap: 10,
  },

  category: {
    fontSize: 11,
    fontWeight: 700,
    textTransform: "uppercase",
    color: "#6b7280",
  },

  inventory: {
    fontSize: 11,
    color: "#6b7280",
  },

  productName: {
    margin: "14px 0 4px",
    fontSize: 19,
  },

  price: {
    margin: 0,
    fontSize: 20,
    fontWeight: 800,
  },

  productInfo: {
    color: "#555",
    fontSize: 13,
    lineHeight: 1.5,
  },

  button: {
    marginTop: 10,
    padding: "10px 14px",
    borderRadius: 8,
    border: "1px solid #ccc",
    background: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  },

  error: {
    padding: 20,
    background: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: 10,
    color: "#b91c1c",
  },

  loginCard: {
    maxWidth: 420,
    margin: "80px auto",
    padding: 28,
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 14,
    boxShadow:
      "0 4px 12px rgba(0,0,0,0.05)",
  },

  approvalActions: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  },
};