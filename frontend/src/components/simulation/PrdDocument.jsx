"use client";

import React, { useState, useEffect } from "react";

// Define templates outside the component to keep the code clean and prevent unnecessary re-creations
const TEMPLATES = {
  easy: {
    title: "Acme E-Commerce Platform - Sprint 1",
    objective: "Enable basic online transaction processing by establishing a secure user sign-in route and standard payment processing pipeline.",
    audience: "Primary: Online shoppers seeking quick, secure checkouts.\nSecondary: Internal customer success representatives managing transactions.",
    requirements: "1. User Authentication: Email/password and OAuth (Google/GitHub) flows.\n2. Checkout v1: Single-currency Stripe payment widget integration.\n3. Confirmation Email: Automatic confirmation email dispatched upon Stripe webhook verification.",
    outOfScope: "Native mobile applications (iOS/Android), multi-currency pricing support, and automated AI style recommendations.",
    successMetrics: "1. Checkout success rate above 85%.\n2. Time-to-checkout average under 90 seconds.\n3. User signup conversion rate improvement by 15%.",
  },
  medium: {
    title: "Product Requirements Document (PRD)",
    objective: "[Outline: Describe the primary objective of this sprint here...]",
    audience: "Target users: Online retail shoppers.",
    requirements: "1. User Authentication (Must-Have)\n2. Checkout v1 Stripe flow (Must-Have)\n3. Search Filters (Should-Have)\n4. [Enter additional requirements here...]",
    outOfScope: "Mobile applications and advanced chatbot helpers.",
    successMetrics: "[Add key performance indicators here...]",
  },
  hard: {
    title: "",
    objective: "",
    audience: "",
    requirements: "",
    outOfScope: "",
    successMetrics: "",
  }
};

