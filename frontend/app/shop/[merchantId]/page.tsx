"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Script from "next/script";

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

type StoreInfo = {
  merchant_id: number;
  store_name: string;
  status: string;
  currency: string;
  policy_max_order: number;
  approval_threshold: number | null;
  products: Product[];
};

type CartItem = {
  product: Product;
  quantity: number;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  recommendedProduct?: Product;
  recommendedUpsell?: Product;
};

const API = "http://127.0.0.1:8000";

function money(amount: number) {
  return `₹${amount.toLocaleString("en-IN")}`;
}

export default function PublicStorefrontPage() {
  const params = useParams();
  const merchantId = params?.merchantId ? String(params.merchantId) : "1";

  const [storeInfo, setStoreInfo] = useState<StoreInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Search
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  // Cart
  const [cart, setCart] = useState<CartItem[]>([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [customerEmail, setCustomerEmail] = useState("customer@demo.com");
  const [customerName, setCustomerName] = useState("Alex Hunter");
  const [checkingOut, setCheckingOut] = useState(false);
  const [checkoutNotice, setCheckoutNotice] = useState<{
    type: "success" | "approval" | "error";
    message: string;
    orderId?: number;
    paymentId?: string;
  } | null>(null);

  // AI Concierge
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your AI Sales Concierge. Ask me about recommendations, compatibility, or specifications from our catalog!",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Load Store Info
  const loadStore = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API}/shop/${merchantId}/info`);
      if (!res.ok) {
        throw new Error(`Store not found (Status: ${res.status})`);
      }
      const data: StoreInfo = await res.json();
      setStoreInfo(data);
    } catch (err: any) {
      console.error("Failed to load store:", err);
      setError(err.message || "Failed to load store information.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStore();
  }, [merchantId]);

  // Cart Helpers
  const addToCart = (product: Product, quantity = 1) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        const newQty = Math.min(existing.quantity + quantity, product.inventory);
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: newQty } : item
        );
      }
      return [...prev, { product, quantity: Math.min(quantity, product.inventory) }];
    });
    setCartOpen(true);
  };

  const updateQuantity = (productId: number, delta: number) => {
    setCart((prev) =>
      prev
        .map((item) => {
          if (item.product.id === productId) {
            const newQty = item.quantity + delta;
            return newQty > 0 ? { ...item, quantity: Math.min(newQty, item.product.inventory) } : null;
          }
          return item;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const removeFromCart = (productId: number) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const cartSubtotal = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const totalItemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  // AI Chat Handler
  const handleSendMessage = async (customPrompt?: string) => {
    const text = customPrompt || chatInput;
    if (!text.trim() || chatLoading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setChatMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setChatInput("");
    setChatLoading(true);

    try {
      const res = await fetch(`${API}/shop/${merchantId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        throw new Error(`AI assistant error (${res.status})`);
      }

      const data = await res.json();
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          recommendedProduct: data.recommended_product || undefined,
          recommendedUpsell: data.recommended_upsell || undefined,
        },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I had trouble checking the catalog right now. Please browse the items directly below!",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Checkout with Razorpay Test Mode
  const handleCheckout = async () => {
    if (cart.length === 0) return;
    setCheckingOut(true);
    setCheckoutNotice(null);

    try {
      const payload = {
        items: cart.map((c) => ({
          product_id: c.product.id,
          quantity: c.quantity,
        })),
        customer_email: customerEmail,
        customer_name: customerName,
        confirmed: true,
      };

      const res = await fetch(`${API}/shop/${merchantId}/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Checkout request rejected");
      }

      // Check if order was held for Human-In-The-Loop approval
      if (data.status === "NEEDS_APPROVAL") {
        setCheckoutNotice({
          type: "approval",
          message: data.message || "Order held for merchant approval.",
          orderId: data.order_id,
        });
        setCart([]);
        return;
      }

      // Order created -> Launch Razorpay Checkout Modal
      const rzpKey = data.razorpay_key_id;
      const rzpOrderId = data.razorpay_order_id;
      const orderDbId = data.order_id;

      if (typeof window === "undefined" || !(window as any).Razorpay) {
        throw new Error("Razorpay SDK not loaded. Please refresh the page.");
      }

      const options = {
        key: rzpKey,
        amount: Math.round(data.amount * 100),
        currency: data.currency || "INR",
        name: storeInfo?.store_name || "RazorGrow Store",
        description: `Order #${orderDbId} - Razorpay Test Mode`,
        order_id: rzpOrderId,
        handler: async function (response: any) {
          try {
            // Verify payment on backend
            const verifyRes = await fetch(`${API}/shop/${merchantId}/verify-payment`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                order_id: orderDbId,
                razorpay_order_id: response.razorpay_order_id || rzpOrderId,
                razorpay_payment_id: response.razorpay_payment_id,
              }),
            });

            const verifyData = await verifyRes.json();
            if (verifyRes.ok) {
              setCheckoutNotice({
                type: "success",
                message: "Payment successful! Your order has been placed and confirmed.",
                orderId: orderDbId,
                paymentId: response.razorpay_payment_id,
              });
              setCart([]);
              loadStore(); // Refresh inventory
            } else {
              setCheckoutNotice({
                type: "error",
                message: verifyData.detail || "Payment verification failed on server.",
              });
            }
          } catch (err: any) {
            setCheckoutNotice({
              type: "error",
              message: "Payment completed but verification failed to connect.",
            });
          }
        },
        prefill: {
          name: customerName,
          email: customerEmail,
        },
        theme: {
          color: "#3395ff",
        },
        modal: {
          ondismiss: function () {
            setCheckingOut(false);
          },
        },
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    } catch (err: any) {
      console.error("Checkout error:", err);
      setCheckoutNotice({
        type: "error",
        message: err.message || "Failed to initiate payment.",
      });
    } finally {
      setCheckingOut(false);
    }
  };

  // Categories list
  const categories = [
    "all",
    ...Array.from(new Set(storeInfo?.products.map((p) => p.category) || [])),
  ];

  const filteredProducts = (storeInfo?.products || []).filter((p) => {
    const matchesSearch =
      search === "" ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.tags.some((t) => t.toLowerCase().includes(search.toLowerCase())) ||
      p.use_cases.some((u) => u.toLowerCase().includes(search.toLowerCase()));
    const matchesCat = selectedCategory === "all" || p.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0e14] text-[#e8ecf4] flex flex-col items-center justify-center p-6">
        <div className="w-12 h-12 border-4 border-[#3395ff]/30 border-t-[#3395ff] rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-medium tracking-tight">Connecting to Merchant Storefront...</h2>
        <p className="text-[#8b94a8] text-sm mt-2">Grounded catalog and AI Sales Agent loading</p>
      </div>
    );
  }

  if (error || !storeInfo) {
    return (
      <div className="min-h-screen bg-[#0b0e14] text-[#e8ecf4] flex flex-col items-center justify-center p-6">
        <div className="max-w-md bg-[#12161f] border border-[#232a3a] p-8 rounded-2xl text-center shadow-2xl">
          <div className="w-16 h-16 bg-[#ff5c5c]/10 text-[#ff5c5c] rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🏪
          </div>
          <h1 className="text-2xl font-bold mb-2">Storefront Unavailable</h1>
          <p className="text-[#8b94a8] text-sm mb-6">{error || "This store does not exist or is currently inactive."}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2.5 bg-[#3395ff] text-black font-semibold rounded-lg hover:bg-[#3395ff]/90 transition-all cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0e14] text-[#e8ecf4] flex flex-col selection:bg-[#3395ff] selection:text-black">
      {/* Razorpay Script */}
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />

      {/* Top Notification / Banner */}
      <div className="bg-[#12161f] border-b border-[#232a3a] py-2 px-6 flex items-center justify-between text-xs text-[#8b94a8]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#2fd180] pulse-dot" />
          <span className="font-medium text-[#e8ecf4]">Interactive Test Store</span>
          <span>•</span>
          <span>Simulated Razorpay payments enabled (No real charges)</span>
        </div>
        <div className="hidden sm:flex items-center gap-4">
          <span>Max Cart Limit: {money(storeInfo.policy_max_order)}</span>
          {storeInfo.approval_threshold && (
            <span>Auto-Approval Threshold: {money(storeInfo.approval_threshold)}</span>
          )}
        </div>
      </div>

      {/* Store Header */}
      <header className="sticky top-0 z-30 bg-[#0b0e14]/90 backdrop-blur-md border-b border-[#232a3a] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#3395ff] to-[#2fd180] flex items-center justify-center text-black font-black text-xl shadow-lg shadow-[#3395ff]/20">
              RG
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-[#e8ecf4] flex items-center gap-2">
                {storeInfo.store_name}
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-[#2fd180]/10 text-[#2fd180] border border-[#2fd180]/30">
                  Verified
                </span>
              </h1>
              <p className="text-xs text-[#8b94a8]">Grounded AI Commerce Catalog</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* AI Assistant Toggle Button */}
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#191f2c] hover:bg-[#232a3a] border border-[#232a3a] text-sm font-medium transition-all cursor-pointer group"
            >
              <span className="text-base group-hover:scale-110 transition-transform">🤖</span>
              <span className="hidden sm:inline">Ask AI Agent</span>
            </button>

            {/* Shopping Cart Button */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative flex items-center gap-2.5 px-4 py-2 rounded-xl bg-[#3395ff] text-black font-semibold text-sm hover:bg-[#3395ff]/90 transition-all shadow-lg shadow-[#3395ff]/20 cursor-pointer"
            >
              <span>🛒</span>
              <span>Cart</span>
              {totalItemCount > 0 && (
                <span className="w-5 h-5 rounded-full bg-black text-[#3395ff] text-xs font-bold flex items-center justify-center">
                  {totalItemCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Notice Modal / Banner if any */}
        {checkoutNotice && (
          <div
            className={`p-5 rounded-2xl border transition-all ${
              checkoutNotice.type === "success"
                ? "bg-[#2fd180]/10 border-[#2fd180]/40 text-[#2fd180]"
                : checkoutNotice.type === "approval"
                ? "bg-[#ffb020]/10 border-[#ffb020]/40 text-[#ffb020]"
                : "bg-[#ff5c5c]/10 border-[#ff5c5c]/40 text-[#ff5c5c]"
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-base flex items-center gap-2">
                  {checkoutNotice.type === "success" && "🎉 Order Confirmed & Paid"}
                  {checkoutNotice.type === "approval" && "⏳ Order Pending Merchant Approval"}
                  {checkoutNotice.type === "error" && "⚠️ Checkout Action Notice"}
                </h3>
                <p className="text-sm mt-1 text-[#e8ecf4]">{checkoutNotice.message}</p>
                {checkoutNotice.orderId && (
                  <div className="mt-3 flex flex-wrap gap-4 text-xs font-mono text-[#8b94a8]">
                    <span className="bg-[#12161f] px-3 py-1 rounded border border-[#232a3a]">
                      Order #{checkoutNotice.orderId}
                    </span>
                    {checkoutNotice.paymentId && (
                      <span className="bg-[#12161f] px-3 py-1 rounded border border-[#232a3a]">
                        Payment: {checkoutNotice.paymentId}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <button
                onClick={() => setCheckoutNotice(null)}
                className="text-[#8b94a8] hover:text-[#e8ecf4] text-lg font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Hero & AI Sales Agent Quick Trigger */}
        <section className="bg-gradient-to-r from-[#12161f] via-[#191f2c] to-[#12161f] border border-[#232a3a] rounded-3xl p-6 sm:p-8 relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-[#3395ff]/10 to-transparent pointer-events-none" />
          <div className="max-w-2xl">
            <span className="text-xs font-mono uppercase text-[#3395ff] tracking-wider font-semibold">
              Autonomous Sales Concierge
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold mt-1 tracking-tight text-[#e8ecf4]">
              Grounded AI Purchasing with Real-Time Policies
            </h2>
            <p className="text-sm text-[#8b94a8] mt-2 leading-relaxed">
              Explore catalog products, check guaranteed compatibility, and test seamless Razorpay checkout with policy-bound safety.
            </p>

            <div className="mt-5 flex flex-wrap gap-2">
              <button
                onClick={() => {
                  setChatOpen(true);
                  handleSendMessage("Show me high-performance laptops for coding");
                }}
                className="text-xs px-3.5 py-2 rounded-xl bg-[#0b0e14]/60 hover:bg-[#3395ff]/20 border border-[#232a3a] hover:border-[#3395ff]/50 text-[#e8ecf4] transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span>💻</span> "Show me laptops for coding"
              </button>
              <button
                onClick={() => {
                  setChatOpen(true);
                  handleSendMessage("Recommend a gaming setup under ₹70,000");
                }}
                className="text-xs px-3.5 py-2 rounded-xl bg-[#0b0e14]/60 hover:bg-[#3395ff]/20 border border-[#232a3a] hover:border-[#3395ff]/50 text-[#e8ecf4] transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span>🎮</span> "Gaming setup under ₹70,000"
              </button>
              <button
                onClick={() => {
                  setChatOpen(true);
                  handleSendMessage("What accessories are compatible with my items?");
                }}
                className="text-xs px-3.5 py-2 rounded-xl bg-[#0b0e14]/60 hover:bg-[#3395ff]/20 border border-[#232a3a] hover:border-[#3395ff]/50 text-[#e8ecf4] transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span>⚡</span> "Suggest compatible accessories"
              </button>
            </div>
          </div>
        </section>

        {/* Search & Categories Bar */}
        <section className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          {/* Category Chips */}
          <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2 rounded-xl text-xs font-medium capitalize transition-all cursor-pointer whitespace-nowrap ${
                  selectedCategory === cat
                    ? "bg-[#3395ff] text-black font-semibold shadow-md shadow-[#3395ff]/20"
                    : "bg-[#12161f] hover:bg-[#191f2c] border border-[#232a3a] text-[#8b94a8] hover:text-[#e8ecf4]"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-72">
            <input
              type="text"
              placeholder="Search products or tags..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#12161f] border border-[#232a3a] rounded-xl px-4 py-2 pl-9 text-xs text-[#e8ecf4] placeholder-[#8b94a8] focus:outline-none focus:border-[#3395ff] transition-all"
            />
            <span className="absolute left-3 top-2.5 text-xs text-[#8b94a8]">🔍</span>
          </div>
        </section>

        {/* Product Catalog Grid */}
        <section>
          {filteredProducts.length === 0 ? (
            <div className="text-center py-16 bg-[#12161f] border border-[#232a3a] rounded-2xl">
              <span className="text-3xl">📦</span>
              <h3 className="text-lg font-semibold mt-2">No matching products found</h3>
              <p className="text-sm text-[#8b94a8] mt-1">Try clearing your search query or category filters.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProducts.map((product) => {
                const inCart = cart.find((i) => i.product.id === product.id);
                return (
                  <div
                    key={product.id}
                    className="bg-[#12161f] border border-[#232a3a] rounded-2xl p-5 flex flex-col justify-between hover:border-[#3395ff]/40 transition-all group"
                  >
                    <div>
                      {/* Top Badges */}
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[10px] uppercase font-mono px-2.5 py-1 rounded-md bg-[#191f2c] text-[#8b94a8] border border-[#232a3a]">
                          {product.category}
                        </span>
                        <span
                          className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                            product.inventory > 0
                              ? "bg-[#2fd180]/10 text-[#2fd180] border border-[#2fd180]/30"
                              : "bg-[#ff5c5c]/10 text-[#ff5c5c] border border-[#ff5c5c]/30"
                          }`}
                        >
                          {product.inventory > 0 ? `${product.inventory} in stock` : "Sold Out"}
                        </span>
                      </div>

                      {/* Title & Price */}
                      <h3 className="text-base font-bold text-[#e8ecf4] group-hover:text-[#3395ff] transition-colors">
                        {product.name}
                      </h3>
                      <div className="text-xl font-extrabold text-[#e8ecf4] mt-1">
                        {money(product.price)}
                      </div>

                      {/* Tags */}
                      {product.tags && product.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {product.tags.map((tag) => (
                            <span
                              key={tag}
                              className="text-[10px] px-2 py-0.5 rounded bg-[#191f2c] text-[#8b94a8]"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="mt-6 pt-4 border-t border-[#232a3a]">
                      <button
                        onClick={() => addToCart(product)}
                        disabled={product.inventory <= 0}
                        className={`w-full py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                          product.inventory <= 0
                            ? "bg-[#191f2c] text-[#8b94a8] cursor-not-allowed"
                            : inCart
                            ? "bg-[#2fd180]/10 text-[#2fd180] border border-[#2fd180]/30 hover:bg-[#2fd180]/20"
                            : "bg-[#3395ff] text-black hover:bg-[#3395ff]/90 shadow-md shadow-[#3395ff]/10"
                        }`}
                      >
                        <span>🛒</span>
                        <span>{inCart ? `In Cart (${inCart.quantity}) + Add More` : "Add to Cart"}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {/* Cart Drawer Modal */}
      {cartOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
            onClick={() => setCartOpen(false)}
          />

          <div className="relative w-full max-w-md bg-[#12161f] border-l border-[#232a3a] h-full flex flex-col justify-between shadow-2xl p-6 z-10 overflow-y-auto">
            <div>
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-[#232a3a]">
                <div className="flex items-center gap-2">
                  <span className="text-xl">🛒</span>
                  <h3 className="font-bold text-lg text-[#e8ecf4]">Shopping Cart</h3>
                  <span className="text-xs font-mono text-[#8b94a8]">({totalItemCount} items)</span>
                </div>
                <button
                  onClick={() => setCartOpen(false)}
                  className="text-[#8b94a8] hover:text-[#e8ecf4] p-1.5 rounded-lg hover:bg-[#191f2c] cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Items List */}
              <div className="py-4 space-y-3">
                {cart.length === 0 ? (
                  <div className="text-center py-12 text-[#8b94a8]">
                    <span className="text-4xl">🛍️</span>
                    <p className="mt-2 text-sm font-medium">Your cart is currently empty</p>
                    <button
                      onClick={() => setCartOpen(false)}
                      className="mt-4 text-xs text-[#3395ff] hover:underline cursor-pointer"
                    >
                      Browse Catalog
                    </button>
                  </div>
                ) : (
                  cart.map((item) => (
                    <div
                      key={item.product.id}
                      className="bg-[#191f2c] border border-[#232a3a] rounded-xl p-3 flex items-center justify-between"
                    >
                      <div className="flex-1 pr-2">
                        <h4 className="text-xs font-semibold text-[#e8ecf4] line-clamp-1">
                          {item.product.name}
                        </h4>
                        <div className="text-xs font-mono text-[#3395ff] mt-0.5">
                          {money(item.product.price)} each
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <div className="flex items-center bg-[#12161f] border border-[#232a3a] rounded-lg">
                          <button
                            onClick={() => updateQuantity(item.product.id, -1)}
                            className="px-2 py-0.5 text-xs text-[#8b94a8] hover:text-[#e8ecf4] cursor-pointer"
                          >
                            -
                          </button>
                          <span className="px-2 text-xs font-mono font-medium text-[#e8ecf4]">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => updateQuantity(item.product.id, 1)}
                            className="px-2 py-0.5 text-xs text-[#8b94a8] hover:text-[#e8ecf4] cursor-pointer"
                          >
                            +
                          </button>
                        </div>

                        <button
                          onClick={() => removeFromCart(item.product.id)}
                          className="text-[#ff5c5c] hover:bg-[#ff5c5c]/10 p-1.5 rounded-lg text-xs cursor-pointer"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Checkout Footer */}
            {cart.length > 0 && (
              <div className="pt-4 border-t border-[#232a3a] space-y-4">
                {/* Customer Prefill Info */}
                <div className="space-y-2">
                  <label className="text-[11px] font-mono text-[#8b94a8] uppercase">
                    Customer Details (Demo)
                  </label>
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full bg-[#0b0e14] border border-[#232a3a] rounded-lg px-3 py-1.5 text-xs text-[#e8ecf4] focus:outline-none focus:border-[#3395ff]"
                  />
                  <input
                    type="email"
                    placeholder="Email Address"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    className="w-full bg-[#0b0e14] border border-[#232a3a] rounded-lg px-3 py-1.5 text-xs text-[#e8ecf4] focus:outline-none focus:border-[#3395ff]"
                  />
                </div>

                {/* Subtotal */}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[#8b94a8]">Order Subtotal</span>
                  <span className="text-lg font-bold text-[#e8ecf4] font-mono">
                    {money(cartSubtotal)}
                  </span>
                </div>

                {/* Policy Warning if above approval threshold */}
                {storeInfo.approval_threshold && cartSubtotal >= storeInfo.approval_threshold && (
                  <div className="p-2.5 rounded-lg bg-[#ffb020]/10 border border-[#ffb020]/30 text-[#ffb020] text-xs">
                    ⚠️ Order total meets or exceeds the store approval limit ({money(storeInfo.approval_threshold)}). It will trigger merchant HITL approval.
                  </div>
                )}

                {/* Checkout Trigger */}
                <button
                  onClick={handleCheckout}
                  disabled={checkingOut}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-[#3395ff] to-[#2fd180] text-black font-bold text-sm hover:opacity-95 transition-all shadow-lg shadow-[#3395ff]/20 cursor-pointer disabled:opacity-50"
                >
                  {checkingOut ? "Preparing Razorpay Order..." : `Pay ${money(cartSubtotal)} (Test Mode)`}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Sales Agent Assistant Drawer */}
      {chatOpen && (
        <div className="fixed bottom-6 right-6 z-40 w-full max-w-sm sm:max-w-md bg-[#12161f] border border-[#232a3a] rounded-3xl shadow-2xl flex flex-col h-[520px] overflow-hidden">
          {/* Header */}
          <div className="bg-[#191f2c] border-b border-[#232a3a] p-4 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-[#3395ff]/20 text-[#3395ff] flex items-center justify-center font-bold">
                🤖
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#e8ecf4]">Store AI Concierge</h4>
                <p className="text-[10px] text-[#2fd180] flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#2fd180] inline-block" />
                  Grounded in Store Catalog
                </p>
              </div>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="text-[#8b94a8] hover:text-[#e8ecf4] p-1 cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs ledger-scroll">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[#3395ff] text-black font-medium"
                      : "bg-[#191f2c] text-[#e8ecf4] border border-[#232a3a]"
                  }`}
                >
                  {msg.content}
                </div>

                {/* Grounded Recommended Product Card */}
                {msg.recommendedProduct && (
                  <div className="mt-2 w-full max-w-[85%] bg-[#0b0e14] border border-[#3395ff]/40 rounded-xl p-3 shadow-md">
                    <span className="text-[9px] uppercase font-mono text-[#3395ff] font-bold">
                      ★ Recommended Pick
                    </span>
                    <h5 className="font-bold text-xs text-[#e8ecf4] mt-0.5">
                      {msg.recommendedProduct.name}
                    </h5>
                    <div className="text-sm font-extrabold text-[#2fd180] mt-1">
                      {money(msg.recommendedProduct.price)}
                    </div>
                    <button
                      onClick={() => addToCart(msg.recommendedProduct!)}
                      className="mt-2 w-full py-1.5 bg-[#3395ff] text-black font-semibold text-[11px] rounded-lg hover:bg-[#3395ff]/90 cursor-pointer"
                    >
                      + Add to Cart
                    </button>
                  </div>
                )}

                {/* Grounded Recommended Upsell Card */}
                {msg.recommendedUpsell && (
                  <div className="mt-1.5 w-full max-w-[85%] bg-[#0b0e14] border border-[#2fd180]/40 rounded-xl p-3 shadow-md">
                    <span className="text-[9px] uppercase font-mono text-[#2fd180] font-bold">
                      ⚡ Compatible Companion
                    </span>
                    <h5 className="font-bold text-xs text-[#e8ecf4] mt-0.5">
                      {msg.recommendedUpsell.name}
                    </h5>
                    <div className="text-sm font-extrabold text-[#e8ecf4] mt-1">
                      {money(msg.recommendedUpsell.price)}
                    </div>
                    <button
                      onClick={() => addToCart(msg.recommendedUpsell!)}
                      className="mt-2 w-full py-1.5 bg-[#2fd180] text-black font-semibold text-[11px] rounded-lg hover:bg-[#2fd180]/90 cursor-pointer"
                    >
                      + Bundle Addon
                    </button>
                  </div>
                )}
              </div>
            ))}

            {chatLoading && (
              <div className="flex items-center gap-2 text-[#8b94a8] text-xs">
                <span className="w-2 h-2 rounded-full bg-[#3395ff] animate-ping" />
                <span>Agent checking merchant inventory...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="p-3 bg-[#191f2c] border-t border-[#232a3a] flex gap-2">
            <input
              type="text"
              placeholder="Ask anything about the catalog..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              className="flex-1 bg-[#12161f] border border-[#232a3a] rounded-xl px-3 py-2 text-xs text-[#e8ecf4] focus:outline-none focus:border-[#3395ff]"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={chatLoading}
              className="px-3.5 py-2 bg-[#3395ff] text-black font-bold rounded-xl text-xs hover:bg-[#3395ff]/90 cursor-pointer disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
