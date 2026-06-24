"use client";

import React, { useState } from "react";

const rawJsonBlock = `{\n  "status": "error",\n  "error": {\n    "type": "SQL_CONN_TIMEOUT",\n    "trace": "DbConnectionExhausted: Pool size 20 hit."\n  }\n}`;

export default function ApiTab({ difficulty, apiLatency, setApiLatency }) {
  const [submitted, setSubmitted] = useState(false);
  const [success, setSuccess] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [showHint, setShowHint] = useState(false);

  // Easy/Medium states
  const [selectedErrorCode, setSelectedErrorCode] = useState("");
  const [previewWidgetActive, setPreviewWidgetActive] = useState(false);
  const [mediumChecking, setMediumChecking] = useState(false);

  // Hard states
  const [hardJsonText, setHardJsonText] = useState(`{
  "status": "error"
  "code": 500,
  "error": {
    "message": "Database deadlock detected",
    "details": "Deadlock found when trying to get lock"
  }
}`);
  const [terminalLogs, setTerminalLogs] = useState([
    "[SYSTEM] Initializing server gateway...",
    "[DEBUG] Route mapping registered: GET /api/v1/users/profile",
    "[ERROR] JSONParserException: Unexpected token 'code' at line 3. Expected comma separator after property value."
  ]);

  const handleEasySubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    setSuccess(true);
    setFeedback("Payload verified! The JSON is correctly formatted and standard REST codes mapped. Live client widget is active.");
    setPreviewWidgetActive(true);
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    if (!selectedErrorCode) return;

    setMediumChecking(true);
    setTimeout(() => {
      setMediumChecking(false);
      setSubmitted(true);
      if (selectedErrorCode === "500") {
        setSuccess(true);
        setFeedback("Success! You correctly triaged the unlabelled status code 500 (Internal Server Error) causing the dashboard crash. Staging refreshed.");
        setPreviewWidgetActive(true);
      } else {
        setSuccess(false);
        setFeedback("Triage Rejected. Status code mapping does not match the dashboard 500 stack trace. Please re-evaluate the raw JSON block.");
      }
    }, 1500); // Delayed feedback
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    
    // Check if comma was added after "status": "error"
    try {
      const parsed = JSON.parse(hardJsonText);
      if (parsed.status === "error" && parsed.code === 500) {
        setSuccess(true);
        setFeedback("Production pipeline restored! The malformed payload JSON syntax errors were successfully resolved. The terminal parser returns exit code 0.");
        setTerminalLogs(prev => [
          ...prev,
          "[SYSTEM] Parsing patched payload...",
          "[INFO] JSON formatting compliance check: OK",
          "[SUCCESS] Staging container built and deployed successfully."
        ]);
      } else {
        setSuccess(false);
        setFeedback("Triage Rejected. You modified core parameters. Ensure JSON syntax matches structure while maintaining code 500 status keys.");
      }
    } catch (err) {
      setSuccess(false);
      setFeedback(`Syntax Compilation Error: ${err.message}. Check missing commas or bracket matches.`);
      setTerminalLogs(prev => [
        ...prev,
        `[ERROR] JSONParserException: Failed to parse custom text. ${err.message}`
      ]);
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setSelectedErrorCode("");
    setPreviewWidgetActive(false);
    setShowHint(false);
    setHardJsonText(`{
  "status": "error"
  "code": 500,
  "error": {
    "message": "Database deadlock detected",
    "details": "Deadlock found when trying to get lock"
  }
}`);
    setTerminalLogs([
      "[SYSTEM] Initializing server gateway...",
      "[DEBUG] Route mapping registered: GET /api/v1/users/profile",
      "[ERROR] JSONParserException: Unexpected token 'code' at line 3. Expected comma separator after property value."
    ]);
  };

  return (
    <div className="flex-1 flex overflow-hidden font-body-md">
      {/* LEFT PANEL: API EDITOR */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">API Design & Payload Inspector</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Triage and resolve API payload structures and response mappings.</p>
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
              {success ? "API Resolved Successfully" : "Triage Rejected"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Revise Payload" : "Try Again"}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col gap-6">
            
            {/* EASY VIEW: Preformatted JSON + error map */}
            {difficulty === "easy" && (
              <div className="flex flex-col gap-5">
                <div className="grid grid-cols-2 gap-4">
                  
                  {/* Colored JSON */}
                  <div className="bg-inverse-surface rounded-2xl p-5 text-white font-mono text-[11px] leading-relaxed shadow-lg">
                    <div className="text-surface-variant font-bold mb-2">{"// Formatted JSON Response"}</div>
                    {"{"}
                    <div className="pl-6">
                      <span className="text-blue-300">{"\"status\""}</span>: <span className="text-green-300">{"\"success\""}</span>,
                    </div>
                    <div className="pl-6">
                      <span className="text-blue-300">{"\"code\""}</span>: <span className="text-amber-300">200</span>,
                    </div>
                    <div className="pl-6">
                      <span className="text-blue-300">{"\"data\""}</span>: {"{"}
                      <div className="pl-6">
                        <span className="text-blue-300">{"\"id\""}</span>: <span className="text-amber-300">4412</span>,
                      </div>
                      <div className="pl-6">
                        <span className="text-blue-300">{"\"name\""}</span>: <span className="text-green-300">{"\"Aiden\""}</span>,
                      </div>
                      <div className="pl-6">
                        <span className="text-blue-300">{"\"role\""}</span>: <span className="text-green-300">{"\"Frontend Dev\""}</span>
                      </div>
                      {"}"}
                    </div>
                    {"}"}
                  </div>

                  {/* REST Map */}
                  <div className="border border-outline-variant/30 rounded-2xl p-5 bg-surface-container-low font-body-sm text-xs text-on-surface-variant flex flex-col gap-2">
                    <h4 className="font-label-sm font-bold text-on-surface uppercase mb-1">Standard REST Error Map</h4>
                    <div className="flex justify-between border-b border-outline-variant/10 pb-1">
                      <span className="font-semibold">200 OK</span>
                      <span className="text-outline">Success response payload</span>
                    </div>
                    <div className="flex justify-between border-b border-outline-variant/10 pb-1">
                      <span className="font-semibold">401 Unauthorized</span>
                      <span className="text-outline">Missing credentials / tokens</span>
                    </div>
                    <div className="flex justify-between border-b border-outline-variant/10 pb-1">
                      <span className="font-semibold">404 Not Found</span>
                      <span className="text-outline">Endpoint route mapping incorrect</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-semibold">500 Internal Error</span>
                      <span className="text-outline">Uncaught exception / server crashed</span>
                    </div>
                  </div>
                </div>

                {/* Inline Hint */}
                <div className="bg-primary/5 border border-primary/20 p-4 rounded-xl flex items-start gap-2.5">
                  <span className="material-symbols-outlined text-primary text-[18px]">lightbulb</span>
                  <div className="font-body-sm text-[12px] text-on-surface-variant">
                    <span className="font-bold text-primary">Hint:</span> Select the REST code and click verification. Use the &quot;Live Widget Preview&quot; on the right to see immediately how the front-end fetches the user profile.
                  </div>
                </div>

                <button
                  onClick={handleEasySubmit}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container transition-all"
                >
                  Verify Payload
                </button>
              </div>
            )}

            {/* MEDIUM VIEW: Raw JSON + Unlabelled codes + Request Hint toggle */}
            {difficulty === "medium" && (
              <div className="flex flex-col gap-5">
                <div className="grid grid-cols-2 gap-4">
                  {/* Raw JSON block */}
                  <div className="bg-black/85 rounded-2xl p-5 text-white/90 font-mono text-[11px] leading-relaxed shadow-lg whitespace-pre">
                    <div className="text-white/40 mb-2">{"// Raw JSON API Response Block"}</div>
                    {rawJsonBlock}
                  </div>

                  {/* Dropdown to select unlabelled code */}
                  <div className="border border-outline-variant/30 rounded-2xl p-5 bg-surface-container-low flex flex-col gap-4">
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-xs font-bold text-on-surface">Identify the response status code:</label>
                      <p className="font-body-sm text-[11px] text-outline">The frontend received this unlabelled payload during database pool timeouts.</p>
                    </div>

                    <select
                      value={selectedErrorCode}
                      onChange={(e) => setSelectedErrorCode(e.target.value)}
                      className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 text-xs outline-none text-on-surface"
                    >
                      <option value="" className="bg-surface text-on-surface">Choose status code...</option>
                      <option value="400" className="bg-surface text-on-surface">400 Bad Request</option>
                      <option value="401" className="bg-surface text-on-surface">401 Unauthorized</option>
                      <option value="403" className="bg-surface text-on-surface">403 Forbidden</option>
                      <option value="404" className="bg-surface text-on-surface">404 Not Found</option>
                      <option value="500" className="bg-surface text-on-surface">500 Internal Server Error</option>
                    </select>

                    {/* Hint toggle */}
                    <div>
                      <button
                        type="button"
                        onClick={() => setShowHint(!showHint)}
                        className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-[14px]">help</span>
                        {showHint ? "Hide Hint" : "Request Hint"}
                      </button>
                      
                      {showHint && (
                        <p className="font-body-sm text-[11px] text-on-surface-variant bg-surface border border-outline-variant/10 rounded-lg p-3 mt-2 leading-relaxed">
                          Database connection drops or pools sizing limits are server-side failures. Therefore, they map to the 5xx HTTP response range.
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleMediumSubmit}
                  disabled={!selectedErrorCode || mediumChecking}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                >
                  {mediumChecking && (
                    <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                  )}
                  Triage Status Code
                </button>
              </div>
            )}

            {/* HARD VIEW: Raw malformed nested JSON + Terminal Logs block */}
            {difficulty === "hard" && (
              <div className="flex flex-col gap-5">
                <div className="grid grid-cols-2 gap-4">
                  {/* Editor */}
                  <div className="flex flex-col gap-2">
                    <label className="font-label-sm text-xs font-bold text-on-surface">Edit API Response Syntax:</label>
                    <textarea
                      value={hardJsonText}
                      onChange={(e) => setHardJsonText(e.target.value)}
                      className="w-full h-44 bg-black/90 text-green-400 font-mono text-xs p-4 rounded-2xl outline-none resize-none focus:ring-1 focus:ring-error"
                    />
                  </div>

                  {/* Terminal traces */}
                  <div className="flex flex-col gap-2">
                    <span className="font-label-sm text-xs font-bold text-on-surface">Terminal Logs:</span>
                    <div className="h-44 bg-black border border-white/10 rounded-2xl p-4 font-mono text-[9px] text-white/80 overflow-y-auto scrollbar-thin flex flex-col gap-1 select-none">
                      {terminalLogs.map((log, idx) => (
                        <div key={idx} className={log.includes("ERROR") ? "text-error" : log.includes("SUCCESS") ? "text-green-400" : "text-white/60"}>
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleHardSubmit}
                  className="self-end py-2.5 px-6 bg-error text-white font-label-md text-xs rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container transition-all font-semibold"
                >
                  Compile & Deploy Payload
                </button>
              </div>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: LIVE CLIENT PREVIEW */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">devices</span>
          Widget Staging
        </h3>

        <div className="flex-1 bg-surface-container-low border border-outline-variant/30 rounded-2xl p-4 flex flex-col justify-center items-stretch relative min-h-[300px] overflow-hidden">
          
          {/* Easy widget live preview */}
          {difficulty === "easy" && previewWidgetActive && (
            <div className="bg-surface rounded-xl border border-outline-variant/20 p-4 shadow-sm text-center flex flex-col gap-3 font-body-sm text-[12px] animate-fade-in">
              <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs mx-auto">
                AI
              </div>
              <div>
                <h4 className="font-bold text-on-surface">Aiden</h4>
                <p className="text-outline text-[10px]">Frontend Lead</p>
              </div>
              <div className="text-[10px] text-green-700 bg-green-50 border border-green-200 rounded py-1 px-2 font-semibold">
                Status: 200 OK
              </div>
            </div>
          )}

          {difficulty === "easy" && !previewWidgetActive && (
            <div className="text-center text-outline flex flex-col items-center gap-3">
              <span className="material-symbols-outlined text-[40px] text-outline-variant">api</span>
              <p className="font-body-sm text-[12px]">Widget state: Idle</p>
              <button
                onClick={() => setPreviewWidgetActive(true)}
                className="py-1.5 px-3 bg-primary/10 text-primary text-xs rounded-lg hover:bg-primary/20 font-semibold"
              >
                Live Widget Preview
              </button>
            </div>
          )}

          {/* Medium widget preview */}
          {difficulty === "medium" && previewWidgetActive && (
            <div className="bg-surface rounded-xl border border-outline-variant/20 p-4 shadow-sm text-center flex flex-col gap-3 font-body-sm text-[12px] animate-fade-in">
              <span className="material-symbols-outlined text-[36px] text-green-600">check_circle</span>
              <h4 className="font-bold text-on-surface">Dashboard Restored</h4>
              <p className="text-outline text-[10px]">Database connection issue resolved by HTTP status mapping.</p>
            </div>
          )}

          {difficulty === "medium" && !previewWidgetActive && (
            <div className="text-center text-outline flex flex-col items-center gap-2">
              <span className="material-symbols-outlined text-[40px] text-error animate-pulse">error</span>
              <p className="font-body-sm text-[12px] text-error font-semibold">500 Internal Error</p>
              <p className="font-body-sm text-[10px] text-outline-variant">User dashboard card is blank. Triage status code mapping to debug.</p>
            </div>
          )}

          {/* Hard widget preview */}
          {difficulty === "hard" && success && (
            <div className="bg-surface rounded-xl border border-outline-variant/20 p-4 shadow-sm text-center flex flex-col gap-3 font-body-sm text-[12px] animate-fade-in">
              <span className="material-symbols-outlined text-[36px] text-green-600">dns</span>
              <h4 className="font-bold text-on-surface">Server Live</h4>
              <p className="text-outline text-[10px]">JSON Parser compiled successfully.</p>
            </div>
          )}

          {difficulty === "hard" && !success && (
            <div className="text-center text-outline flex flex-col items-center gap-2">
              <span className="material-symbols-outlined text-[40px] text-error">build</span>
              <p className="font-body-sm text-[12px] text-error font-semibold">JSON Syntax Corrupted</p>
              <p className="font-body-sm text-[10px] text-outline-variant">Server gateway is offline. Review terminal logs to solve parsing exceptions.</p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