export default function PrdDocument({ difficulty }) {
  const [docData, setDocData] = useState(TEMPLATES.medium);
  const [activeMode, setActiveMode] = useState("edit"); // 'edit' | 'preview'
  const [isClient, setIsClient] = useState(false);

  // 1. Hydration & Initial Load: Check for saved drafts before applying templates
  useEffect(() => {
    setIsClient(true);
    const savedDraft = sessionStorage.getItem(`prd_draft_${difficulty}`);
    
    if (savedDraft) {
      setDocData(JSON.parse(savedDraft));
    } else {
      setDocData(TEMPLATES[difficulty] || TEMPLATES.medium);
    }
  }, [difficulty]);

  // 2. Auto-Save: Persist data to sessionStorage on every keystroke
  useEffect(() => {
    if (isClient) {
      sessionStorage.setItem(`prd_draft_${difficulty}`, JSON.stringify(docData));
    }
  }, [docData, difficulty, isClient]);

  const handleInputChange = (field, value) => {
    setDocData((prev) => ({ ...prev, [field]: value }));
  };

  // Prevent hydration mismatch flashes
  if (!isClient) return <div className="flex-1 bg-surface-bright h-full"></div>;

  return (
    <div className="flex-1 flex flex-col bg-surface-bright h-full overflow-hidden p-6 md:p-gutter">
      {/* Document Control Bar */}
      <div className="flex justify-between items-center mb-6 pb-4 border-b border-outline-variant/30 shrink-0">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">
            PRD Document View
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            {difficulty === "easy" && "Easy Mode: Fully guided template with structured instructions."}
            {difficulty === "medium" && "Medium Mode: Partially filled framework. Add details."}
            {difficulty === "hard" && "Hard Mode: Blank canvas. Complete the PRD from scratch."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveMode("edit")}
            className={`px-4 py-2 rounded-lg font-label-md text-label-md transition-all ${
              activeMode === "edit"
                ? "bg-primary text-on-primary shadow-sm"
                : "bg-surface border border-outline-variant text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            Edit
          </button>
          <button
            onClick={() => setActiveMode("preview")}
            className={`px-4 py-2 rounded-lg font-label-md text-label-md transition-all ${
              activeMode === "preview"
                ? "bg-primary text-on-primary shadow-sm"
                : "bg-surface border border-outline-variant text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            Preview Document
          </button>
        </div>
      </div>

      {/* Editor & View Container */}
      <div className="flex-1 overflow-y-auto bg-surface border border-outline-variant/35 rounded-2xl shadow-sm p-6 max-w-4xl mx-auto w-full mb-4">
        {activeMode === "edit" ? (
          <div className="flex flex-col gap-6">
            {/* Title */}
            <div className="flex flex-col gap-2">
              <label className="font-label-md text-label-md text-on-surface font-bold">Document Title</label>
              <input
                type="text"
                value={docData.title}
                onChange={(e) => handleInputChange("title", e.target.value)}
                placeholder="e.g. Acme Billing Dashboard PRD"
                className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-3 font-headline-md text-xl font-bold focus:outline-none focus:border-primary"
              />
              {difficulty === "easy" && (
                <span className="text-[12px] text-primary italic font-medium">
                  💡 Hint: Choose a descriptive title specifying the target features and sprint cycle.
                </span>
              )}
            </div>

            {/* Objective */}
            <div className="flex flex-col gap-2">
              <label className="font-label-md text-label-md text-on-surface font-bold">1. Product Objective</label>
              <textarea
                value={docData.objective}
                onChange={(e) => handleInputChange("objective", e.target.value)}
                placeholder="What objective does this feature solve? What are we trying to build?"
                rows={3}
                className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-3 font-body-sm text-body-sm focus:outline-none focus:border-primary resize-y"
              />
              {difficulty === "easy" && (
                <span className="text-[12px] text-primary italic font-medium">
                  💡 Hint: Write a 1-2 sentence high-level goal focusing on business and user outcomes.
                </span>
              )}
            </div>

            {/* Target Audience */}
            <div className="flex flex-col gap-2">
              <label className="font-label-md text-label-md text-on-surface font-bold">2. Target Audience</label>
              <textarea
                value={docData.audience}
                onChange={(e) => handleInputChange("audience", e.target.value)}
                placeholder="Describe your user personas and target market segments."
                rows={3}
                className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-3 font-body-sm text-body-sm focus:outline-none focus:border-primary resize-y"
              />
            </div>

            {/* Functional Requirements */}
            <div className="flex flex-col gap-2">
              <label className="font-label-md text-label-md text-on-surface font-bold">3. Functional Requirements</label>
              <textarea
                value={docData.requirements}
                onChange={(e) => handleInputChange("requirements", e.target.value)}
                placeholder="List requirements, features, user stories, and specs..."
                rows={6}
                className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-3 font-body-sm text-body-sm focus:outline-none focus:border-primary font-mono text-[13px] resize-y"
              />
              {difficulty === "easy" && (
                <span className="text-[12px] text-primary italic font-medium">
                  💡 Hint: Break features into itemized lines. Map these directly to your MoSCoW Must-Have and Should-Have columns.
                </span>
              )}
            </div>

            {/* Out of Scope */}
            <div className="flex flex-col gap-2">
              <label className="font-label-md text-label-md text-on-surface font-bold">4. Out of Scope (Won't Have)</label>
              <textarea
                value={docData.outOfScope}
                onChange={(e) => handleInputChange("outOfScope", e.target.value)}
                placeholder="Explicitly identify what will NOT be built in this sprint to prevent scope creep."
                rows={3}
                className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-3 font-body-sm text-body-sm focus:outline-none focus:border-primary resize-y"
              />
            </div>

            {/* Success Metrics */}
            <div className="flex flex-col gap-2">
              <label className="font-label-md text-label-md text-on-surface font-bold">5. Success Metrics & KPIs</label>
              <textarea
                value={docData.successMetrics}
                onChange={(e) => handleInputChange("successMetrics", e.target.value)}
                placeholder="Specify key metrics to validate this product post-deployment."
                rows={3}
                className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-3 font-body-sm text-body-sm focus:outline-none focus:border-primary resize-y"
              />
            </div>
          </div>
        ) : (
          /* Preview Mode Rendering - FIX: Added whitespace-pre-wrap to all elements */
          <article className="prose max-w-none text-on-surface flex flex-col gap-6">
            <header className="border-b border-outline-variant/30 pb-4 mb-4">
              <h1 className="text-3xl font-extrabold text-on-surface">
                {docData.title || "Untitled Product Requirements Document"}
              </h1>
              <p className="text-outline text-xs mt-2 uppercase tracking-wide">
                Status: Draft · Career DNA AI Product Simulation
              </p>
            </header>

            <section className="flex flex-col gap-2">
              <h3 className="font-bold text-lg text-primary border-l-4 border-primary pl-3">1. Product Objective</h3>
              <p className="text-on-surface-variant font-body-md bg-surface-container-low p-4 rounded-xl italic whitespace-pre-wrap">
                {docData.objective || "No objective provided yet."}
              </p>
            </section>

            <section className="flex flex-col gap-2">
              <h3 className="font-bold text-lg text-primary border-l-4 border-primary pl-3">2. Target Audience</h3>
              <p className="text-on-surface-variant font-body-md whitespace-pre-wrap">
                {docData.audience || "No audience description provided yet."}
              </p>
            </section>

            <section className="flex flex-col gap-2">
              <h3 className="font-bold text-lg text-primary border-l-4 border-primary pl-3">3. Functional Requirements</h3>
              <div className="bg-surface-container-lowest p-4 rounded-xl border border-outline-variant/20 font-mono text-[13px] whitespace-pre-wrap text-on-surface">
                {docData.requirements || "No functional requirements specified yet."}
              </div>
            </section>

            <section className="flex flex-col gap-2">
              <h3 className="font-bold text-lg text-primary border-l-4 border-primary pl-3">4. Out of Scope</h3>
              <p className="text-on-surface-variant font-body-md whitespace-pre-wrap">
                {docData.outOfScope || "No out of scope items identified."}
              </p>
            </section>

            <section className="flex flex-col gap-2">
              <h3 className="font-bold text-lg text-primary border-l-4 border-primary pl-3">5. Success Metrics & KPIs</h3>
              <p className="text-on-surface-variant font-body-md whitespace-pre-wrap">
                {docData.successMetrics || "No success metrics listed."}
              </p>
            </section>
          </article>
        )}
      </div>
    </div>
  );
}