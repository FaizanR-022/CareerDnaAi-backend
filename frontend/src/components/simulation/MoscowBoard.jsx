"use client";

import React, { useState, useEffect } from "react";

const INITIAL_CARDS = {
  easy: [
    { id: "uauth", title: "User Authentication", desc: "Email + OAuth login flow for security.", hint: "Hint: Core blocker", type: "Feature", col: "must" },
    { id: "stripe", title: "Checkout v1", desc: "Single-currency Stripe integration flow.", hint: "Hint: Revenue critical", type: "Feature", col: "must" },
    { id: "avatar", title: "Profile Avatar Upload", desc: "Basic image crop and resize functionality.", hint: "User Story Hint", type: "Feature", col: "should" },
    { id: "search", title: "Search Filters", desc: "Category and price range selection.", hint: "UX Improvement", type: "Feature", col: "should" },
    { id: "dark", title: "Dark Mode", desc: "User preference toggle.", hint: "Visual Polish", type: "Feature", col: "could" },
    { id: "ios", title: "Native iOS App", desc: "Out of scope for Sprint 1.", hint: "Out of Scope", type: "Feature", col: "wont" }
  ],
  medium: [
    { id: "uauth", title: "User Authentication", desc: "Email + OAuth login flow", type: "Feature", col: "must" },
    { id: "stripe", title: "Checkout v1", desc: "Single-currency Stripe flow", type: "Feature", col: "must" },
    { id: "email", title: "Order Confirmation Email", desc: "Triggered on payment success", type: "Feature", col: "must" },
    { id: "wishlist", title: "Wishlist", desc: "Save items for later", type: "Feature", col: "should" },
    { id: "search", title: "Search Filters", desc: "Category + price range", type: "Feature", col: "should" },
    { id: "avatar", title: "Profile Avatar Upload", desc: "Image crop + resize", type: "Feature", col: "should" },
    { id: "dark", title: "Dark Mode", desc: "User preference toggle", type: "Feature", col: "could" },
    { id: "referral", title: "Referral Codes", desc: "Friends-invite flow", type: "Feature", col: "could" },
    { id: "ios", title: "Native iOS App", desc: "Out of scope for Sprint 1", type: "Feature", col: "wont" },
    { id: "chatbot", title: "AI Stylist Chatbot", desc: "Deferred to Q3", type: "Feature", col: "wont" }
  ],
  hard: [
    { id: "uauth", title: "User Authentication", desc: "Email + OAuth login flow", type: "Feature", col: "must" },
    { id: "stripe", title: "Checkout v1", desc: "Single-currency Stripe flow", type: "Feature", col: "must" },
    { id: "email", title: "Order Confirmation Email", desc: "Triggered on payment success", type: "Feature", col: "must" },
    { id: "dbmig", title: "Database Migrations & Rollback", desc: "Ensure hotfix capabilities for database crashes", type: "DevOps", col: "must" },
    { id: "wishlist", title: "Wishlist", desc: "Save items for later", type: "Feature", col: "should" },
    { id: "search", title: "Search Filters", desc: "Category + price range", type: "Feature", col: "should" },
    { id: "avatar", title: "Profile Avatar Upload", desc: "Image crop + resize", type: "Feature", col: "should" },
    { id: "cartpersistence", title: "Cart Session Persistence", desc: "Sync carts across guest and logged-in states", type: "Feature", col: "should" },
    { id: "dark", title: "Dark Mode", desc: "User preference toggle", type: "Feature", col: "could" },
    { id: "referral", title: "Referral Codes", desc: "Friends-invite flow", type: "Feature", col: "could" },
    { id: "ios", title: "Native iOS App", desc: "Out of scope for Sprint 1", type: "Feature", col: "wont" },
    { id: "chatbot", title: "AI Stylist Chatbot", desc: "Deferred to Q3", type: "Feature", col: "wont" }
  ]
};

