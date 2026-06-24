"use client";

import React, { useState } from "react";

export default function DesignReviewTab({ difficulty, a11yScore, setA11yScore }) {
  // Common states
  const [selectedMockup, setSelectedMockup] = useState(null); // 'A' or 'B'
  const [submitted, setSubmitted] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [success, setSuccess] = useState(false);

  // Medium States
  const [mediumReasons, setMediumReasons] = useState("");

  // Hard States
  const [primaryHex, setPrimaryHex] = useState("#0f172a");
  const [bgHex, setBgHex] = useState("#faf8ff");
  const [typoPair, setTypoPair] = useState("");
  const [hardExplanation, setHardExplanation] = useState("");

  const handleEasySubmit = (e) => {
    e.preventDefault();
    if (!selectedMockup) return;

    setSubmitted(true);
    if (selectedMockup === "A") {
      setSuccess(true);
      setFeedback("Correct choice! Design A conforms to proper HCI spacing alignments, readability scales, and WCAG AA contrast ratios (4.5:1). a11y Score +5%.");
      setA11yScore(Math.min(a11yScore + 5, 100));
    } else {
      setSuccess(false);
      setFeedback("Incorrect choice. Design B utilizes low-contrast text on bright blocks and suffers from spacing misalignment, breaking visual hierarchy.");
    }
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    if (!selectedMockup || !mediumReasons.trim()) return;

    setSubmitted(true);
    const lowerReasons = mediumReasons.toLowerCase();
    const hasContrastTerm = lowerReasons.includes("contrast") || lowerReasons.includes("wcag") || lowerReasons.includes("contrast ratio");
    const hasAlignmentTerm = lowerReasons.includes("align") || lowerReasons.includes("spacing") || lowerReasons.includes("hierarchy");

    if (selectedMockup === "A" && hasContrastTerm && hasAlignmentTerm) {
      setSuccess(true);
      setFeedback("Excellent Analysis! You correctly pointed out Design A's high contrast index and clean padding grids while noting Design B's violations. a11y Score +10%.");
      setA11yScore(Math.min(a11yScore + 10, 100));
    } else if (selectedMockup === "B") {
      setSuccess(false);
      setFeedback("Triage Rejected. Design B contains severe readability and alignment defects. Review contrast ratios and retry.");
    } else {
      setSuccess(false);
      setFeedback("Justification Rejected. Your design reasons are too brief or omit core keywords (e.g. contrast ratios, alignment, spacing). Please expand your analysis.");
    }
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    if (!primaryHex.trim() || !bgHex.trim() || !typoPair || !hardExplanation.trim()) return;

    setSubmitted(true);
    
    // Validate hex format
    const hexRegex = /^#[0-9A-F]{6}$/i;
    const validHex = hexRegex.test(primaryHex) && hexRegex.test(bgHex);
    
    const lowerExplanation = hardExplanation.toLowerCase();
    const hasHciKeywords = lowerExplanation.includes("contrast") || lowerExplanation.includes("therapeutic") || lowerExplanation.includes("hierarchy") || lowerExplanation.includes("readability");

    if (validHex && typoPair && hasHciKeywords) {
      setSuccess(true);
      setFeedback("Design System Approved! Typography scale (Outfit/Inter) and hex color matching represent high readability grids conforming to modern therapeutic healthcare constraints. a11y Score +15%.");
      setA11yScore(Math.min(a11yScore + 15, 100));
    } else {
      setSuccess(false);
      setFeedback("Design System Rejected. Ensure hex formats are valid (e.g., #4648D4) and your explanation justifies accessibility contrast and hierarchy mapping.");
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setSelectedMockup(null);
    setMediumReasons("");
    setHardExplanation("");
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: DESIGN WORKSPACE */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Design Review & Theme Calibration</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Review design systems and theme assets to verify WCAG guidelines.</p>
        </div>

        {submitted ? (
          /* Submission Feedback Display */
          <div className="max-w-xl mx-auto w-full bg-surface border border-outline-variant/30 rounded-2xl p-8 shadow-xl text-center flex flex-col items-center gap-5 mt-4">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
              success ? "bg-primary-container text-white" : "bg-error-container/30 text-error"
            }`}>
              <span className="material-symbols-outlined text-[36px]">
                {success ? "check_circle" : "warning"}
              </span>
            </div>

            <h3 className="font-headline-md text-[20px] font-bold text-on-surface">
              {success ? "Design Specification Approved" : "Specification Rejected"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Revise Configuration" : "Try Again"}
              </button>
            </div>
          </div>
        ) : (
          /* Workspaces based on difficulty */
          <div className="flex-1 flex flex-col gap-6">

            {/* EASY/MEDIUM WORKSPACE: A/B Testing layout */}
            {difficulty !== "hard" && (
              <div className="flex flex-col gap-5">
                <h3 className="font-label-md text-sm font-bold text-on-surface">A/B Testing: Choose the better contrast & spacing design</h3>
                
                <div className="grid grid-cols-2 gap-6">
                  {/* Mockup A */}
                  <div
                    onClick={() => setSelectedMockup("A")}
                    className={`border rounded-2xl p-5 cursor-pointer transition-all duration-200 ${
                      selectedMockup === "A" 
                        ? "ring-2 ring-primary border-primary bg-primary/5" 
                        : "border-outline-variant/35 hover:border-outline-variant"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-4">
                      <span className="font-mono text-[10px] bg-green-100 text-green-800 rounded px-2 py-0.5 font-bold">MOCKUP A</span>
                      <span className="material-symbols-outlined text-green-600 text-sm">check_circle</span>
                    </div>

                    {/* Mock visual elements */}
                    <div className="bg-surface border border-outline-variant/10 rounded-xl p-4 flex flex-col gap-4 font-body-sm">
                      <div className="h-4 bg-primary/20 rounded w-1/3"></div>
                      <div className="h-8 bg-surface-container-high rounded w-full flex items-center px-3 font-semibold text-[13px] text-on-surface-variant">
                        High Contrast Heading (4.5:1)
                      </div>
                      <div className="h-16 bg-surface-container-low rounded w-full flex flex-col justify-center gap-1.5 p-3 text-[11px] text-outline">
                        <span>• Consistently aligned paddings</span>
                        <span>• Accessible contrast ratio</span>
                      </div>
                      <button type="button" className="py-2 bg-primary text-white text-xs font-semibold rounded-lg shadow-sm">
                        Submit Transaction
                      </button>
                    </div>
                  </div>

                  {/* Mockup B */}
                  <div
                    onClick={() => setSelectedMockup("B")}
                    className={`border rounded-2xl p-5 cursor-pointer transition-all duration-200 ${
                      selectedMockup === "B" 
                        ? "ring-2 ring-primary border-primary bg-primary/5" 
                        : "border-outline-variant/35 hover:border-outline-variant"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-4">
                      <span className="font-mono text-[10px] bg-red-100 text-red-800 rounded px-2 py-0.5 font-bold">MOCKUP B</span>
                      <span className="material-symbols-outlined text-red-600 text-sm">warning</span>
                    </div>

                    {/* Mock visual elements */}
                    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex flex-col gap-4 font-body-sm">
                      <div className="h-4 bg-yellow-300/35 rounded w-1/3"></div>
                      <div className="h-8 bg-yellow-200 rounded w-full flex items-center px-3 font-semibold text-[13px] text-yellow-700">
                        Low Contrast text on yellow background
                      </div>
                      <div className="h-16 bg-yellow-100/50 rounded w-full flex flex-col justify-center gap-1.5 p-3 text-[11px] text-yellow-600/80">
                        <span>• Cluttered overlapping grids</span>
                        <span>• Contrast ratio too low (1.8:1)</span>
                      </div>
                      <button type="button" className="py-2 bg-yellow-400 text-yellow-900 text-xs font-semibold rounded-lg shadow-sm">
                        Submit Transaction
                      </button>
                    </div>
                  </div>
                </div>

                {/* Medium specifics: Input reasons */}
                {difficulty === "medium" && (
                  <div className="flex flex-col gap-2 bg-surface-container p-4 rounded-xl border border-outline-variant/20 mt-2">
                    <label className="font-label-sm text-xs text-outline font-semibold">Justify Design choice (mention contrast ratio and alignment):</label>
                    <textarea
                      value={mediumReasons}
                      onChange={(e) => setMediumReasons(e.target.value)}
                      placeholder="Explain why A conforms to WCAG standards compared to B..."
                      className="w-full h-24 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[12px] resize-none outline-none transition-all"
                    />
                  </div>
                )}

                {/* Submit button for Easy/Medium */}
                <button
                  onClick={difficulty === "easy" ? handleEasySubmit : handleMediumSubmit}
                  disabled={!selectedMockup || (difficulty === "medium" && !mediumReasons.trim())}
                  className="self-end mt-4 py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all"
                >
                  Verify Design Choice
                </button>
              </div>
            )}

            {/* HARD WORKSPACE: Design from scratch brief */}
            {difficulty === "hard" && (
              <form onSubmit={handleHardSubmit} className="flex flex-col gap-5">
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm font-body-sm text-[13px] text-on-surface-variant leading-relaxed">
                  <h3 className="font-label-md text-sm font-bold text-on-surface mb-2">Design Brief: Startup &apos;AetherHealth&apos;</h3>
                  <p className="mb-3">Define a clean therapeutic healthcare interface theme. WCAG AA requirements mandate a minimum contrast ratio of 4.5:1 for body copy. Select a modern typography pair and valid primary/background colors below.</p>
                  
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    {/* Primary Color */}
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Primary Hex (e.g. #0F172A)</label>
                      <input
                        type="text"
                        value={primaryHex}
                        onChange={(e) => setPrimaryHex(e.target.value)}
                        placeholder="#000000"
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-mono text-xs outline-none"
                      />
                    </div>

                    {/* Background Color */}
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Background Hex (e.g. #FAF8FF)</label>
                      <input
                        type="text"
                        value={bgHex}
                        onChange={(e) => setBgHex(e.target.value)}
                        placeholder="#ffffff"
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-mono text-xs outline-none"
                      />
                    </div>

                    {/* Typography pairing */}
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Typography Pair</label>
                      <select
                        value={typoPair}
                        onChange={(e) => setTypoPair(e.target.value)}
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 text-xs outline-none"
                      >
                        <option value="">Select pairing...</option>
                        <option value="Outfit_Inter">Outfit (Headers) + Inter (Body)</option>
                        <option value="Montserrat_Roboto">Montserrat (Headers) + Roboto (Body)</option>
                      </select>
                    </div>
                  </div>

                  {/* Justification input */}
                  <div className="flex flex-col gap-1">
                    <label className="font-label-sm text-[11px] text-outline font-semibold">Justify contrast mapping and hierarchy details against client guidelines:</label>
                    <textarea
                      value={hardExplanation}
                      onChange={(e) => setHardExplanation(e.target.value)}
                      placeholder="Write how the hex choice achieves therapeutic color contrast and Outfit font headers achieve clean visual hierarchy..."
                      className="w-full h-24 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 text-xs resize-none outline-none transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!primaryHex.trim() || !bgHex.trim() || !typoPair || !hardExplanation.trim()}
                  className="self-end py-2.5 px-6 bg-error text-white font-label-md text-xs rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all font-semibold"
                >
                  Verify Design Specs
                </button>
              </form>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: DESIGN CRITERIA */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">gavel</span>
          HCI Guidelines
        </h3>

        <div className="flex flex-col gap-4 font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">WCAG AA Contrast Index</h4>
            <p>Standard text require a minimum contrast ratio of 4.5:1. Large headings (above 18pt bold) require at least 3.0:1.</p>
          </div>

          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Visual Grid Alignment</h4>
            <p>Ensure components snap to consistent gutters (spacing variables of 8px, 16px, or 24px) to retain structural alignment hierarchy.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
