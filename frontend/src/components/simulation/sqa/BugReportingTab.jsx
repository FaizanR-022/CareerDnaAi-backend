"use client";

import React, { useState } from "react";

export default function BugReportingTab({ difficulty, bugsFound, setBugsFound, testCoverage, setTestCoverage }) {
  // Easy values
  const [givenVal, setGivenVal] = useState("");
  const [whenVal, setWhenVal] = useState("");
  const [thenVal, setThenVal] = useState("");

  // Medium values
  const [medTitle, setMedTitle] = useState("");
  const [medExpected, setMedExpected] = useState("");
  const [medActual, setMedActual] = useState("");
  const [medSeverity, setMedSeverity] = useState("High");

  // Hard values
  const [hardSuiteId, setHardSuiteId] = useState("");
  const [hardPrecondition, setHardPrecondition] = useState("");
  const [hardEdgeCases, setHardEdgeCases] = useState("");
  const [hardSeverity, setHardSeverity] = useState("Critical");
  const [hardJustification, setHardJustification] = useState("");

  // Submission / Evaluation states
  const [submitted, setSubmitted] = useState(false);
  const [success, setSuccess] = useState(false);
  const [feedback, setFeedback] = useState("");

  const handleEasySubmit = (e) => {
    e.preventDefault();
    if (!givenVal.trim() || !whenVal.trim() || !thenVal.trim()) return;

    setSubmitted(true);
    setSuccess(true);
    setFeedback("Scenario builder compiled successfully! Standard 'GIVEN-WHEN-THEN' test case written and added to backlog. Bugs Found +1, Coverage +10%.");
    setBugsFound(Math.min(bugsFound + 1, 3));
    setTestCoverage(Math.min(testCoverage + 10, 100));
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    if (!medTitle.trim() || !medExpected.trim() || !medActual.trim()) return;

    setSubmitted(true);
    setSuccess(true);
    setFeedback(`Test Case '${medTitle}' logged. Severity marked as '${medSeverity}'. Bug ticket pushed to Engineering backlog. Bugs Found +1, Coverage +15%.`);
    setBugsFound(Math.min(bugsFound + 1, 3));
    setTestCoverage(Math.min(testCoverage + 15, 100));
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    if (!hardSuiteId.trim() || !hardPrecondition.trim() || !hardEdgeCases.trim() || !hardJustification.trim()) return;

    setSubmitted(true);
    const lowerJust = hardJustification.toLowerCase();
    
    // Check if they write a logical justification (mentions blocks, payments, PRD conflict, or security)
    const validJustification = lowerJust.includes("block") || 
                               lowerJust.includes("conflict") || 
                               lowerJust.includes("security") || 
                               lowerJust.includes("payment") || 
                               lowerJust.includes("prd") ||
                               lowerJust.includes("gate");

    if (validJustification && hardSeverity === "Critical") {
      setSuccess(true);
      setFeedback("Severity Justified! Dan (Frontend Dev) reviewed your justification: 'The guest checkout registration bypass creates database consistency gaps and security risks which block payment flows.' Severity approved as Critical. Backlog updated. Bugs Found +1, Coverage +20%.");
      setBugsFound(Math.min(bugsFound + 1, 3));
      setTestCoverage(Math.min(testCoverage + 20, 100));
    } else {
      setSuccess(false);
      setFeedback("Justification Rejected: Stakeholder pushback wins. Your written argument was insufficient. Explain how this PRD conflict blocks core payment safety and checkout integrity.");
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setGivenVal("");
    setWhenVal("");
    setThenVal("");
    setMedTitle("");
    setMedExpected("");
    setMedActual("");
    setHardSuiteId("");
    setHardPrecondition("");
    setHardEdgeCases("");
    setHardJustification("");
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: BUG REPORT WORKSPACE */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Test Case Writing & Bug Triage</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Log your verified defects and configure severity rules for the dev backlog.</p>
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
              {success ? "Bug Logged & Verified" : "Severity Triage Blocked"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Create Next Ticket" : "Revise Justification"}
              </button>
            </div>
          </div>
        ) : (
          /* Log Forms */
          <div className="flex-1 flex flex-col gap-6">

            {/* EASY DIFFICULTY: GIVEN-WHEN-THEN scenario builder */}
            {difficulty === "easy" && (
              <form onSubmit={handleEasySubmit} className="flex flex-col gap-5">
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-4">GIVEN-WHEN-THEN Test Builder</h3>
                  
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">1. Given (Precondition/Input State)</label>
                      <input
                        type="text"
                        value={givenVal}
                        onChange={(e) => setGivenVal(e.target.value)}
                        placeholder="e.g. user enters invalid email formatting"
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
                      />
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">2. When (Action Event)</label>
                      <input
                        type="text"
                        value={whenVal}
                        onChange={(e) => setWhenVal(e.target.value)}
                        placeholder="e.g. user clicks the payment checkout submit button"
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
                      />
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">3. Then (Expected Outcome)</label>
                      <input
                        type="text"
                        value={thenVal}
                        onChange={(e) => setThenVal(e.target.value)}
                        placeholder="e.g. visual red email formatting validation error displays"
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
                      />
                    </div>
                  </div>
                </div>

                {/* Bug Triage section */}
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-3">Backlog Metadata</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Bug Title</label>
                      <input disabled type="text" value="Stripe payment checkout - email validation bypass" className="bg-surface-container-low border border-outline-variant/35 rounded-lg p-2.5 font-body-sm text-[13px] text-on-surface-variant opacity-75 cursor-not-allowed" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Severity Triage</label>
                      <select disabled className="bg-surface-container-low border border-outline-variant/35 rounded-lg p-2.5 font-body-sm text-[13px] text-on-surface-variant opacity-75 cursor-not-allowed">
                        <option>High Severity (Pre-classified)</option>
                      </select>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!givenVal.trim() || !whenVal.trim() || !thenVal.trim()}
                  className="self-end py-3 px-6 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all"
                >
                  Create Bug Ticket
                </button>
              </form>
            )}

            {/* MEDIUM DIFFICULTY: Standard bug log & severity select */}
            {difficulty === "medium" && (
              <form onSubmit={handleMediumSubmit} className="flex flex-col gap-5">
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-4">Create Test Case & Log Ticket</h3>
                  
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Test Title / Scenario Name</label>
                      <input
                        type="text"
                        value={medTitle}
                        onChange={(e) => setMedTitle(e.target.value)}
                        placeholder="e.g. TC_04: Verification of 16-digit card limits"
                        className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1">
                        <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Expected Behavior</label>
                        <textarea
                          value={medExpected}
                          onChange={(e) => setMedExpected(e.target.value)}
                          placeholder="What the form is supposed to do..."
                          className="h-20 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[13px] resize-none outline-none"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Actual Behavior (Observed Defect)</label>
                        <textarea
                          value={medActual}
                          onChange={(e) => setMedActual(e.target.value)}
                          placeholder="What actually happens (Console Exception/silent block)..."
                          className="h-20 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[13px] resize-none outline-none"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm flex flex-col gap-4">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface">Severity Classification</h3>
                  <div className="flex flex-col gap-1.5">
                    <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Choose Severity</label>
                    <select
                      value={medSeverity}
                      onChange={(e) => setMedSeverity(e.target.value)}
                      className="bg-surface border border-outline-variant rounded-lg p-2.5 font-body-sm text-[13px] focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                      <option value="Low">Low Severity (UI tweak, formatting mismatch)</option>
                      <option value="Medium">Medium Severity (Functional glitch, workaround exists)</option>
                      <option value="High">High Severity (Major feature fails on specific devices)</option>
                      <option value="Critical">Critical Severity (Core flow blocked, blocks payment/invoicing)</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!medTitle.trim() || !medExpected.trim() || !medActual.trim()}
                  className="self-end py-3 px-6 bg-tertiary-container text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-tertiary disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all"
                >
                  Log Bug to Board
                </button>
              </form>
            )}

            {/* HARD DIFFICULTY: Edge Case Suites + Severity Justifications */}
            {difficulty === "hard" && (
              <form onSubmit={handleHardSubmit} className="flex flex-col gap-5">
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface mb-4">Create Test Suite (Edge Cases)</h3>
                  
                  <div className="flex flex-col gap-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1">
                        <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Test Suite ID</label>
                        <input
                          type="text"
                          value={hardSuiteId}
                          onChange={(e) => setHardSuiteId(e.target.value)}
                          placeholder="e.g. SUITE_CHECKOUT_0x4"
                          className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px]"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Pre-conditions & Setup</label>
                        <input
                          type="text"
                          value={hardPrecondition}
                          onChange={(e) => setHardPrecondition(e.target.value)}
                          placeholder="e.g. network throttled, guest checkout session active"
                          className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px]"
                        />
                      </div>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Edge Cases Assertions (Verify boundaries/empty values)</label>
                      <textarea
                        value={hardEdgeCases}
                        onChange={(e) => setHardEdgeCases(e.target.value)}
                        placeholder="Detail specific assertions (e.g. Assert that submitting card details with invalid password length triggers silent fail state check)..."
                        className="h-20 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2 font-body-sm text-[12px] resize-none outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Severity justifying */}
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm flex flex-col gap-4">
                  <h3 className="font-label-md text-label-md font-bold text-on-surface">Stakeholder Conflict Triage</h3>
                  
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Mark Severity Level</label>
                      <select
                        value={hardSeverity}
                        onChange={(e) => setHardSeverity(e.target.value)}
                        className="bg-surface border border-outline-variant rounded-lg p-2.5 font-body-sm text-[13px] focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="Low">Low Severity (UI tweak)</option>
                        <option value="Medium">Medium Severity ( glitched workaround )</option>
                        <option value="High">High Severity (Major feature broken)</option>
                        <option value="Critical">Critical Severity (Core flow blocked / blocks payment)</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">Severity Justification Against Pushback</label>
                      <p className="font-body-sm text-[11px] text-outline-variant italic bg-surface-container-low p-2.5 border border-outline-variant/20 rounded-lg">
                        Dan (Dev NPC): &quot;Guest checkout registration bypass is a feature, not a bug. Justify why this is a Critical issue.&quot;
                      </p>
                      <textarea
                        value={hardJustification}
                        onChange={(e) => setHardJustification(e.target.value)}
                        placeholder="Write your justification (mention how it violates PRD specifications, blocks secure checkout, or risks payment integrity)..."
                        className="h-24 bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[12px] resize-none outline-none transition-all"
                      />
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!hardSuiteId.trim() || !hardPrecondition.trim() || !hardEdgeCases.trim() || !hardJustification.trim()}
                  className="self-end py-3 px-6 bg-error text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all font-semibold"
                >
                  File Defect Report
                </button>
              </form>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: TRIAGE RULES */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">assessment</span>
          Triage Rules
        </h3>

        <div className="flex flex-col gap-4 font-body-sm text-[11px] text-on-surface-variant leading-relaxed">
          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1.5 uppercase">Severity Guidelines</h4>
            <ul className="list-disc pl-4 flex flex-col gap-1.5">
              <li><strong>Critical</strong>: The application crashes, data is corrupted, or a core invoicing flow is completely blocked.</li>
              <li><strong>High</strong>: A key feature is inoperable, but users can complete the transaction via workarounds.</li>
              <li><strong>Low</strong>: Minor visual alignments, margins, or spelling mistakes that do not affect function.</li>
            </ul>
          </div>

          <div className="bg-error-container/20 border border-error/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-error mb-1.5 uppercase">Stakeholder Pushback</h4>
            <p>Under Hard mode, developers will push back to avoid delaying releases. SQA must state clear facts (such as PRD violations, browser logs, and safety exploits) to justify ticket triage levels.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