export default function MoscowBoard({ difficulty }) {
  const [cards, setCards] = useState([]);
  const [showAddForm, setShowAddForm] = useState(null); // 'must' | 'should' | 'could' | 'wont' | null
  const [newCardTitle, setNewCardTitle] = useState("");
  const [newCardDesc, setNewCardDesc] = useState("");

  // Sync cards with difficulty
  useEffect(() => {
    setCards(JSON.parse(JSON.stringify(INITIAL_CARDS[difficulty] || INITIAL_CARDS.medium)));
  }, [difficulty]);

  // Drag & Drop handlers
  const handleDragStart = (e, cardId) => {
    e.dataTransfer.setData("text/plain", cardId);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e, targetCol) => {
    e.preventDefault();
    const cardId = e.dataTransfer.getData("text/plain");
    if (!cardId) return;

    setCards((prevCards) =>
      prevCards.map((card) => (card.id === cardId ? { ...card, col: targetCol } : card))
    );
  };

  const handleAddCard = (e, column) => {
    e.preventDefault();
    if (!newCardTitle.trim()) return;

    const newCard = {
      id: `custom_${Date.now()}`,
      title: newCardTitle,
      desc: newCardDesc || "Custom feature card added during simulation.",
      type: "Feature",
      col: column,
      hint: difficulty === "easy" ? "User created card" : undefined
    };

    setCards((prev) => [...prev, newCard]);
    setNewCardTitle("");
    setNewCardDesc("");
    setShowAddForm(null);
  };

  const getColCards = (colName) => cards.filter((c) => c.col === colName);

  const getColumns = () => [
    {
      id: "must",
      title: "Must Have",
      colorClass: "bg-primary-container",
      opacityClass: "opacity-100",
      borderClass: difficulty === "easy" ? "border-primary-fixed-dim" : "border-outline-variant/40"
    },
    {
      id: "should",
      title: "Should Have",
      colorClass: difficulty === "easy" ? "bg-primary-fixed-dim" : "bg-primary-fixed",
      opacityClass: difficulty === "hard" ? "opacity-90" : "opacity-100",
      borderClass: "border-outline-variant/40"
    },
    {
      id: "could",
      title: "Could Have",
      colorClass: "bg-outline-variant",
      opacityClass: "opacity-80",
      borderClass: "border-outline-variant/40"
    },
    {
      id: "wont",
      title: "Won't Have",
      colorClass: "bg-error-container",
      opacityClass: "opacity-60",
      borderClass: "border-outline-variant/40"
    }
  ];

  return (
    <div className="flex-1 p-gutter bg-surface-bright relative overflow-hidden flex flex-col h-full">
      {/* Drag Watermark Hint */}
      <div className="absolute top-4 right-8 bg-surface border border-outline-variant/30 shadow-sm rounded-full px-4 py-2 flex items-center gap-2 text-outline font-label-sm text-label-sm z-10">
        <span className="material-symbols-outlined text-[16px]">drag_indicator</span>
        Drag cards between columns
      </div>

      <div className="flex gap-6 overflow-x-auto pb-4 pt-8 kanban-scroll flex-1 h-full w-full">
        {getColumns().map((col) => {
          const colCards = getColCards(col.id);

          return (
            <div
              key={col.id}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, col.id)}
              className={`flex-1 min-w-[220px] lg:min-w-[240px] flex flex-col gap-4 transition-all duration-300 ${col.opacityClass}`}
            >
              {/* Column Header */}
              <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${col.colorClass}`}></div>
                  <h3 className={`font-bold text-on-surface tracking-tight ${
                    difficulty === "hard" ? "text-[16px]" : "text-[18px]"
                  }`}>
                    {col.title}
                  </h3>
                </div>
                <span className="bg-surface-container-high text-on-surface-variant w-6 h-6 rounded-full flex items-center justify-center font-label-sm text-label-sm border border-outline-variant/10 shadow-sm">
                  {colCards.length}
                </span>
              </div>

              {/* Card List Area */}
              <div className="flex flex-col gap-3 min-h-[400px] bg-black/[0.01] rounded-xl p-1 border border-dashed border-outline-variant/10">
                {colCards.map((card) => (
                  <div
                    key={card.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, card.id)}
                    className={`bg-surface rounded-xl shadow-sm border hover:shadow-md transition-all duration-200 cursor-grab active:cursor-grabbing flex flex-col gap-3 relative group overflow-hidden ${
                      difficulty === "easy" ? "p-5 border-primary-fixed-dim" : "p-4 border-outline-variant/40"
                    } ${difficulty === "hard" ? "p-3 gap-2" : ""}`}
                  >
                    {/* Left color bar for easy cards */}
                    {difficulty === "easy" && (
                      <div className={`absolute top-0 left-0 w-1 h-full opacity-50 ${col.colorClass}`}></div>
                    )}

                    <div className="flex justify-between items-start gap-1">
                      <h4 className={`font-label-md text-on-surface font-bold ${
                        difficulty === "hard" ? "text-[13px] leading-tight" : "text-[15px]"
                      }`}>
                        {card.title}
                      </h4>
                      <button className="text-outline-variant hover:text-primary transition-colors shrink-0">
                        <span className="material-symbols-outlined text-[18px]">more_horiz</span>
                      </button>
                    </div>

                    <p className={`font-body-sm text-on-surface-variant ${
                      difficulty === "hard" ? "text-[12px] leading-tight" : "text-body-sm"
                    }`}>
                      {card.desc}
                    </p>

                    {/* Hints (Easy Mode only) */}
                    {difficulty === "easy" && card.hint && (
                      <div className="mt-1 inline-flex items-center gap-1.5 bg-primary-fixed/30 text-primary px-2.5 py-1 rounded-md w-fit">
                        <span className="material-symbols-outlined text-[14px]">emoji_objects</span>
                        <span className="font-label-sm text-label-sm font-medium">{card.hint}</span>
                      </div>
                    )}

                    {/* Standard tags for Medium/Hard */}
                    {difficulty !== "easy" && (
                      <div className="flex justify-between items-center mt-1 border-t border-outline-variant/10 pt-2 shrink-0">
                        <span className="bg-surface-container text-on-surface-variant px-2 py-0.5 rounded font-label-sm text-[11px]">
                          {card.type}
                        </span>
                        <span className="material-symbols-outlined text-outline text-[18px]">
                          sentiment_satisfied
                        </span>
                      </div>
                    )}
                  </div>
                ))}

                {/* Inline Card Add Form */}
                {showAddForm === col.id ? (
                  <form
                    onSubmit={(e) => handleAddCard(e, col.id)}
                    className="bg-surface rounded-xl p-4 border border-primary flex flex-col gap-3 shadow-md"
                  >
                    <input
                      type="text"
                      required
                      placeholder="Card Title..."
                      value={newCardTitle}
                      onChange={(e) => setNewCardTitle(e.target.value)}
                      className="border border-outline-variant rounded px-2.5 py-1.5 text-sm focus:outline-none focus:border-primary w-full bg-surface"
                    />
                    <textarea
                      placeholder="Card Description..."
                      value={newCardDesc}
                      onChange={(e) => setNewCardDesc(e.target.value)}
                      className="border border-outline-variant rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary w-full bg-surface h-16 resize-none"
                    />
                    <div className="flex gap-2 justify-end">
                      <button
                        type="button"
                        onClick={() => {
                          setShowAddForm(null);
                          setNewCardTitle("");
                          setNewCardDesc("");
                        }}
                        className="px-3 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-xs text-on-surface-variant font-medium"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-3 py-1.5 rounded bg-primary text-on-primary text-xs font-semibold hover:bg-primary-container"
                      >
                        Save
                      </button>
                    </div>
                  </form>
                ) : (
                  <button
                    onClick={() => setShowAddForm(col.id)}
                    className="w-full py-3 rounded-xl border border-dashed border-outline-variant text-outline hover:text-on-surface hover:bg-surface-container transition-colors font-label-sm text-label-sm flex items-center justify-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[16px]">add</span> Add card
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
