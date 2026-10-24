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
  revenue?: number;
  total_revenue?: number;
  recovered_revenue: number;
  upsell_revenue?: number;
  ai_influenced_revenue?: number;
  average_order_value: number;
  payment_conversion_rate: number;
  payment_recovery_rate?: number;
  policy_blocks: number;
};

type Campaign = {
  id: number;
  title: string;
  description: string;
  bundle_config: {
    base_product_id: number;
    base_product_name: string;
    addon_product_id: number;
    addon_product_name: string;
    original_total: number;
    discounted_total: number;
    discount_percent: number;
  } | null;
  discount_percent: number;
  status: string;
  projected_impact: string;
  created_at: string | null;
  decided_at: string | null;
  decided_by_user_id: number | null;
};

type InsightsResponse = {
  insights: string[];
  recommendations: Array<{
    type: string;
    base_product: string;
    addon_product: string;
    regular_price: number;
    bundle_price: number;
    discount_percent: number;
  }>;
  campaign_proposal: {
    id: number;
    title: string;
    description: string;
    status: string;
    projected_impact: string;
    discount_percent: number;
  } | null;
};

type AICatalogPolicy = {
  currency: string;
  max_transaction_amount: number;
  max_discount_percent: number;
  merchant_approval_threshold: number | null;
  customer_confirmation_required: boolean;
  policy_version: number;
};

type AICatalogSummary = {
  total_items: number;
  categories: string[];
  in_stock_items: number;
};

type AICatalogItem = {
  id: number;
  name: string;
  price: number;
  currency: string;
  category: string;
  tags: string[];
  use_cases: string[];
  availability: string;
  inventory: number;
  compatibility: Array<{
    product_id: number;
    name: string;
    price: number;
    category: string;
    in_stock: boolean;
  }>;
  upsell_suggestions: Array<{
    product_id: number;
    name: string;
    price: number;
    category: string;
    in_stock: boolean;
  }>;
  purchase_limits: {
    min_quantity?: number;
    max_quantity?: number;
  };
};

type AICatalogResponse = {
  protocol: string;
  merchant: {
    id: number;
    name: string;
    status: string;
    currency: string;
  };
  commerce_policies: AICatalogPolicy;
  catalog_summary: AICatalogSummary;
  items: AICatalogItem[];
};

type AIBuyerScenario = {
  id: string;
  title: string;
  description: string;
  query: string;
  budget_limit: number;
  product_id?: number | null;
  include_compatible_addon: boolean;
  expected_outcome: string;
};

