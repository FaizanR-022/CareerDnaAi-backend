"use client";

import React, { useState } from "react";

export default function SpecsTab({ difficulty, testCoverage, setTestCoverage }) {
  const [gapInput, setGapInput] = useState("");
  const [hardGapConflict, setHardGapConflict] = useState("");
  const [hardGapResolution, setHardGapResolution] = useState("");

  const [submitted, setSubmitted] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [success, setSuccess] = useState(false);

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    if (!gapInput.trim()) return;

    const lower = gapInput.toLowerCase();
    if (lower.includes("password") || lower.includes("complexity") || lower.includes("character") || lower.includes("length")) {
      setSuccess(true);
      setFeedback("Gap Analysis Accepted! You correctly identified that password complexity criteria (minimum 8 characters, special character requirements) were missing from the functional specs. Test Coverage increased +15%.");
      setTestCoverage(Math.min(testCoverage + 15, 100));
    } else {
      setSuccess(false);
      setFeedback("Gap Analysis Rejected: The product team notes that your input does not target the core missing validation specification. Hint: Look at the Password credentials section.");
    }
    setSubmitted(true);
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    if (!hardGapConflict.trim() || !hardGapResolution.trim()) return;

    const lowerConflict = hardGapConflict.toLowerCase();
    const lowerResolution = hardGapResolution.toLowerCase();

    // Check if they identify guest checkout vs registration conflict
    const identifiedConflict = (lowerConflict.includes("guest") || lowerConflict.includes("checkout")) && 
                               (lowerConflict.includes("register") || lowerConflict.includes("registration") || lowerConflict.includes("sign up"));
    
    if (identifiedConflict && hardGapResolution.length > 20) {
      setSuccess(true);
      setFeedback("Conflicts Identified & Resolved! You correctly caught the critical conflict between Section 1.1 (mandatory registration) and Section 2.4 (guest checkout bypass). The proposed flow resolution is logged. Test Coverage increased +25%.");
      setTestCoverage(Math.min(testCoverage + 25, 100));
    } else {
      setSuccess(false);
      setFeedback("Triage Rejected: The identified gap is incorrect or the resolution is too brief. Ensure you outline the conflict between registration constraints (Sec 1.1) and guest checkout (Sec 2.4).");
    }
    setSubmitted(true);
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: SPEC ANALYSIS */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Requirement Blueprint & Specs</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Review the PRD specs to build your test cases and isolate logic gaps.</p>
        </div>

        {/* EASY DIFFICULTY: Visual Blueprint and color-coded list */}
        {difficulty === "easy" && (
          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-outline-variant/30 rounded-2xl p-6 shadow-sm">
              <h3 className="font-label-md text-label-md font-bold text-on-surface mb-4">Registration Flow Blueprint</h3>
              
              {/* Visual Flow diagram */}
              <div className="flex items-center justify-around bg-surface-container-low p-4 rounded-xl border border-outline-variant/20 mb-6 font-mono text-[11px] text-center">
                <div className="p-3 bg-green-100 text-green-800 rounded-lg border border-green-300 w-36 shadow-sm">
                  <span className="font-bold block uppercase mb-1">Step 1: Input</span>
                  Email & Password Input fields
                </div>
                <span className="material-symbols-outlined text-outline">arrow_forward</span>
                <div className="p-3 bg-blue-100 text-blue-800 rounded-lg border border-blue-300 w-36 shadow-sm">
                  <span className="font-bold block uppercase mb-1">Step 2: Validation</span>
                  Check regex format & length rules
                </div>
                <span className="material-symbols-outlined text-outline">arrow_forward</span>
                <div className="p-3 bg-red-100 text-red-800 rounded-lg border border-red-300 w-36 shadow-sm">
                  <span className="font-bold block uppercase mb-1">Step 3: Gateway</span>
                  Stripe Payment verification
                </div>
              </div>

              {/* Color coded Specs key */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 border-l-4 border-green-500 bg-green-50/50 rounded-r-lg">
                  <h4 className="font-label-sm text-xs font-bold text-green-800 mb-1">Email Specifications</h4>
                  <p className="font-body-sm text-[11px] text-on-surface-variant">Requires standard regex formatting. Must contain &quot;@&quot; and domain extension.</p>
                </div>
                <div className="p-3 border-l-4 border-blue-500 bg-blue-50/50 rounded-r-lg">
                  <h4 className="font-label-sm text-xs font-bold text-blue-800 mb-1">Password Specifications</h4>
                  <p className="font-body-sm text-[11px] text-on-surface-variant">Must be minimum 8 characters. Requires at least 1 uppercase and 1 special symbol.</p>
                </div>
                <div className="p-3 border-l-4 border-red-500 bg-red-50/50 rounded-r-lg">
                  <h4 className="font-label-sm text-xs font-bold text-red-800 mb-1">Stripe Checkout Specs</h4>
                  <p className="font-body-sm text-[11px] text-on-surface-variant">Card number verified by Luhn algorithm. CVV and Expiry fields mandatory.</p>
                </div>
              </div>
            </div>

            <div className="bg-primary-fixed border border-primary-fixed-dim rounded-xl p-4 flex gap-3 items-center">
              <span className="material-symbols-outlined text-[24px] text-primary">lightbulb</span>
              <div>
                <h4 className="font-label-md text-label-md font-bold text-on-primary-fixed">Guided Tip</h4>
                <p className="font-body-sm text-[12px] text-on-primary-fixed-variant">Review the colors on the flow. These directly correlate with field triggers in the Test Execution tab.</p>
              </div>
            </div>
          </div>
        )}

        {/* MEDIUM DIFFICULTY: Plain text PRD and single gap input */}
        {difficulty === "medium" && (
          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm font-body-sm text-[13px] text-on-surface-variant leading-relaxed">
              <h3 className="font-label-md text-[15px] font-bold text-on-surface mb-3 pb-2 border-b border-outline-variant/20">PRD Segment: Account Authentication Flow</h3>
              <p className="mb-2"><strong>1. Functional Overview:</strong> The system will present a signup form requesting a username (email) and password credentials. Upon submission, the app will execute checks prior to sending payload requests to database schema storage.</p>
              <p className="mb-2"><strong>2. Credentials Validation Specifications:</strong></p>
              <ul className="list-disc pl-5 mb-3 flex flex-col gap-1">
                <li>Username input field: Requires a string matching standard email syntax rules. Empty states must block submit requests.</li>
                <li>Password input field: Requires characters to be inputted. The system must confirm validation checks pass before saving accounts. <em>(Note: Specific password strength or length complexity thresholds are not defined in current release guidelines).</em></li>
              </ul>
              <p><strong>3. Payment Interface:</strong> Stripe elements integration. Requires Luhn-validated card numbers, correct expiration dates, and 3-digit CVV configurations.</p>
            </div>

            {submitted ? (
              <div className={`p-4 rounded-xl border ${success ? "bg-primary/5 border-primary text-primary" : "bg-error-container/20 border-error text-error"}`}>
                <div className="flex items-start gap-3">
                  <span className="material-symbols-outlined mt-0.5">{success ? "check_circle" : "warning"}</span>
                  <div>
                    <h4 className="font-label-md text-label-md font-bold">{success ? "Gap Analysis Successful" : "Analysis Rejected"}</h4>
                    <p className="font-body-sm text-[12px] mt-1 leading-relaxed">{feedback}</p>
                    {!success && (
                      <button onClick={() => setSubmitted(false)} className="mt-2 text-xs underline font-semibold focus:outline-none">
                        Try Again
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <form onSubmit={handleMediumSubmit} className="bg-surface-container border border-outline-variant/30 rounded-xl p-5 shadow-sm flex flex-col gap-4">
                <div>
                  <h4 className="font-label-md text-label-md font-bold text-on-surface mb-1">Requirement Gap Analysis</h4>
                  <p className="font-body-sm text-[12px] text-outline">Examine Section 2 (Password validation) above. Identify what crucial validation specification is missing.</p>
                </div>
                <div className="flex flex-col gap-1.5">
                  <input
                    type="text"
                    value={gapInput}
                    onChange={(e) => setGapInput(e.target.value)}
                    placeholder="Enter missing requirement (e.g. Password character length/complexity rule)..."
                    className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!gapInput.trim()}
                  className="self-end py-2 px-5 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline/30 disabled:cursor-not-allowed transition-all"
                >
                  Submit Gap Analysis
                </button>
              </form>
            )}
          </div>
        )}

        {/* HARD DIFFICULTY: Raw conflicts, multiple resolution inputs */}
        {difficulty === "hard" && (
          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm font-mono text-xs text-on-surface-variant leading-relaxed">
              <h3 className="font-label-md text-[14px] font-bold text-on-surface mb-3 pb-2 border-b border-outline-variant/20">{"// RAW SYSTEM SPECIFICATION DUMP"}</h3>
              <div className="flex flex-col gap-3">
                <div>
                  <span className="text-primary font-bold">SECTION 1.1: REGISTRATION FLOW</span>
                  <p className="pl-4 mt-1">To ensure platform security and support recurring invoicing, the checkout system must block guest session paths. All purchase routes require account creation first. The user MUST register with a valid email and unique password before inputting card details on the Stripe payment interface.</p>
                </div>
                <div>
                  <span className="text-primary font-bold">SECTION 2.4: CHECKOUT PROCESS</span>
                  <p className="pl-4 mt-1">Guest checkout paths must remain operational to decrease checkout attrition rates. Users can submit direct card payments by inputting payment details and emails. Stripe authorization queries will bypass account registration validation rules and checkout user immediately.</p>
                </div>
                <div>
                  <span className="text-primary font-bold">SECTION 3.0: STAKEHOLDER CONSTRAINTS</span>
                  <p className="pl-4 mt-1">Stripe Element must only load within secure iframe containers. Forms must execute silent client checks prior to triggering transaction logs.</p>
                </div>
              </div>
            </div>

            {submitted ? (
              <div className={`p-4 rounded-xl border ${success ? "bg-primary/5 border-primary text-primary" : "bg-error-container/20 border-error text-error"}`}>
                <div className="flex items-start gap-3">
                  <span className="material-symbols-outlined mt-0.5">{success ? "check_circle" : "warning"}</span>
                  <div>
                    <h4 className="font-label-md text-label-md font-bold">{success ? "Triage Successful" : "Triage Rejected"}</h4>
                    <p className="font-body-sm text-[12px] mt-1 leading-relaxed">{feedback}</p>
                    {!success && (
                      <button onClick={() => setSubmitted(false)} className="mt-2 text-xs underline font-semibold focus:outline-none">
                        Try Again
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <form onSubmit={handleHardSubmit} className="bg-surface-container border border-outline-variant/30 rounded-xl p-5 shadow-sm flex flex-col gap-4">
                <div>
                  <h4 className="font-label-md text-label-md font-bold text-on-surface mb-1">Gap Analysis: Conflicting Requirements</h4>
                  <p className="font-body-sm text-[12px] text-outline">Identify the primary system design conflict and propose a logical compromise flow.</p>
                </div>
                
                <div className="flex flex-col gap-3">
                  <div className="flex flex-col gap-1">
                    <label className="font-label-sm text-[11px] text-outline font-semibold">1. Describe the conflict between Section 1.1 and Section 2.4:</label>
                    <textarea
                      value={hardGapConflict}
                      onChange={(e) => setHardGapConflict(e.target.value)}
                      placeholder="Identify the clash between mandatory registration requirements and guest checkout session rules..."
                      className="w-full h-20 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[13px] resize-none outline-none transition-all"
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="font-label-sm text-[11px] text-outline font-semibold">2. Propose a functional resolution specification:</label>
                    <textarea
                      value={hardGapResolution}
                      onChange={(e) => setHardGapResolution(e.target.value)}
                      placeholder="Outline a compromise (e.g. guest checkout allowed, with optional account setup post-payment)..."
                      className="w-full h-20 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[13px] resize-none outline-none transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!hardGapConflict.trim() || !hardGapResolution.trim()}
                  className="self-end py-2 px-5 bg-error text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container disabled:bg-outline/30 disabled:cursor-not-allowed transition-all"
                >
                  Submit Conflict Report
                </button>
              </form>
            )}
          </div>
        )}
      </div>

      {/* RIGHT PANEL: QA FRAMEWORK */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">gavel</span>
          QA Framework
        </h3>

        <div className="flex flex-col gap-4 font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Requirement Traceability</h4>
            <p>Every test case must trace back to a specific PRD line item. Logic gaps identified here must be reported in the Bug Reporting workspace as specification defects.</p>
          </div>

          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Conflict Triage</h4>
            <p>Conflicting requirements are blocks. If two acceptance criteria contradict each other, the QA lead must flag the ticket back to Product for revision before tests execute.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
