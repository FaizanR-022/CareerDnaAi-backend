"use client";

import React, { useState, useEffect } from "react";

export default function CodeSandboxTab({ difficulty, responsiveScore, setResponsiveScore }) {
  // Easy selections
  const [easyDirection, setEasyDirection] = useState("");
  const [easyGrid, setEasyGrid] = useState("");
  const [viewportMode, setViewportMode] = useState("desktop"); // desktop, tablet, mobile

  // Medium selections
  const [medPadding, setMedPadding] = useState("");
  const [medWidth, setMedWidth] = useState(800); // slider width: 320 to 1200

  // Hard selections
  const [hardCssText, setHardCssText] = useState("/* Write media query to center .grid-layout on screens < 768px... */");
  const [compileLogs, setCompileLogs] = useState([]);
  const [compileSuccess, setCompileSuccess] = useState(false);

  // Verification states
  const [submitted, setSubmitted] = useState(false);
  const [success, setSuccess] = useState(false);
  const [feedback, setFeedback] = useState("");

  const handleEasySubmit = (e) => {
    e.preventDefault();
    if (!easyDirection || !easyGrid) return;

    setSubmitted(true);
    if (easyDirection === "row" && easyGrid === "grid-cols-3") {
      setSuccess(true);
      setFeedback("HTML/CSS Sandbox compiles! flex-direction: row and grid-cols-3 align elements cleanly on desktop. Responsive Score +1 Breakpoint.");
      setResponsiveScore("3/3 Breakpoints");
    } else {
      setSuccess(false);
      setFeedback("Compilation failed. Mismatched flex direction or grid alignment. Review layout stacking.");
    }
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    if (!medPadding.trim()) return;

    setSubmitted(true);
    const cleanPadding = medPadding.trim().toLowerCase();
    
    if (cleanPadding === "md:p-6" || cleanPadding === "p-6" || cleanPadding === "p-4 md:p-8") {
      setSuccess(true);
      setFeedback("Fluid width constraints compiled! Responsive padding offsets flex boundaries on manual resize checks. Responsive Score +1 Breakpoint.");
      setResponsiveScore("3/3 Breakpoints");
    } else {
      setSuccess(false);
      setFeedback("Verification failed. Padding value didn't adjust fluid limits. Try: md:p-6 or similar responsive tailwind utility.");
    }
  };

  const handleHardCompile = (e) => {
    e.preventDefault();
    setCompileSuccess(false);
    const css = hardCssText.trim().toLowerCase();
    const logs = ["Parsing raw sandbox stylesheet...", "Analysing AST rules..."];

    // Validate media query syntax
    const hasMedia = css.includes("@media") && css.includes("768px");
    const hasDirection = css.includes("flex-direction") && css.includes("column");
    const hasPadding = css.includes("padding");

    setTimeout(() => {
      if (hasMedia && hasDirection && hasPadding) {
        logs.push("SUCCESS: Media query @media (max-width: 768px) compiled successfully.");
        logs.push("Staging preview refreshed.");
        setCompileLogs(logs);
        setCompileSuccess(true);
        setSuccess(true);
        setFeedback("Hard Sandbox compilation complete! The responsive media query successfully stack elements and applies margins below 768px. Score +1 Breakpoint.");
        setResponsiveScore("3/3 Breakpoints");
      } else {
        logs.push("ERROR: Syntax compilation exception. Missing media boundary query or flex-direction properties.");
        setCompileLogs(logs);
        setSuccess(false);
        setFeedback("Code compiling error. Check media query bounds (e.g. max-width: 768px) and style blocks (.grid-layout).");
      }
      setSubmitted(true);
    }, 1000);
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setEasyDirection("");
    setEasyGrid("");
    setMedPadding("");
    setHardCssText("/* Write media query to center .grid-layout on screens < 768px... */");
    setCompileSuccess(false);
    setCompileLogs([]);
  };

  // Viewport width styling mapping for the mock browser frame
  const getBrowserWidthStyle = () => {
    if (difficulty === "easy") {
      if (viewportMode === "mobile") return "w-[340px]";
      if (viewportMode === "tablet") return "w-[540px]";
      return "w-full max-w-[620px]";
    } else if (difficulty === "medium") {
      return `w-[${medWidth}px]`;
    } else {
      // Hard
      return compileSuccess ? "w-[340px]" : "w-full max-w-[620px]"; // switch to mobile frame if compile success
    }
  };

  const getResponsiveClass = () => {
    if (difficulty === "easy") {
      if (viewportMode === "mobile") return "flex-col grid-cols-1";
      if (viewportMode === "tablet") return "flex-row grid-cols-2";
      return `flex-${easyDirection || "col"} ${easyGrid || "grid-cols-1"}`;
    } else if (difficulty === "medium") {
      if (medWidth < 480) return "flex-col grid-cols-1 p-2";
      if (medWidth < 768) return "flex-row grid-cols-2 p-4";
      return "flex-row grid-cols-3 p-6";
    } else {
      // Hard
      return compileSuccess ? "flex-col grid-cols-1 p-4" : "flex-row grid-cols-3 p-6";
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: CODE BOX EDITOR */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header */}
        <div className="mb-5">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">CSS Staging Sandbox</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Adjust CSS directives and check how the viewport layout changes in the preview panel.</p>
        </div>

        {submitted && feedback ? (
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
              {success ? "Compilation Complete" : "Staging compilation error"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Reset Editor" : "Revise Code"}
              </button>
            </div>
          </div>
        ) : (
          /* Interactive Code block selectors */
          <div className="flex flex-col gap-5">
            
            {/* EASY VIEW: Code snippet with inline dropdown selections */}
            {difficulty === "easy" && (
              <div className="flex flex-col gap-4">
                <div className="bg-inverse-surface rounded-2xl p-5 text-white font-mono text-[11px] leading-relaxed shadow-lg flex flex-col gap-2">
                  <span className="text-surface-variant font-bold">{"// EDITABLE MOCK CSS LANDING PAGE STYLESHEET"}</span>
                  <div>
                    <span className="text-blue-300">.container</span> {"{"}
                    <div className="pl-6 flex items-center gap-2">
                      <span className="text-purple-300">display:</span> <span className="text-green-300">flex;</span>
                    </div>
                    <div className="pl-6 flex items-center gap-2">
                      <span className="text-purple-300">flex-direction:</span>
                      <select
                        value={easyDirection}
                        onChange={(e) => setEasyDirection(e.target.value)}
                        className="bg-black/60 border border-white/20 rounded px-2 py-0.5 font-mono text-[10px] text-green-300 focus:outline-none"
                      >
                        <option value="">Choose...</option>
                        <option value="row">row (Side by side)</option>
                        <option value="col">col (Vertical stack)</option>
                      </select>
                      <span className="text-white">;</span>
                    </div>
                    <span className="text-white">{"}"}</span>
                  </div>

                  <div>
                    <span className="text-blue-300">.grid-layout</span> {"{"}
                    <div className="pl-6 flex items-center gap-2">
                      <span className="text-purple-300">grid-template-columns:</span>
                      <select
                        value={easyGrid}
                        onChange={(e) => setEasyGrid(e.target.value)}
                        className="bg-black/60 border border-white/20 rounded px-2 py-0.5 font-mono text-[10px] text-green-300 focus:outline-none"
                      >
                        <option value="">Choose...</option>
                        <option value="grid-cols-3">repeat(3, 1fr) [3 cols]</option>
                        <option value="grid-cols-1">repeat(1, 1fr) [1 col]</option>
                      </select>
                      <span className="text-white">;</span>
                    </div>
                    <span className="text-white">{"}"}</span>
                  </div>
                </div>

                <button
                  onClick={handleEasySubmit}
                  disabled={!easyDirection || !easyGrid}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all"
                >
                  Compile Staging Code
                </button>
              </div>
            )}

            {/* MEDIUM VIEW: Manual resize slider & property value input */}
            {difficulty === "medium" && (
              <div className="flex flex-col gap-4">
                {/* Fluid slider */}
                <div className="bg-surface border border-outline-variant/20 p-4 rounded-xl shadow-sm flex flex-col gap-2">
                  <div className="flex justify-between items-center text-xs font-semibold text-outline">
                    <span>Resize Viewport Fluidity:</span>
                    <span className="font-mono text-primary font-bold">{medWidth}px</span>
                  </div>
                  <input
                    type="range"
                    min="320"
                    max="1200"
                    value={medWidth}
                    onChange={(e) => setMedWidth(parseInt(e.target.value))}
                    className="w-full accent-primary cursor-ew-resize"
                  />
                </div>

                <div className="bg-inverse-surface rounded-2xl p-5 text-white font-mono text-[11px] leading-relaxed shadow-lg flex flex-col gap-2">
                  <span className="text-surface-variant font-bold">{"// EDITABLE MOCK UTILITY CLASSES"}</span>
                  <div>
                    <span className="text-blue-300">.responsive-card-layout</span> {"{"}
                    <div className="pl-6 flex items-center gap-1.5 flex-wrap">
                      <span className="text-purple-300">margin:</span> <span className="text-green-300">16px;</span>
                    </div>
                    <div className="pl-6 flex items-center gap-1.5 flex-wrap">
                      <span className="text-purple-300">padding:</span>
                      <input
                        type="text"
                        value={medPadding}
                        onChange={(e) => setMedPadding(e.target.value)}
                        placeholder="e.g. md:p-6"
                        className="bg-black/60 border border-white/20 rounded px-2 py-0.5 font-mono text-[10px] text-green-300 focus:outline-none w-24"
                      />
                      <span className="text-white">;</span>
                      <span className="text-surface-variant text-[9px]">{"// Enter utility padding scale"}</span>
                    </div>
                    <span className="text-white">{"}"}</span>
                  </div>
                </div>

                <button
                  onClick={handleMediumSubmit}
                  disabled={!medPadding.trim()}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all"
                >
                  Compile Fluid sandbox
                </button>
              </div>
            )}

            {/* HARD VIEW: Raw code editor & compile output logs */}
            {difficulty === "hard" && (
              <div className="flex flex-col gap-4">
                <div className="bg-inverse-surface rounded-2xl p-5 text-white font-mono text-[11px] leading-relaxed shadow-lg flex flex-col gap-3">
                  <div className="flex justify-between items-center text-surface-variant font-bold border-b border-white/5 pb-2">
                    <span>{"// MAIN STYLESHEET EDITOR"}</span>
                    <span className="text-[9px] uppercase tracking-wider text-error">Staging environment active</span>
                  </div>

                  <textarea
                    value={hardCssText}
                    onChange={(e) => setHardCssText(e.target.value)}
                    className="w-full h-32 bg-transparent text-green-400 border-none outline-none resize-none font-mono focus:ring-0 scrollbar-thin text-xs"
                  />
                </div>

                <div className="flex justify-between items-center">
                  <span className="font-body-sm text-[11px] text-outline italic">Compile raw directives to trigger CSS rules check.</span>
                  <button
                    onClick={handleHardCompile}
                    className="py-2.5 px-6 bg-error text-white font-label-md text-xs rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container transition-all font-semibold"
                  >
                    Compile Sandbox Code
                  </button>
                </div>

                {/* Console trace logs */}
                {compileLogs.length > 0 && (
                  <div className="h-28 bg-black border border-white/10 rounded-xl p-3 font-mono text-[10px] text-white/70 overflow-y-auto scrollbar-thin flex flex-col gap-1">
                    <div className="text-surface-variant">{"// Staging CLI traces:"}</div>
                    {compileLogs.map((log, idx) => (
                      <div key={idx} className={log.startsWith("ERROR") ? "text-error" : log.startsWith("SUCCESS") ? "text-green-400" : "text-white/80"}>
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: LIVE VIEWPORT PREVIEW */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-headline-md text-[16px] font-bold text-on-surface flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[20px] text-primary">visibility</span>
            HTML Preview
          </h3>

          {/* Easy view toggle */}
          {difficulty === "easy" && (
            <div className="flex bg-surface-container rounded p-0.5 border border-outline-variant/10 text-[9px] font-bold select-none">
              <button onClick={() => setViewportMode("desktop")} className={`px-1.5 py-0.5 rounded ${viewportMode === "desktop" ? "bg-primary text-white" : "text-outline"}`}>D</button>
              <button onClick={() => setViewportMode("tablet")} className={`px-1.5 py-0.5 rounded ${viewportMode === "tablet" ? "bg-primary text-white" : "text-outline"}`}>T</button>
              <button onClick={() => setViewportMode("mobile")} className={`px-1.5 py-0.5 rounded ${viewportMode === "mobile" ? "bg-primary text-white" : "text-outline"}`}>M</button>
            </div>
          )}
        </div>

        {/* Viewport content */}
        <div className="flex-1 bg-surface-container-low border border-outline-variant/30 rounded-2xl p-3 flex justify-center items-start overflow-y-auto relative min-h-[300px]">
          <div className={`${getBrowserWidthStyle()} bg-surface border border-outline-variant/10 shadow-sm rounded-lg overflow-hidden flex flex-col gap-2 transition-all duration-300 font-body-sm text-[10px]`}>
            {/* Header */}
            <div className="bg-surface-container py-1.5 px-3 flex justify-between items-center border-b border-outline-variant/20 select-none">
              <span className="font-bold">AetherHealth</span>
              <span className="material-symbols-outlined text-[14px]">menu</span>
            </div>

            {/* Layout Cards */}
            <div className={`grid gap-2 p-3 ${getResponsiveClass()}`}>
              {/* Box 1 */}
              <div className="bg-primary/5 border border-primary/20 p-2.5 rounded flex flex-col gap-1">
                <span className="font-bold">1. Patient Queue</span>
                <p className="text-outline text-[9px]">Check waiting list bounds.</p>
              </div>

              {/* Box 2 */}
              <div className="bg-primary/5 border border-primary/20 p-2.5 rounded flex flex-col gap-1">
                <span className="font-bold">2. Diagnosis Metrics</span>
                <p className="text-outline text-[9px]">Scan biometric variables.</p>
              </div>

              {/* Box 3 */}
              <div className="bg-primary/5 border border-primary/20 p-2.5 rounded flex flex-col gap-1">
                <span className="font-bold">3. Prescriptions logs</span>
                <p className="text-outline text-[9px]">Verify pharmacist dispatch tags.</p>
              </div>
            </div>

            {/* Visual warning if layout is not clean */}
            {difficulty === "hard" && !compileSuccess && (
              <div className="bg-error-container/20 border-t border-error/20 p-2 text-center text-error font-semibold text-[9px] flex items-center justify-center gap-1">
                <span className="material-symbols-outlined text-[12px]">error</span>
                Viewport Breakpoint Broken (&lt;768px)
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