type AIBuyerProcureResult = {
  status: string;
  message: string;
  execution_id: number | null;
  session_id: string;
  procurement_plan: any;
  cart_id: number | null;
  order: any | null;
  approval_id: number | null;
  policy_decision: {
    decision: string;
    reason: string;
  };
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

  // Day 11: Revenue Analytics & AI Campaign states
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignsLoading, setCampaignsLoading] = useState(false);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [campaignDecisionLoading, setCampaignDecisionLoading] = useState<number | null>(null);

  // Day 12: AI-Readable Catalog & AI Buyer Interface states
  const [aiCatalog, setAiCatalog] = useState<AICatalogResponse | null>(null);
  const [aiCatalogLoading, setAiCatalogLoading] = useState(false);
  const [showRawCatalogJson, setShowRawCatalogJson] = useState(false);
  const [buyerScenarios, setBuyerScenarios] = useState<AIBuyerScenario[]>([]);
  const [buyerQuery, setBuyerQuery] = useState("Procure a developer laptop under ₹70,000 paired with a compatible wireless mouse");
  const [buyerBudget, setBuyerBudget] = useState<number>(70000);
  const [buyerAutoConfirm, setBuyerAutoConfirm] = useState(true);
  const [buyerProductId, setBuyerProductId] = useState<number | null>(1);
  const [buyerProcureLoading, setBuyerProcureLoading] = useState(false);
  const [buyerProcureResult, setBuyerProcureResult] = useState<AIBuyerProcureResult | null>(null);

  // IMPORTANT:
  // Keep the actual token in React state instead of repeatedly
  // reading localStorage inside different effects.
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const [loggedIn, setLoggedIn] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  // Self-serve Storefront & Merchant States
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [shopName, setShopName] = useState("");
  const [currentMerchantId, setCurrentMerchantId] = useState<number>(1);
  const [currentMerchantName, setCurrentMerchantName] = useState<string>("My Store");
  const [copiedStoreLink, setCopiedStoreLink] = useState(false);

  // Add Product Modal States
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [newProductName, setNewProductName] = useState("");
  const [newProductPrice, setNewProductPrice] = useState("");
  const [newProductCategory, setNewProductCategory] = useState("laptop");
  const [newProductTags, setNewProductTags] = useState("");
  const [newProductInventory, setNewProductInventory] = useState("10");
  const [addProductLoading, setAddProductLoading] = useState(false);

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

      fetch(`${API}/analytics/overview?limit=10`, {
        headers: authHeaders,
      }).then(async (response) => {
        if (!response.ok) {
          const body = await response.text();

          console.error(
            "Analytics overview API failed:",
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
            `Analytics overview API failed: ${response.status}`,
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

      fetch(`${API}/auth/me`, {
        headers: authHeaders,
      }).then((r) => (r.ok ? r.json() : null)),
    ])
      .then(
        ([
          productData,
          dashboardData,
          approvalData,
          meData,
        ]) => {
          setProducts(productData);
          setDashboard(dashboardData);
          setApprovals(approvalData);
          if (meData?.merchant_id) {
            setCurrentMerchantId(meData.merchant_id);
          }
          if (meData?.merchant_name) {
            setCurrentMerchantName(meData.merchant_name);
          }
          loadExecutions(token);
          loadCampaigns(token);
          loadAICatalog(meData?.merchant_id || 1);
          loadBuyerScenarios();
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

  const loadCampaigns = async (tokenToUse?: string) => {
    const token = tokenToUse || accessToken;
    if (!token) return;
    setCampaignsLoading(true);
    try {
      const response = await fetch(`${API}/analytics/campaigns`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data);
      }
    } catch (err) {
      console.error("Failed to load campaigns:", err);
    } finally {
      setCampaignsLoading(false);
    }
  };

  const askAIInsights = async () => {
    if (!accessToken) return;
    setInsightsLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/analytics/insights`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`AI Insights failed: ${response.status}`);
      }
      const data = await response.json();
      setInsights(data);
      await loadCampaigns();
    } catch (err) {
      console.error("AI Insights error:", err);
      setError("Failed to generate AI revenue insights.");
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleCampaignDecision = async (campaignId: number, approve: boolean) => {
    if (!accessToken) return;
    setCampaignDecisionLoading(campaignId);
    setError("");
    try {
      const action = approve ? "approve" : "reject";
      const response = await fetch(`${API}/analytics/campaigns/${campaignId}/${action}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Action failed: ${response.status}`);
      }
      await loadCampaigns();
      if (insights?.campaign_proposal?.id === campaignId) {
        setInsights((prev) =>
          prev
            ? {
                ...prev,
                campaign_proposal: {
                  ...prev.campaign_proposal!,
                  status: approve ? "APPROVED" : "REJECTED",
                },
              }
            : null
        );
      }
    } catch (err: any) {
      console.error("Campaign decision error:", err);
      setError(err.message || "Failed to process campaign decision.");
    } finally {
      setCampaignDecisionLoading(null);
    }
  };

  const loadAICatalog = async (merchantId?: number) => {
    setAiCatalogLoading(true);
    const mId = merchantId ?? currentMerchantId ?? 1;
    try {
      const response = await fetch(`${API}/ai/catalog?merchant_id=${mId}`);
      if (response.ok) {
        const data = await response.json();
        setAiCatalog(data);
      }
    } catch (err) {
      console.error("Failed to load AI catalog:", err);
    } finally {
      setAiCatalogLoading(false);
    }
  };

  const loadBuyerScenarios = async () => {
    try {
      const response = await fetch(`${API}/ai/buyer/scenarios`);
      if (response.ok) {
        const data = await response.json();
        setBuyerScenarios(data);
      }
    } catch (err) {
      console.error("Failed to load buyer scenarios:", err);
    }
  };

  const executeBuyerProcure = async (scenario?: AIBuyerScenario) => {
    const query = scenario ? scenario.query : buyerQuery;
    const budget = scenario ? scenario.budget_limit : buyerBudget;
    const prodId = scenario ? scenario.product_id : buyerProductId;
    const addon = scenario ? scenario.include_compatible_addon : true;

    setBuyerProcureLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/ai/buyer/procure`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          merchant_id: 1,
          query: query,
          budget_limit: budget,
          product_id: prodId,
          include_compatible_addon: addon,
          auto_confirm: buyerAutoConfirm,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Procurement failed: ${response.status}`);
      }

      const result: AIBuyerProcureResult = await response.json();
      setBuyerProcureResult(result);

      // Refresh executions and approvals
      loadExecutions();
      if (accessToken) {
        fetch(`${API}/approvals`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        })
          .then((r) => r.ok && r.json())
          .then((d) => d && setApprovals(d))
          .catch(() => {});
      }
    } catch (err: any) {
      console.error("Autonomous procurement error:", err);
      setError(err.message || "Failed to execute autonomous buyer procurement.");
    } finally {
      setBuyerProcureLoading(false);
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

  const handleAddProduct = async () => {
    if (!newProductName.trim() || !newProductPrice || !accessToken) return;
    setAddProductLoading(true);
    setError("");
    try {
      const payload = {
        name: newProductName.trim(),
        price: parseFloat(newProductPrice),
        category: newProductCategory,
        tags: newProductTags
          ? newProductTags
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean)
          : [],
        use_cases: ["general"],
        inventory: parseInt(newProductInventory, 10) || 5,
      };

      const res = await fetch(`${API}/products`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to add product (${res.status})`);
      }

      // Refresh products list
      const prodRes = await fetch(`${API}/products`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (prodRes.ok) {
        const pData = await prodRes.json();
        setProducts(pData);
      }
      setShowAddProductModal(false);
      setNewProductName("");
      setNewProductPrice("");
      setNewProductTags("");
      loadAICatalog(currentMerchantId);
    } catch (err: any) {
      console.error("Add product error:", err);
      setError(err.message || "Failed to add product");
    } finally {
      setAddProductLoading(false);
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
            {authMode === "login"
              ? "Sign in to access your merchant console."
              : "Launch your autonomous AI merchant store."}
          </p>

          {/* Mode Switcher Tabs */}
          <div style={{ display: "flex", gap: "8px", margin: "18px 0 14px" }}>
            <button
              type="button"
              onClick={() => {
                setAuthMode("login");
                setError("");
              }}
              style={{
                flex: 1,
                padding: "8px",
                borderRadius: "8px",
                border: authMode === "login" ? "1px solid #3395ff" : "1px solid #232a3a",
                background: authMode === "login" ? "rgba(51, 149, 255, 0.15)" : "#12161f",
                color: authMode === "login" ? "#3395ff" : "#8b94a8",
                fontWeight: 600,
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode("register");
                setError("");
              }}
              style={{
                flex: 1,
                padding: "8px",
                borderRadius: "8px",
                border: authMode === "register" ? "1px solid #2fd180" : "1px solid #232a3a",
                background: authMode === "register" ? "rgba(47, 209, 128, 0.15)" : "#12161f",
                color: authMode === "register" ? "#2fd180" : "#8b94a8",
                fontWeight: 600,
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Open New Shop
            </button>
          </div>

          {authMode === "register" && (
            <input
              type="text"
              placeholder="Store Name (e.g. Apex Gaming Hardware)"
              value={shopName}
              onChange={(event) => setShopName(event.target.value)}
              style={styles.search}
            />
          )}

          <input
            type="email"
            placeholder="Merchant Email"
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
                if (authMode === "register") {
                  // Register merchant & auto-provision shop
                  const regResp = await fetch(`${API}/auth/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      email,
                      password,
                      shop_name: shopName || "My Store",
                    }),
                  });

                  if (!regResp.ok) {
                    const errData = await regResp.json().catch(() => ({}));
                    throw new Error(errData.detail || `Registration failed: ${regResp.status}`);
                  }
                }

                // Log in
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

                window.localStorage.setItem(
                  ACCESS_TOKEN_KEY,
                  token,
                );

                if (data.user?.merchant_id) {
                  setCurrentMerchantId(data.user.merchant_id);
                }
                if (data.user?.merchant_name) {
                  setCurrentMerchantName(data.user.merchant_name);
                }

                setAccessToken(token);
                setLoggedIn(true);
              } catch (err: any) {
                console.error(err);
                setError(err.message || "Authentication failed. Check credentials.");
              } finally {
                setLoginLoading(false);
              }
            }}
            style={{
              ...styles.button,
              background: authMode === "register" ? "#2fd180" : "#3395ff",
              color: "#05070c",
              border: "none",
              padding: "12px",
              marginTop: "16px",
            }}
          >
            {loginLoading
              ? "Processing..."
              : authMode === "register"
              ? "Create Store & Launch"
              : "Sign in to Dashboard"}
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

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={styles.status}>
            <span style={styles.statusDot}></span>
            System operational
          </div>
          <button
            type="button"
            onClick={() => {
              window.localStorage.removeItem(ACCESS_TOKEN_KEY);
              setAccessToken(null);
              setLoggedIn(false);
            }}
            style={{
              padding: "4px 10px",
              background: "#191f2c",
              border: "1px solid #232a3a",
              borderRadius: "6px",
              color: "#8b94a8",
              fontSize: "12px",
              cursor: "pointer",
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Shareable Public Storefront Banner */}
      <section
        style={{
          maxWidth: 1200,
          margin: "0 auto 24px",
          padding: "16px 20px",
          borderRadius: "16px",
          background: "linear-gradient(90deg, rgba(51, 149, 255, 0.12), rgba(47, 209, 128, 0.12))",
          border: "1px solid rgba(51, 149, 255, 0.3)",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "28px" }}>🏪</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: "16px", color: "#e8ecf4", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>{currentMerchantName}</span>
              <span
                style={{
                  fontSize: "11px",
                  padding: "2px 8px",
                  borderRadius: "999px",
                  background: "rgba(47, 209, 128, 0.2)",
                  color: "#2fd180",
                  border: "1px solid rgba(47, 209, 128, 0.4)",
                  fontWeight: 600,
                }}
              >
                Storefront Live
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#8b94a8", marginTop: "2px" }}>
              Customer Storefront URL:{" "}
              <span style={{ fontFamily: "monospace", color: "#3395ff" }}>
                http://localhost:3000/shop/{currentMerchantId}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => {
              const url = `${window.location.origin}/shop/${currentMerchantId}`;
              navigator.clipboard.writeText(url);
              setCopiedStoreLink(true);
              setTimeout(() => setCopiedStoreLink(false), 2500);
            }}
            style={{
              padding: "8px 14px",
              borderRadius: "10px",
              background: "#191f2c",
              border: "1px solid #232a3a",
              color: "#e8ecf4",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {copiedStoreLink ? "✓ Link Copied!" : "📋 Copy Store Link"}
          </button>

          <a
            href={`/shop/${currentMerchantId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: "8px 16px",
              borderRadius: "10px",
              background: "#3395ff",
              color: "#05070c",
              fontSize: "12px",
              fontWeight: 700,
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>Visit Customer Store</span>
            <span>↗</span>
          </a>

          <button
            type="button"
            onClick={() => setShowAddProductModal(true)}
            style={{
              padding: "8px 16px",
              borderRadius: "10px",
              background: "#2fd180",
              color: "#05070c",
              fontSize: "12px",
              fontWeight: 700,
              border: "none",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>+ Add Product</span>
          </button>
        </div>
      </section>

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
                label="Total Revenue"
                value={money(
                  dashboard.metrics.total_revenue ??
                    dashboard.metrics.revenue ??
                    0,
                )}
              />

              <MetricCard
                label="AI-Influenced Revenue"
                value={money(
                  dashboard.metrics.ai_influenced_revenue ?? 0,
                )}
              />

              <MetricCard
                label="Upsell Revenue"
                value={money(
                  dashboard.metrics.upsell_revenue ?? 0,
                )}
              />

              <MetricCard
                label="Recovered Revenue"
                value={money(
                  dashboard.metrics.recovered_revenue,
                )}
              />
            </div>

            <div style={styles.secondaryGrid}>
              <MetricCard
                label="Average Order"
                value={money(
                  dashboard.metrics.average_order_value,
                )}
              />

              <MetricCard
                label="Payment Conversion"
                value={`${dashboard.metrics.payment_conversion_rate}%`}
              />

              <MetricCard
                label="Recovery Rate"
                value={`${dashboard.metrics.payment_recovery_rate ?? 0}%`}
              />

              <MetricCard
                label="Total Orders"
                value={dashboard.metrics.total_orders.toString()}
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

      {/* Autonomous Revenue Intelligence & Campaign Studio (Day 11) */}
      <section style={styles.catalog}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h2 style={styles.title}>Autonomous Revenue Intelligence & Campaign Studio</h2>
            <p style={styles.muted}>
              Generate grounded catalog bundle promotions, forecast revenue uplift, and enforce human-in-the-loop campaign activation.
            </p>
          </div>
          <button
            type="button"
            disabled={insightsLoading}
            onClick={() => askAIInsights()}
            style={{
              ...styles.button,
              background: "#1e1b4b",
              color: "#e0e7ff",
              border: "1px solid #4338ca",
              padding: "10px 20px",
              marginTop: 0,
              display: "flex",
              alignItems: "center",
              gap: 8,
              boxShadow: "0 2px 8px rgba(67, 56, 202, 0.2)",
            }}
          >
            <span>⚡</span>
            <span>{insightsLoading ? "Analyzing Catalog & Affinity..." : "Ask AI: How can I increase revenue?"}</span>
          </button>
        </div>

        {/* AI Grounded Insights Banner if available */}
        {insights && (
          <div style={{ marginTop: 20, background: "#f5f3ff", border: "1px solid #ddd6fe", borderRadius: 14, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <span style={{ fontSize: 18 }}>💡</span>
              <strong style={{ color: "#4c1d95", fontSize: 16 }}>AI Grounded Analysis & Inventory Audit</strong>
            </div>
            <ul style={{ margin: 0, paddingLeft: 20, color: "#5b21b6", fontSize: 14, lineHeight: 1.7 }}>
              {insights.insights.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>

            {insights.campaign_proposal && (
              <div
                style={{
                  marginTop: 16,
                  padding: 18,
                  borderRadius: 12,
                  background: "#fff",
                  border: "1px solid #c4b5fd",
                  boxShadow: "0 2px 6px rgba(124, 58, 237, 0.08)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
                  <div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "#6d28d9", textTransform: "uppercase", letterSpacing: 0.5 }}>
                      Recommended Promotion Proposal #{insights.campaign_proposal.id}
                    </span>
                    <h3 style={{ margin: "4px 0 8px", fontSize: 18, color: "#1e1b4b" }}>
                      {insights.campaign_proposal.title}
                    </h3>
                  </div>
                  <span
                    style={{
                      padding: "4px 10px",
                      borderRadius: 999,
                      fontSize: 12,
                      fontWeight: 700,
                      background:
                        insights.campaign_proposal.status === "APPROVED"
                          ? "#dcfce7"
                          : insights.campaign_proposal.status === "REJECTED"
                          ? "#fee2e2"
                          : "#fef3c7",
                      color:
                        insights.campaign_proposal.status === "APPROVED"
                          ? "#15803d"
                          : insights.campaign_proposal.status === "REJECTED"
                          ? "#b91c1c"
                          : "#b45309",
                    }}
                  >
                    {insights.campaign_proposal.status}
                  </span>
                </div>

                <p style={{ margin: "6px 0 12px", fontSize: 14, color: "#374151", lineHeight: 1.5 }}>
                  {insights.campaign_proposal.description}
                </p>

                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, color: "#334155" }}>
                  <span>📈</span>
                  <strong>Forecast:</strong>
                  <span>{insights.campaign_proposal.projected_impact}</span>
                </div>

                {insights.campaign_proposal.status === "PENDING_APPROVAL" && (
                  <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
                    <button
                      type="button"
                      disabled={campaignDecisionLoading === insights.campaign_proposal.id}
                      onClick={() => handleCampaignDecision(insights.campaign_proposal!.id, true)}
                      style={{
                        ...styles.button,
                        background: "#047857",
                        color: "#fff",
                        border: "none",
                        padding: "8px 18px",
                        marginTop: 0,
                      }}
                    >
                      {campaignDecisionLoading === insights.campaign_proposal.id ? "Processing..." : "Approve & Activate Campaign"}
                    </button>
                    <button
                      type="button"
                      disabled={campaignDecisionLoading === insights.campaign_proposal.id}
                      onClick={() => handleCampaignDecision(insights.campaign_proposal!.id, false)}
                      style={{
                        ...styles.button,
                        background: "#fef2f2",
                        color: "#b91c1c",
                        border: "1px solid #fecaca",
                        padding: "8px 18px",
                        marginTop: 0,
                      }}
                    >
                      Reject Proposal
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Existing & Approved Campaigns Table */}
        <div style={{ ...styles.activityCard, marginTop: 20 }}>
          <div style={styles.activityHeader}>
            <div>
              <h3 style={styles.cardTitle}>Merchant Bundle Campaigns</h3>
              <p style={styles.muted}>
                Active and historical AI-generated bundle promotions and their governance state.
              </p>
            </div>
            <button
              type="button"
              style={{ ...styles.button, background: "#f3f4f6", marginTop: 0 }}
              onClick={() => loadCampaigns()}
            >
              Refresh Campaigns
            </button>
          </div>

          {campaignsLoading ? (
            <div style={{ padding: 20, color: "#6b7280" }}>Loading campaigns...</div>
          ) : campaigns.length === 0 ? (
            <div style={{ padding: 24, textAlign: "center", color: "#6b7280", fontSize: 14 }}>
              No bundle campaigns yet. Click <strong>"Ask AI: How can I increase revenue?"</strong> above to generate your first promotion proposal.
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              {campaigns.map((camp) => (
                <div
                  key={camp.id}
                  style={{
                    ...styles.activityRow,
                    flexWrap: "wrap",
                    gap: 16,
                    padding: 16,
                    borderBottom: "1px solid #f1f5f9",
                  }}
                >
                  <div style={{ flex: 1, minWidth: 280 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <strong style={{ fontSize: 15, color: "#111827" }}>{camp.title}</strong>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: 999,
                          fontSize: 11,
                          fontWeight: 700,
                          background:
                            camp.status === "APPROVED"
                              ? "#dcfce7"
                              : camp.status === "REJECTED"
                              ? "#fee2e2"
                              : "#fef3c7",
                          color:
                            camp.status === "APPROVED"
                              ? "#15803d"
                              : camp.status === "REJECTED"
                              ? "#b91c1c"
                              : "#b45309",
                        }}
                      >
                        {camp.status}
                      </span>
                    </div>
                    <p style={{ margin: "4px 0 6px", fontSize: 13, color: "#4b5563" }}>
                      {camp.description}
                    </p>
                    <div style={{ fontSize: 12, color: "#6b7280", display: "flex", gap: 16, flexWrap: "wrap" }}>
                      <span>Discount: <strong>{camp.discount_percent}%</strong></span>
                      {camp.bundle_config && (
                        <span>
                          Bundle Price: <strong>₹{camp.bundle_config.discounted_total.toLocaleString("en-IN")}</strong> (Regular: ₹{camp.bundle_config.original_total.toLocaleString("en-IN")})
                        </span>
                      )}
                      {camp.created_at && (
                        <span>Created: {new Date(camp.created_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>

                  {camp.status === "PENDING_APPROVAL" ? (
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <button
                        type="button"
                        disabled={campaignDecisionLoading === camp.id}
                        onClick={() => handleCampaignDecision(camp.id, true)}
                        style={{
                          ...styles.button,
                          background: "#047857",
                          color: "#fff",
                          border: "none",
                          padding: "6px 14px",
                          fontSize: 13,
                          marginTop: 0,
                        }}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={campaignDecisionLoading === camp.id}
                        onClick={() => handleCampaignDecision(camp.id, false)}
                        style={{
                          ...styles.button,
                          background: "#fef2f2",
                          color: "#b91c1c",
                          border: "1px solid #fecaca",
                          padding: "6px 14px",
                          fontSize: 13,
                          marginTop: 0,
                        }}
                      >
                        Reject
                      </button>
                    </div>
                  ) : (
                    <div style={{ fontSize: 12, color: "#6b7280", textAlign: "right" }}>
                      <div>Decided by User #{camp.decided_by_user_id ?? "N/A"}</div>
                      {camp.decided_at && <div>{new Date(camp.decided_at).toLocaleString()}</div>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
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

      {/* AI-Readable Catalog & Autonomous AI Buyer Simulator (Day 12) */}
      <section style={styles.catalog}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 20 }}>🤖</span>
              <h2 style={styles.title}>AI-Readable Catalog & Autonomous AI Buyer Interface</h2>
              <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 8px", background: "#e0e7ff", color: "#3730a3", borderRadius: 999 }}>
                DAY 12
              </span>
            </div>
            <p style={styles.muted}>
              Structured machine-readable commerce protocol (<code>/ai/catalog</code>) with availability &amp; policy manifests, alongside a controlled autonomous buyer client executing policy-governed procurement.
            </p>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              style={{ ...styles.button, background: "#f8fafc", marginTop: 0 }}
              onClick={() => loadAICatalog()}
            >
              Refresh AI Catalog
            </button>
            <button
              type="button"
              style={{
                ...styles.button,
                background: showRawCatalogJson ? "#4338ca" : "#f1f5f9",
                color: showRawCatalogJson ? "#fff" : "#1e293b",
                marginTop: 0,
              }}
              onClick={() => setShowRawCatalogJson(!showRawCatalogJson)}
            >
              {showRawCatalogJson ? "View Clean Summary" : "Inspect Raw JSON Schema"}
            </button>
          </div>
        </div>

        {/* Machine-Readable Protocol Manifest Header Card */}
        {aiCatalog && (
          <div style={{ marginTop: 20, background: "#0f172a", color: "#f8fafc", borderRadius: 14, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, borderBottom: "1px solid #334155", paddingBottom: 14 }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: "#38bdf8", textTransform: "uppercase" }}>
                  Active Agent Protocol
                </span>
                <div style={{ fontSize: 16, fontWeight: 700, color: "#fff", marginTop: 2 }}>
                  {aiCatalog.protocol}
                </div>
              </div>
              <div style={{ display: "flex", gap: 16, fontSize: 13, flexWrap: "wrap" }}>
                <div>
                  <span style={{ color: "#94a3b8" }}>Endpoint: </span>
                  <code style={{ background: "#1e293b", padding: "2px 6px", borderRadius: 4, color: "#38bdf8" }}>GET /ai/catalog?merchant_id={aiCatalog.merchant.id}</code>
                </div>
                <div>
                  <span style={{ color: "#94a3b8" }}>Discovered Items: </span>
                  <strong style={{ color: "#fff" }}>{aiCatalog.catalog_summary.total_items}</strong>
                </div>
                <div>
                  <span style={{ color: "#94a3b8" }}>In Stock: </span>
                  <strong style={{ color: "#4ade80" }}>{aiCatalog.catalog_summary.in_stock_items}</strong>
                </div>
              </div>
            </div>

            {/* Commerce Policies Manifest */}
            <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, fontSize: 12 }}>
              <div style={{ background: "#1e293b", padding: "10px 14px", borderRadius: 8, border: "1px solid #334155" }}>
                <span style={{ color: "#94a3b8" }}>MAX TRANSACTION LIMIT</span>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginTop: 2 }}>
                  ₹{aiCatalog.commerce_policies.max_transaction_amount.toLocaleString("en-IN")}
                </div>
              </div>
              <div style={{ background: "#1e293b", padding: "10px 14px", borderRadius: 8, border: "1px solid #334155" }}>
                <span style={{ color: "#94a3b8" }}>MAX ALLOWED DISCOUNT</span>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginTop: 2 }}>
                  {aiCatalog.commerce_policies.max_discount_percent}%
                </div>
              </div>
              <div style={{ background: "#1e293b", padding: "10px 14px", borderRadius: 8, border: "1px solid #334155" }}>
                <span style={{ color: "#94a3b8" }}>APPROVAL THRESHOLD</span>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#facc15", marginTop: 2 }}>
                  {aiCatalog.commerce_policies.merchant_approval_threshold ? `₹${aiCatalog.commerce_policies.merchant_approval_threshold.toLocaleString("en-IN")}` : "None"}
                </div>
              </div>
              <div style={{ background: "#1e293b", padding: "10px 14px", borderRadius: 8, border: "1px solid #334155" }}>
                <span style={{ color: "#94a3b8" }}>CONFIRMATION GATE</span>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#4ade80", marginTop: 2 }}>
                  {aiCatalog.commerce_policies.customer_confirmation_required ? "MANDATORY" : "OPTIONAL"}
                </div>
              </div>
            </div>

            {/* Optional Raw JSON view */}
            {showRawCatalogJson && (
              <div style={{ marginTop: 16 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8" }}>MACHINE-READABLE MANIFEST PAYLOAD:</span>
                <pre style={{ margin: "6px 0 0", padding: 14, background: "#020617", borderRadius: 8, fontSize: 12, maxHeight: 260, overflowY: "auto", border: "1px solid #1e293b" }}>
                  {JSON.stringify(aiCatalog, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Controlled AI Buyer Client Simulation Studio */}
        <div style={{ ...styles.activityCard, marginTop: 20 }}>
          <div style={styles.activityHeader}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <h3 style={styles.cardTitle}>Autonomous AI Buyer Client Simulator</h3>
                <span style={styles.liveBadge}>CONTROLLED AGENT</span>
              </div>
              <p style={styles.muted}>
                Test an external autonomous AI buyer discovering products, assembling carts, and routing checkout through merchant policy gates.
              </p>
            </div>
          </div>

          <div style={{ padding: 20 }}>
            {/* Scenario Preset Chips */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 8 }}>
                Select Golden Demonstration Scenario:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {buyerScenarios.map((scen) => (
                  <button
                    key={scen.id}
                    type="button"
                    style={{
                      padding: "8px 14px",
                      borderRadius: 8,
                      border: buyerQuery === scen.query ? "2px solid #4f46e5" : "1px solid #d1d5db",
                      background: buyerQuery === scen.query ? "#eef2ff" : "#fff",
                      fontSize: 13,
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                    onClick={() => {
                      setBuyerQuery(scen.query);
                      setBuyerBudget(scen.budget_limit);
                      if (scen.product_id) setBuyerProductId(scen.product_id);
                      executeBuyerProcure(scen);
                    }}
                  >
                    <div style={{ fontWeight: 700, color: "#1f2937" }}>{scen.title}</div>
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>
                      Budget: ₹{scen.budget_limit.toLocaleString("en-IN")} • {scen.expected_outcome}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Procurement Inputs */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 10, alignItems: "center" }}>
              <input
                type="text"
                placeholder="Enter AI Buyer goal (e.g. 'Procure laptop for programming under ₹70,000 with mouse')..."
                value={buyerQuery}
                onChange={(e) => setBuyerQuery(e.target.value)}
                style={{ ...styles.search, margin: 0 }}
              />

              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 13, color: "#6b7280", fontWeight: 600 }}>Budget:</span>
                <input
                  type="number"
                  value={buyerBudget}
                  onChange={(e) => setBuyerBudget(Number(e.target.value))}
                  style={{
                    padding: "12px",
                    border: "1px solid #d1d5db",
                    borderRadius: 8,
                    width: 110,
                    fontSize: 14,
                  }}
                />
              </div>

              <button
                type="button"
                disabled={buyerProcureLoading}
                onClick={() => executeBuyerProcure()}
                style={{
                  ...styles.button,
                  background: "#4338ca",
                  color: "#fff",
                  border: "none",
                  padding: "0 22px",
                  height: 44,
                  marginTop: 0,
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <span>🚀</span>
                <span>{buyerProcureLoading ? "Autonomous Agent Running..." : "Execute AI Buyer"}</span>
              </button>
            </div>

            {/* Procurement Execution Result Banner & Breakdown */}
            {buyerProcureResult && (
              <div
                style={{
                  marginTop: 20,
                  borderRadius: 12,
                  border: "1px solid",
                  borderColor:
                    buyerProcureResult.status === "SUCCESS"
                      ? "#86efac"
                      : buyerProcureResult.status === "NEEDS_APPROVAL"
                      ? "#fde047"
                      : "#fca5a5",
                  background:
                    buyerProcureResult.status === "SUCCESS"
                      ? "#f0fdf4"
                      : buyerProcureResult.status === "NEEDS_APPROVAL"
                      ? "#fefce8"
                      : "#fef2f2",
                  padding: 18,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 22 }}>
                      {buyerProcureResult.status === "SUCCESS" ? "✅" : buyerProcureResult.status === "NEEDS_APPROVAL" ? "⏳" : "🛑"}
                    </span>
                    <div>
                      <strong
                        style={{
                          fontSize: 16,
                          color:
                            buyerProcureResult.status === "SUCCESS"
                              ? "#15803d"
                              : buyerProcureResult.status === "NEEDS_APPROVAL"
                              ? "#854d0e"
                              : "#b91c1c",
                        }}
                      >
                        {buyerProcureResult.status === "SUCCESS"
                          ? "Procurement Successfully Executed"
                          : buyerProcureResult.status === "NEEDS_APPROVAL"
                          ? "Procurement Paused: Needs Merchant Human Approval"
                          : "Procurement Blocked: Policy Violation"}
                      </strong>
                      <p style={{ margin: "2px 0 0", fontSize: 13, color: "#374151" }}>
                        {buyerProcureResult.message}
                      </p>
                    </div>
                  </div>

                  {buyerProcureResult.execution_id && (
                    <button
                      type="button"
                      style={{
                        ...styles.button,
                        background: "#fff",
                        border: "1px solid #cbd5e1",
                        fontSize: 12,
                        marginTop: 0,
                      }}
                      onClick={() => viewTrace(buyerProcureResult.execution_id!)}
                    >
                      🔍 Inspect Trace #{buyerProcureResult.execution_id}
                    </button>
                  )}
                </div>

                {/* Procurement Summary Cards */}
                <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
                  {buyerProcureResult.procurement_plan?.base_product && (
                    <div style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                      <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>SELECTED PRODUCT</span>
                      <div style={{ fontWeight: 700, fontSize: 14, color: "#0f172a" }}>
                        {buyerProcureResult.procurement_plan.base_product.name}
                      </div>
                      <div style={{ fontSize: 12, color: "#64748b" }}>
                        Qty: {buyerProcureResult.procurement_plan.base_product.quantity} • ₹{buyerProcureResult.procurement_plan.base_product.total.toLocaleString("en-IN")}
                      </div>
                    </div>
                  )}

                  {buyerProcureResult.procurement_plan?.addon_product && (
                    <div style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                      <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>COMPATIBLE ADD-ON</span>
                      <div style={{ fontWeight: 700, fontSize: 14, color: "#0f172a" }}>
                        {buyerProcureResult.procurement_plan.addon_product.name}
                      </div>
                      <div style={{ fontSize: 12, color: "#64748b" }}>
                        Qty: 1 • ₹{buyerProcureResult.procurement_plan.addon_product.total.toLocaleString("en-IN")}
                      </div>
                    </div>
                  )}

                  <div style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                    <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>TOTAL AMOUNT</span>
                    <div style={{ fontWeight: 800, fontSize: 16, color: "#0f172a" }}>
                      ₹{buyerProcureResult.procurement_plan?.total_amount ? buyerProcureResult.procurement_plan.total_amount.toLocaleString("en-IN") : 0}
                    </div>
                    <div style={{ fontSize: 12, color: "#64748b" }}>
                      Policy: {buyerProcureResult.policy_decision.decision}
                    </div>
                  </div>

                  {buyerProcureResult.order?.razorpay_order_id && (
                    <div style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                      <span style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>RAZORPAY ORDER ID</span>
                      <div style={{ fontWeight: 700, fontSize: 13, color: "#16a34a" }}>
                        {buyerProcureResult.order.razorpay_order_id}
                      </div>
                      <div style={{ fontSize: 12, color: "#64748b" }}>
                        Local Order #{buyerProcureResult.order.local_order_id}
                      </div>
                    </div>
                  )}

                  {buyerProcureResult.approval_id && (
                    <div style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #fef08a" }}>
                      <span style={{ fontSize: 11, color: "#854d0e", fontWeight: 700 }}>APPROVAL TICKET</span>
                      <div style={{ fontWeight: 700, fontSize: 13, color: "#a16207" }}>
                        Ticket #{buyerProcureResult.approval_id} (PENDING)
                      </div>
                      <div style={{ fontSize: 12, color: "#854d0e" }}>
                        Awaiting merchant authorization above
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
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

      {/* Add Product Modal */}
      {showAddProductModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "20px",
          }}
          onClick={() => setShowAddProductModal(false)}
        >
          <div
            style={{
              background: "#12161f",
              border: "1px solid #232a3a",
              borderRadius: "16px",
              padding: "24px",
              maxWidth: "480px",
              width: "100%",
              boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
              color: "#e8ecf4",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "#e8ecf4" }}>
                Add Product to Catalog
              </h3>
              <button
                type="button"
                onClick={() => setShowAddProductModal(false)}
                style={{ background: "none", border: "none", color: "#8b94a8", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <p style={{ margin: "0 0 16px", fontSize: "13px", color: "#8b94a8" }}>
              Items added here are immediately live on your public storefront and grounded in the AI Sales Agent's catalog.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "#8b94a8", display: "block", marginBottom: "4px" }}>
                  Product Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Ergonomic Mechanical Keyboard"
                  value={newProductName}
                  onChange={(e) => setNewProductName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1px solid #232a3a",
                    background: "#0b0e14",
                    color: "#e8ecf4",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#8b94a8", display: "block", marginBottom: "4px" }}>
                    Price (₹ INR)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g. 4500"
                    value={newProductPrice}
                    onChange={(e) => setNewProductPrice(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid #232a3a",
                      background: "#0b0e14",
                      color: "#e8ecf4",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#8b94a8", display: "block", marginBottom: "4px" }}>
                    Category
                  </label>
                  <select
                    value={newProductCategory}
                    onChange={(e) => setNewProductCategory(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid #232a3a",
                      background: "#0b0e14",
                      color: "#e8ecf4",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  >
                    <option value="laptop">Laptop</option>
                    <option value="accessories">Accessories</option>
                    <option value="smartphone">Smartphone</option>
                    <option value="peripherals">Peripherals</option>
                    <option value="hardware">Hardware</option>
                    <option value="software">Software</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#8b94a8", display: "block", marginBottom: "4px" }}>
                    Tags (comma separated)
                  </label>
                  <input
                    type="text"
                    placeholder="gaming, wireless, rgb"
                    value={newProductTags}
                    onChange={(e) => setNewProductTags(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid #232a3a",
                      background: "#0b0e14",
                      color: "#e8ecf4",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#8b94a8", display: "block", marginBottom: "4px" }}>
                    Stock Units
                  </label>
                  <input
                    type="number"
                    placeholder="10"
                    value={newProductInventory}
                    onChange={(e) => setNewProductInventory(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid #232a3a",
                      background: "#0b0e14",
                      color: "#e8ecf4",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              </div>

              <button
                type="button"
                disabled={addProductLoading}
                onClick={handleAddProduct}
                style={{
                  marginTop: "8px",
                  padding: "12px",
                  borderRadius: "8px",
                  background: "#2fd180",
                  color: "#05070c",
                  fontWeight: 700,
                  fontSize: "14px",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                {addProductLoading ? "Saving Product..." : "Save Product to Store"}
              </button>
            </div>
          </div>
        </div>
      )}
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