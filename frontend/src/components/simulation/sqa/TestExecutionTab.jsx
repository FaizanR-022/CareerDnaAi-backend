"use client";

import React, { useState } from "react";

export default function TestExecutionTab({ difficulty, bugsFound, setBugsFound, testCoverage, setTestCoverage }) {
  const [viewport, setViewport] = useState("desktop");
  const [networkThrottled, setNetworkThrottled] = useState(false);

  // Mock Form inputs
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");

  // Validation States
  const [formErrors, setFormErrors] = useState({});
  const [consoleLogs, setConsoleLogs] = useState([]);
  const [showConsole, setShowConsole] = useState(false);
  const [transactionStatus, setTransactionStatus] = useState("idle"); // idle | success | failed

  // Performance metrics check (Medium)
  const [perfCheck1, setPerfCheck1] = useState(false);
  const [perfCheck2, setPerfCheck2] = useState(false);
  const [perfCheckSubmitted, setPerfCheckSubmitted] = useState(false);

  // Performance metrics inputs (Hard)
  const [fcpInput, setFcpInput] = useState("");
  const [ttiInput, setTtiInput] = useState("");
  const [perfHardSubmitted, setPerfHardSubmitted] = useState(false);
  const [perfFeedback, setPerfFeedback] = useState("");

  // Submit mock form
  const handleFormSubmit = (e) => {
    e.preventDefault();
    setTransactionStatus("submitting");

    setTimeout(() => {
      let errors = {};
      let logs = [...consoleLogs];
      const timeStr = new Date().toLocaleTimeString();

      // Check validations
      if (!email.includes("@")) {
        errors.email = "Invalid email format. Missing '@' symbol.";
      }
      if (password.length < 8) {
        errors.password = "Password must be at least 8 characters.";
      } else if (!/[!@#$%^&*(),.?":{}|<>]/g.test(password)) {
        errors.password = "Password must contain at least 1 special character.";
      }
      if (cardNumber.replace(/\s+/g, "").length !== 16) {
        errors.cardNumber = "Card number must be exactly 16 digits.";
      }

      const hasErrors = Object.keys(errors).length > 0;

      if (difficulty === "easy") {
        setFormErrors(errors);
        if (hasErrors) {
          setTransactionStatus("failed");
          setBugsFound(Math.min(bugsFound + 1, 3));
        } else {
          setTransactionStatus("success");
          setTestCoverage(Math.min(testCoverage + 10, 100));
        }
      } else if (difficulty === "medium") {
        // Errors are hidden in UI, but printed in mock console
        setFormErrors({});
        if (hasErrors) {
          setTransactionStatus("failed");
          Object.entries(errors).forEach(([field, msg]) => {
            logs.push(`[${timeStr}] ERROR: auth_validation.js - Field '${field}' failed checks: ${msg}`);
          });
          setBugsFound(Math.min(bugsFound + 1, 3));
          setShowConsole(true);
        } else {
          setTransactionStatus("success");
          logs.push(`[${timeStr}] INFO: Authentication valid. Stripe checkout payload sent successfully.`);
          setTestCoverage(Math.min(testCoverage + 15, 100));
        }
        setConsoleLogs(logs);
      } else {
        // Hard mode: silent errors. Form fails but gives no visual or console clues.
        setFormErrors({});
        if (hasErrors) {
          setTransactionStatus("failed");
          logs.push(`[${timeStr}] INFO: Form submitted.`); // silent log
          setBugsFound(Math.min(bugsFound + 1, 3));
        } else {
          setTransactionStatus("success");
          logs.push(`[${timeStr}] INFO: Transaction processed.`);
          setTestCoverage(Math.min(testCoverage + 20, 100));
        }
        setConsoleLogs(logs);
      }
    }, 1200);
  };

  // Submit Medium performance check
  const handlePerfCheckSubmit = () => {
    if (perfCheck1 && perfCheck2) {
      setPerfCheckSubmitted(true);
      setTestCoverage(Math.min(testCoverage + 5, 100));
    } else {
      alert("Please review all guided checklist items first!");
    }
  };

  // Submit Hard performance metrics
  const handlePerfHardSubmit = (e) => {
    e.preventDefault();
    const fcp = parseInt(fcpInput.trim());
    const tti = parseInt(ttiInput.trim());

    if (isNaN(fcp) || isNaN(tti)) {
      alert("Please enter numeric millisecond metrics.");
      return;
    }

    setPerfHardSubmitted(true);
    // Correct values in our mock network logs (FCP: 1450ms, TTI: 2200ms)
    if (fcp >= 1400 && fcp <= 1500 && tti >= 2100 && tti <= 2300) {
      setPerfFeedback("Performance Metrics Checked: Verified! FCP (1450ms) and TTI (2200ms) conform to threshold expectations. Coverage +10%.");
      setTestCoverage(Math.min(testCoverage + 10, 100));
    } else {
      setPerfFeedback("Verification Failed: Metric mismatch. Review the network log waterfall panel on the right carefully.");
    }
  };

  // Viewport framing classes
  const getViewportClass = () => {
    switch (viewport) {
      case "mobile":
        return "w-[320px] h-[480px] border-[12px] border-inverse-surface rounded-[24px] shadow-2xl relative transition-all duration-300";
      case "tablet":
        return "w-[480px] h-[580px] border-[16px] border-inverse-surface rounded-[32px] shadow-2xl relative transition-all duration-300";
      case "desktop":
      default:
        return "w-full max-w-[620px] h-[440px] border border-outline-variant/30 rounded-xl shadow-md transition-all duration-300";
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: VIEWPORT SANDBOX */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Environment controls */}
        <div className="flex justify-between items-center mb-6 bg-surface border border-outline-variant/30 p-3 rounded-xl shadow-sm">
          <div className="flex items-center gap-4">
            <span className="font-label-sm text-[12px] text-outline font-semibold">Environment:</span>
            
            {/* Viewport switch tabs */}
            <div className="flex bg-surface-container rounded-lg p-0.5 border border-outline-variant/15">
              <button
                onClick={() => setViewport("desktop")}
                className={`px-3 py-1 text-xs font-semibold rounded flex items-center gap-1 ${viewport === "desktop" ? "bg-primary text-white" : "text-outline hover:text-on-surface"}`}
              >
                <span className="material-symbols-outlined text-[14px]">desktop_mac</span>
                Desktop
              </button>
              
              {difficulty !== "easy" && (
                <button
                  onClick={() => setViewport("mobile")}
                  className={`px-3 py-1 text-xs font-semibold rounded flex items-center gap-1 ${viewport === "mobile" ? "bg-primary text-white" : "text-outline hover:text-on-surface"}`}
                >
                  <span className="material-symbols-outlined text-[14px]">smartphone</span>
                  Mobile
                </button>
              )}

              {difficulty === "hard" && (
                <button
                  onClick={() => setViewport("tablet")}
                  className={`px-3 py-1 text-xs font-semibold rounded flex items-center gap-1 ${viewport === "tablet" ? "bg-primary text-white" : "text-outline hover:text-on-surface"}`}
                >
                  <span className="material-symbols-outlined text-[14px]">tablet_mac</span>
                  Tablet
                </button>
              )}
            </div>
          </div>

          {/* Network Throttling (Hard) */}
          {difficulty === "hard" && (
            <label className="flex items-center gap-2 cursor-pointer font-label-sm text-xs text-outline font-semibold select-none">
              <input
                type="checkbox"
                checked={networkThrottled}
                onChange={() => setNetworkThrottled(!networkThrottled)}
                className="rounded text-primary focus:ring-primary accent-primary"
              />
              <span>Throttling: Low-Speed 3G</span>
            </label>
          )}
        </div>

        {/* Viewport Frame Container */}
        <div className="flex-1 flex justify-center items-center p-4 bg-surface-container-low/50 rounded-2xl border border-dashed border-outline-variant/40 mb-6 overflow-y-auto relative min-h-[300px]">
          <div className={`${getViewportClass()} bg-surface flex flex-col overflow-hidden`}>
            
            {/* Mock browser header */}
            <div className="bg-surface-container border-b border-outline-variant/30 py-1.5 px-3 flex items-center gap-2 text-[10px] text-outline select-none">
              <span className="w-2.5 h-2.5 rounded-full bg-error-container/80"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/85"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-green-500/80"></span>
              <div className="flex-1 bg-surface border border-outline-variant/10 rounded px-2 text-[9px] truncate">
                https://staging.checkout.career-dna.ai/signup
              </div>
            </div>

            {/* Viewport Body Form */}
            <div className="flex-1 p-4 overflow-y-auto scrollbar-thin">
              <h4 className="font-headline-md text-sm font-bold text-on-surface mb-3">Secure Checkout Gate</h4>
              
              <form onSubmit={handleFormSubmit} className="flex flex-col gap-3">
                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Email Address</label>
                  <input
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter email address"
                    className={`bg-surface border rounded-lg p-2 font-body-sm text-[12px] outline-none transition-all ${
                      formErrors.email ? "border-error focus:ring-1 focus:ring-error" : "border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary"
                    }`}
                  />
                  {formErrors.email && (
                    <span className="text-error font-semibold text-[10px]">{formErrors.email}</span>
                  )}
                </div>

                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Password Credentials</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Create a strong password"
                    className={`bg-surface border rounded-lg p-2 font-body-sm text-[12px] outline-none transition-all ${
                      formErrors.password ? "border-error focus:ring-1 focus:ring-error" : "border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary"
                    }`}
                  />
                  {formErrors.password && (
                    <span className="text-error font-semibold text-[10px]">{formErrors.password}</span>
                  )}
                </div>

                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Stripe Card Number</label>
                  <input
                    type="text"
                    value={cardNumber}
                    onChange={(e) => setCardNumber(e.target.value)}
                    placeholder="XXXX XXXX XXXX XXXX"
                    className={`bg-surface border rounded-lg p-2 font-body-sm text-[12px] outline-none transition-all ${
                      formErrors.cardNumber ? "border-error focus:ring-1 focus:ring-error" : "border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary"
                    }`}
                  />
                  {formErrors.cardNumber && (
                    <span className="text-error font-semibold text-[10px]">{formErrors.cardNumber}</span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="flex flex-col gap-1">
                    <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Expiry Date</label>
                    <input
                      type="text"
                      value={expiry}
                      onChange={(e) => setExpiry(e.target.value)}
                      placeholder="MM/YY"
                      className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px] outline-none transition-all"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="font-label-sm text-[10px] text-outline uppercase font-bold">CVV</label>
                    <input
                      type="password"
                      value={cvv}
                      onChange={(e) => setCvv(e.target.value)}
                      placeholder="XXX"
                      className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px] outline-none transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={transactionStatus === "submitting"}
                  className="w-full mt-2 py-2 bg-primary text-white font-label-md text-xs rounded-lg shadow hover:bg-primary-container disabled:bg-outline-variant/40 disabled:cursor-not-allowed transition-all"
                >
                  {transactionStatus === "submitting" ? "Processing Auth Transaction..." : "Submit Test Transaction"}
                </button>
              </form>

              {/* Transaction result badge */}
              {transactionStatus !== "idle" && transactionStatus !== "submitting" && (
                <div className={`mt-3 p-3 rounded-lg border text-center flex items-center justify-center gap-2 font-semibold text-[11px] ${
                  transactionStatus === "success" 
                    ? "bg-green-50 border-green-200 text-green-700" 
                    : "bg-error-container/20 border-error/20 text-error"
                }`}>
                  <span className="material-symbols-outlined text-[16px]">
                    {transactionStatus === "success" ? "check_circle" : "error"}
                  </span>
                  {transactionStatus === "success" ? "Transaction Completed Successfully." : "Transaction Failed. Form contains errors."}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* MOCK DEV CONSOLE DRAWER (Medium/Hard) */}
        {difficulty !== "easy" && (
          <div className="border border-outline-variant/30 rounded-xl overflow-hidden shadow-sm bg-inverse-surface text-white">
            <div 
              onClick={() => setShowConsole(!showConsole)}
              className="bg-white/5 px-4 py-2 flex justify-between items-center cursor-pointer select-none border-b border-white/5"
            >
              <h4 className="font-label-md text-xs font-bold flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">terminal</span>
                Developer Log Console ({consoleLogs.length} events)
              </h4>
              <span className="material-symbols-outlined text-[18px]">
                {showConsole ? "expand_more" : "expand_less"}
              </span>
            </div>

            {showConsole && (
              <div className="p-3 h-32 overflow-y-auto font-mono text-[10px] text-white/90 bg-black/40 flex flex-col gap-1.5 scrollbar-thin">
                {consoleLogs.length === 0 ? (
                  <span className="text-surface-variant italic">{"// Console is clean. Submit a transaction to trigger diagnostic output logs."}</span>
                ) : (
                  consoleLogs.map((log, i) => (
                    <div key={i} className={log.includes("ERROR") ? "text-error" : log.includes("INFO") ? "text-green-400" : "text-white/60"}>
                      {log}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* RIGHT PANEL: PERFORMANCE TRACE */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">speed</span>
          Performance Monitor
        </h3>

        {/* Medium: Checklist */}
        {difficulty === "medium" && (
          <div className="flex flex-col gap-4">
            <div className="bg-surface-container border border-outline-variant/20 p-3.5 rounded-xl font-body-sm text-[11px] text-on-surface-variant">
              <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1.5 uppercase">Waterfall Metrics Check</h4>
              <p className="leading-relaxed mb-3">Confirm conforming load indicators based on Chrome DevTools performance traces:</p>
              
              <div className="flex flex-col gap-2.5">
                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={perfCheck1}
                    onChange={() => setPerfCheck1(!perfCheck1)}
                    disabled={perfCheckSubmitted}
                    className="mt-0.5 rounded text-primary focus:ring-primary"
                  />
                  <span>First Contentful Paint is under 1.8s (Current: 1.45s)</span>
                </label>
                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={perfCheck2}
                    onChange={() => setPerfCheck2(!perfCheck2)}
                    disabled={perfCheckSubmitted}
                    className="mt-0.5 rounded text-primary focus:ring-primary"
                  />
                  <span>Time to Interactive is under 2.5s (Current: 2.20s)</span>
                </label>
              </div>

              {!perfCheckSubmitted ? (
                <button
                  onClick={handlePerfCheckSubmit}
                  className="w-full mt-4 py-2 bg-primary text-white font-label-md text-xs rounded-lg shadow hover:bg-primary-container transition-all"
                >
                  Verify Load Speed
                </button>
              ) : (
                <div className="mt-3 text-green-700 font-semibold text-center flex items-center justify-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">check_circle</span>
                  Metrics verified successfully.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Hard: Manual performance input + waterfall visualization logs */}
        {difficulty === "hard" && (
          <div className="flex flex-col gap-4">
            {/* Waterfall display */}
            <div className="bg-inverse-surface text-white font-mono text-[10px] p-3 rounded-lg border border-white/5 flex flex-col gap-1.5">
              <span className="text-surface-variant font-bold">{"// NETWORK WATERFALL"}</span>
              <div className="flex items-center gap-2">
                <span className="w-14 text-outline font-semibold">GET /js</span>
                <div className="flex-1 bg-white/10 h-1.5 rounded overflow-hidden">
                  <div className="bg-blue-400 h-full w-[45%]"></div>
                </div>
                <span className="text-blue-400 font-bold shrink-0">1.45s</span>
              </div>
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <span className="w-14 text-outline font-semibold">GET /api</span>
                <div className="flex-1 bg-white/10 h-1.5 rounded overflow-hidden">
                  <div className="bg-yellow-400 h-full w-[65%]"></div>
                </div>
                <span className="text-yellow-400 font-bold shrink-0">2.20s</span>
              </div>
              <div className="flex justify-between text-outline text-[9px]">
                <span>FCP: 1.45s (1450ms)</span>
                <span>TTI: 2.20s (2200ms)</span>
              </div>
            </div>

            {/* Verification form */}
            {perfHardSubmitted && perfFeedback ? (
              <div className={`p-3 rounded-xl border text-[11px] font-semibold leading-relaxed ${
                perfFeedback.startsWith("Performance") 
                  ? "bg-green-50 border-green-200 text-green-700" 
                  : "bg-error-container/20 border-error/20 text-error"
              }`}>
                {perfFeedback}
                {!perfFeedback.startsWith("Performance") && (
                  <button onClick={() => setPerfHardSubmitted(false)} className="block mt-2 underline cursor-pointer text-xs font-semibold focus:outline-none">
                    Try Again
                  </button>
                )}
              </div>
            ) : (
              <form onSubmit={handlePerfHardSubmit} className="bg-surface-container border border-outline-variant/20 p-3.5 rounded-xl flex flex-col gap-3">
                <h4 className="font-label-sm text-xs font-bold text-on-surface uppercase">Input Metric Times (ms)</h4>
                
                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[10px] text-outline font-semibold">First Contentful Paint (FCP):</label>
                  <input
                    type="text"
                    value={fcpInput}
                    onChange={(e) => setFcpInput(e.target.value)}
                    placeholder="Enter FCP in ms"
                    className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px] outline-none"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[10px] text-outline font-semibold">Time to Interactive (TTI):</label>
                  <input
                    type="text"
                    value={ttiInput}
                    onChange={(e) => setTtiInput(e.target.value)}
                    placeholder="Enter TTI in ms"
                    className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px] outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!fcpInput.trim() || !ttiInput.trim()}
                  className="w-full mt-1 py-2 bg-error text-white font-label-md text-xs rounded-lg shadow hover:bg-error-container hover:text-on-error-container disabled:bg-outline-variant/40 disabled:cursor-not-allowed transition-all"
                >
                  Verify Metrics
                </button>
              </form>
            )}
          </div>
        )}

        {/* Default Easy / Info */}
        {difficulty === "easy" && (
          <div className="bg-primary-fixed border border-primary-fixed-dim p-4 rounded-xl font-body-sm text-[11px] text-on-primary-fixed-variant leading-relaxed">
            <h4 className="font-label-sm text-xs font-bold text-on-primary-fixed mb-1 uppercase">Automatic Monitoring</h4>
            <p>Under easy mode, performance metrics and load times conform by default. Focus entirely on verifying form validations and filing bug reports.</p>
          </div>
        )}
      </div>
    </div>
  );
}
