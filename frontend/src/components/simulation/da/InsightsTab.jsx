"use client";

import React, { useState } from "react";

export default function InsightsTab({ difficulty, insightsFound, setInsightsFound }) {
  // Input values
  const [easySelected, setEasySelected] = useState("");
  const [mediumHypothesis, setMediumHypothesis] = useState("");
  const [mediumText, setMediumText] = useState("");
  
  const [hardHypothesis, setHardHypothesis] = useState("");
  const [hardText, setHardText] = useState("");
  const [richTextFormat, setRichTextFormat] = useState({ bold: false, italic: false, underline: false });

  // Evaluation states
  const [submitted, setSubmitted] = useState(false);
  const [evaluationFeedback, setEvaluationFeedback] = useState(null);
  const [evaluationSuccess, setEvaluationSuccess] = useState(false);

  // Easy MCQ Options
  const easyOptions = [
    {
      id: "easy_correct",
      label: "Option A: Institutional volume surges correlate with severe RSI declines on 2026-06-18 and 2026-06-21. This divergence indicates institutional players are offloading block sizes to retail buyers before a trend reversal.",
      isCorrect: true,
    },
    {
      id: "easy_trap",
      label: "Option B (Trap): Crypto trading volumes always double on Tuesdays because of institutional trade settlement limits that reset at Monday midnight.",
      isCorrect: false,
      isTrap: true,
    },
    {
      id: "easy_wrong",
      label: "Option C: Institutional volumes are high because retail buyers are only trading during off-market hours, creating a scheduling anomaly.",
      isCorrect: false,
    }
  ];

  // Medium Hypothesis Choices
  const mediumHypotheses = [
    {
      id: "med_correct",
      title: "Divergence between RSI levels and institutional volume.",
      desc: "Investigate whether volume spikes on high RSI dates represent selling distribution.",
      isCorrect: true,
    },
    {
      id: "med_trap",
      title: "RSI Momentum Indicators.",
      desc: "Investigate if RSI above 70 guarantees a volume increase next week due to market momentum.",
      isCorrect: false,
      isTrap: true,
    }
  ];

  // Hard Hypothesis Choices
  const hardHypotheses = [
    {
      id: "hard_correct",
      title: "Divergence in RSI vs. Institutional block volume.",
      desc: "Analyze if institutional block sells are occurring during retail buying peaks.",
      isCorrect: true,
    },
    {
      id: "hard_trap",
      title: "Webhook logs timing offset.",
      desc: "Analyze if the negative correlation between retail volume and RSI is an artifact of API webhook log latency.",
      isCorrect: false,
      isTrap: true,
    }
  ];

  const handleEasySubmit = (e) => {
    e.preventDefault();
    if (!easySelected) return;

    setSubmitted(true);
    if (easySelected === "easy_correct") {
      setEvaluationSuccess(true);
      setEvaluationFeedback("Correct! You identified the institutional divergence. The client is notified, and Data Integrity metrics are verified.");
      setInsightsFound(1);
    } else if (easySelected === "easy_trap") {
      setEvaluationSuccess(false);
      setEvaluationFeedback("Incorrect (Trap Triggered): Institutional trade settlement limits do not cause price resets. You fell for the planted false lead!");
      setInsightsFound(0);
    } else {
      setEvaluationSuccess(false);
      setEvaluationFeedback("Incorrect: This hypothesis is unsupported by the trading volume logs.");
      setInsightsFound(0);
    }
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    if (!mediumHypothesis || !mediumText.trim()) return;

    setSubmitted(true);
    if (mediumHypothesis === "med_correct") {
      // Check if text is descriptive enough
      if (mediumText.length < 30) {
        setEvaluationSuccess(false);
        setEvaluationFeedback("Rejected: Your written response is too short. Please provide a detailed analysis of the divergence (at least 30 characters).");
      } else {
        setEvaluationSuccess(true);
        setEvaluationFeedback("Acknowledge & Accepted. The VP reviewed your notes and agrees that institutional players are offloading positions. Good work!");
        setInsightsFound(1);
      }
    } else if (mediumHypothesis === "med_trap") {
      setEvaluationSuccess(false);
      setEvaluationFeedback("Rejected (Trap Triggered): Overbought RSI (>70) typically indicates exhaustion and a reversal, NOT a momentum guarantee. You fell for the planted false lead!");
      setInsightsFound(0);
    }
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    if (!hardHypothesis || !hardText.trim()) return;

    setSubmitted(true);
    if (hardHypothesis === "hard_correct") {
      if (hardText.length < 100) {
        setEvaluationSuccess(false);
        setEvaluationFeedback("Rejected: Insufficient analytical depth. Your written recommendation requires advanced statistical correlation analysis (at least 100 characters).");
      } else {
        setEvaluationSuccess(true);
        setEvaluationFeedback("Recommendation Approved by VP. Integrity score high. The client will be informed of institutional distribution. Excellent statistical support.");
        setInsightsFound(2); // In hard mode, they find 2/3 insights if correct!
      }
    } else if (hardHypothesis === "hard_trap") {
      setEvaluationSuccess(false);
      setEvaluationFeedback("Recommendation REJECTED (Trap Triggered). The VP pushback: Webhook latency is standard (under 15ms) and does not account for day-level divergence. You fell for a false correlation trap in the API log timing.");
      setInsightsFound(0);
    }
  };

  const resetForm = () => {
    setSubmitted(false);
    setEvaluationFeedback(null);
    setEvaluationSuccess(false);
    setEasySelected("");
    setMediumHypothesis("");
    setMediumText("");
    setHardHypothesis("");
    setHardText("");
    setInsightsFound(0);
  };

  const toggleStyle = (format) => {
    setRichTextFormat(prev => ({ ...prev, [format]: !prev[format] }));
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: INSIGHTS WORKSPACE */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header description */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Actionable Recommendation Console</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Submit your findings on institutional trends to trigger scoring.</p>
        </div>

        {submitted && evaluationFeedback ? (
          /* Evaluation display */
          <div className="max-w-xl mx-auto w-full bg-surface border border-outline-variant/30 rounded-2xl p-8 shadow-xl text-center flex flex-col items-center gap-5 mt-4">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
              evaluationSuccess ? "bg-primary-container text-white" : "bg-error-container/30 text-error"
            }`}>
              <span className="material-symbols-outlined text-[36px]">
                {evaluationSuccess ? "check_circle" : "warning"}
              </span>
            </div>

            <h3 className="font-headline-md text-[22px] font-bold text-on-surface">
              {evaluationSuccess ? "Insight Approved" : "Submission Rejected"}
            </h3>

            <p className="font-body-sm text-[14px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {evaluationFeedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={resetForm}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                Try Again / Reset
              </button>
            </div>
          </div>
        ) : (
          /* Submission Form workspace */
          <div className="flex-1 flex flex-col gap-6">
            
            {/* EASY DIFFICULTY: MCQ radio buttons */}
            {difficulty === "easy" && (
              <form onSubmit={handleEasySubmit} className="flex flex-col gap-4">
                <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-3">Select the correct core finding from the logs:</h3>
                  
                  <div className="flex flex-col gap-3">
                    {easyOptions.map((opt) => (
                      <label
                        key={opt.id}
                        className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                          easySelected === opt.id
                            ? "bg-primary/5 border-primary shadow-sm"
                            : "bg-surface border-outline-variant/20 hover:border-outline-variant hover:bg-surface-container-low"
                        }`}
                      >
                        <input
                          type="radio"
                          name="easy_mcq"
                          value={opt.id}
                          checked={easySelected === opt.id}
                          onChange={() => setEasySelected(opt.id)}
                          className="mt-1 accent-primary focus:ring-primary"
                        />
                        <span className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed">
                          {opt.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!easySelected}
                  className="py-3 px-6 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline/35 disabled:cursor-not-allowed self-end mt-4 transition-colors"
                >
                  Submit Recommendation
                </button>
              </form>
            )}

            {/* MEDIUM DIFFICULTY: Textarea + Hypothesis deck */}
            {difficulty === "medium" && (
              <form onSubmit={handleMediumSubmit} className="flex flex-col gap-4">
                <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl mb-2">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-3">Select Hypothesis Area:</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {mediumHypotheses.map((h) => (
                      <div
                        key={h.id}
                        onClick={() => setMediumHypothesis(h.id)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col gap-1.5 ${
                          mediumHypothesis === h.id
                            ? "bg-primary/5 border-primary shadow-sm"
                            : "bg-surface border-outline-variant/20 hover:border-outline-variant"
                        }`}
                      >
                        <h4 className="font-label-sm text-xs font-bold text-primary flex items-center gap-1">
                          {h.isTrap && <span className="material-symbols-outlined text-[14px] text-tertiary-container">info</span>}
                          {h.title}
                        </h4>
                        <p className="font-body-sm text-[11px] text-on-surface-variant leading-normal">{h.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-label-sm text-xs text-outline font-semibold">Write your finding analysis (minimum 30 characters):</label>
                  <textarea
                    value={mediumText}
                    onChange={(e) => setMediumText(e.target.value)}
                    placeholder="Provide details on institutional volume spikes and how they correlate with RSI levels..."
                    className="w-full h-36 bg-surface border border-outline-variant rounded-xl p-3 font-body-sm text-[13px] focus:outline-none focus:border-primary resize-none scrollbar-thin shadow-inner"
                  />
                  <div className="text-right text-[11px] text-outline italic">
                    {mediumText.length} characters
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!mediumHypothesis || !mediumText.trim()}
                  className="py-3 px-6 bg-tertiary-container text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-tertiary disabled:bg-outline/35 disabled:cursor-not-allowed self-end mt-2 transition-colors"
                >
                  Submit Review
                </button>
              </form>
            )}

            {/* HARD DIFFICULTY: Rich-text area + Advanced Hypothesis trap */}
            {difficulty === "hard" && (
              <form onSubmit={handleHardSubmit} className="flex flex-col gap-4">
                <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-3">Select Statistical Hypothesis Model:</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {hardHypotheses.map((h) => (
                      <div
                        key={h.id}
                        onClick={() => setHardHypothesis(h.id)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col gap-1.5 ${
                          hardHypothesis === h.id
                            ? "bg-primary/5 border-primary shadow-sm"
                            : "bg-surface border-outline-variant/20 hover:border-outline-variant"
                        }`}
                      >
                        <h4 className="font-label-sm text-xs font-bold text-primary flex items-center gap-1">
                          {h.isTrap && <span className="material-symbols-outlined text-[14px] text-error">info</span>}
                          {h.title}
                        </h4>
                        <p className="font-body-sm text-[11px] text-on-surface-variant leading-normal">{h.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col border border-outline-variant rounded-xl overflow-hidden shadow-inner bg-surface">
                  {/* Rich Text controls */}
                  <div className="bg-surface-container border-b border-outline-variant/40 p-2 flex gap-1 items-center">
                    <button
                      type="button"
                      onClick={() => toggleStyle("bold")}
                      className={`w-8 h-8 rounded flex items-center justify-center hover:bg-surface-container-high transition-colors ${richTextFormat.bold ? "bg-primary-container text-white" : "text-outline"}`}
                    >
                      <span className="material-symbols-outlined text-[18px]">format_bold</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleStyle("italic")}
                      className={`w-8 h-8 rounded flex items-center justify-center hover:bg-surface-container-high transition-colors ${richTextFormat.italic ? "bg-primary-container text-white" : "text-outline"}`}
                    >
                      <span className="material-symbols-outlined text-[18px]">format_italic</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleStyle("underline")}
                      className={`w-8 h-8 rounded flex items-center justify-center hover:bg-surface-container-high transition-colors ${richTextFormat.underline ? "bg-primary-container text-white" : "text-outline"}`}
                    >
                      <span className="material-symbols-outlined text-[18px]">format_underlined</span>
                    </button>
                    <span className="h-6 w-px bg-outline-variant/40 mx-2"></span>
                    <span className="font-body-sm text-[10px] text-outline-variant italic">Full Written Recommendation Workspace</span>
                  </div>

                  <textarea
                    value={hardText}
                    onChange={(e) => setHardText(e.target.value)}
                    placeholder="Provide a detailed Written Recommendation. Detail the correlation coefficient, outline the divergence anomalies, and explain why institutional players are dumping (at least 100 characters)..."
                    className={`w-full h-44 p-4 border-none outline-none focus:ring-0 bg-transparent resize-none font-body-sm text-[13px] scrollbar-thin ${
                      richTextFormat.bold ? "font-extrabold" : ""
                    } ${richTextFormat.italic ? "italic" : ""} ${richTextFormat.underline ? "underline" : ""}`}
                  />
                  <div className="text-right text-[11px] text-outline italic px-4 py-1.5 bg-surface-container-low border-t border-outline-variant/10">
                    {hardText.length} characters
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!hardHypothesis || !hardText.trim()}
                  className="py-3 px-6 bg-error text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container disabled:bg-outline/35 disabled:cursor-not-allowed self-end mt-2 transition-all"
                >
                  Submit Executive Recommendation
                </button>
              </form>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: SCORING CRITERIA */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">assessment</span>
          Scoring Criteria
        </h3>

        <div className="flex flex-col gap-4">
          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl flex flex-col gap-2">
            <h4 className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider">Hypothesis Support</h4>
            <p className="font-body-sm text-[11px] text-on-surface-variant leading-relaxed">
              Your insight must be fully backed by data evidence compiled in the Visualizations tab. Selecting the correct hypothesis scores highest.
            </p>
          </div>

          <div className="bg-error-container/20 border border-error/20 p-4 rounded-xl flex flex-col gap-2">
            <h4 className="font-label-sm text-xs font-bold text-error uppercase tracking-wider">False Leads (Traps)</h4>
            <p className="font-body-sm text-[11px] text-on-error-container leading-relaxed">
              Caution! The database has been seeded with plausible false leads. Double-check your charts to confirm that price spikes correlate with volume distribution before submitting.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
