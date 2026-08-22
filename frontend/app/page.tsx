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

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/products")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load products");
        }

        return response.json();
      })
      .then((data) => {
        setProducts(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not connect to the RazorGrow backend.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <main style={{ padding: 40 }}>Loading catalog...</main>;
  }

  if (error) {
    return <main style={{ padding: 40 }}>{error}</main>;
  }

  const filteredProducts = products.filter((product) => {
  const query = search.toLowerCase().trim();

  if (!query) {
    return true;
  }

  return (
    product.name.toLowerCase().includes(query) ||
    product.category.toLowerCase().includes(query) ||
    product.tags.some((tag) =>
      tag.toLowerCase().includes(query)
    ) ||
    product.use_cases.some((useCase) =>
      useCase.toLowerCase().includes(query)
    )
  );
});

  return (
    <main style={{ padding: 40 }}>
      <h1>RazorGrow Merchant Catalog</h1>
      <input
  type="text"
  placeholder="Search products..."
  value={search}
  onChange={(event) => setSearch(event.target.value)}
  style={{
    width: "100%",
    maxWidth: 500,
    padding: 12,
    marginTop: 20,
    border: "1px solid #ccc",
    borderRadius: 8,
  }}
/>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 20,
          marginTop: 30,
        }}
      >
        {filteredProducts.map((product) => (
          <article
            key={product.id}
            style={{
              border: "1px solid #ddd",
              borderRadius: 12,
              padding: 20,
            }}
          >
            <h2>{product.name}</h2>

            <p>
              <strong>
                ₹{product.price.toLocaleString("en-IN")}
              </strong>
            </p>

            <p>
              <strong>Category:</strong> {product.category}
            </p>

            <p>
              <strong>Inventory:</strong> {product.inventory}
            </p>

            <p>
              <strong>Use cases:</strong>{" "}
              {product.use_cases.join(", ")}
            </p>

            <p>
              <strong>Tags:</strong> {product.tags.join(", ")}
            </p>

            <button
              onClick={async () => {
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
                  `Price: ₹${details.price.toLocaleString("en-IN")}\n` +
                  `Category: ${details.category}\n` +
                  `Inventory: ${details.inventory}`
                );
              }}
              style={{
                marginTop: 15,
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid #ccc",
                cursor: "pointer",
              }}
            >
              View details
            </button>
          </article>

        ))}
      </div>
    </main>
  );
}