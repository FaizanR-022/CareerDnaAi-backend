"use client";

import React, { useState } from "react";

export default function DatabaseTab({ difficulty }) {
  const [submitted, setSubmitted] = useState(false);
  const [success, setSuccess] = useState(false);
  const [feedback, setFeedback] = useState("");
  
  // Easy mode states
  const [easySql, setEasySql] = useState("SELECT name, amount FROM users JOIN transactions ON users.id = transactions.user_id WHERE users.status = '[INSERT_STATUS]';");
  const [easyStatusSelect, setEasyStatusSelect] = useState("");

  // Medium mode states
  const [mediumSql, setMediumSql] = useState("SELECT user_id, ... FROM transactions ...;");

  // Hard mode states
  const [hardSql, setHardSql] = useState("-- Write complex multi-table query from scratch\n");
  const [dbLogs, setDbLogs] = useState([]);

  const handleEasySubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    if (easyStatusSelect === "active") {
      setSuccess(true);
      setFeedback("Query validation passed! Joined 2 tables and filtered active user accounts. Returning 14 records.");
    } else {
      setSuccess(false);
      setFeedback("Query validation failed. Status filter is empty or incorrect. (HCI tip: status should be 'active')");
    }
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    const cleanSql = mediumSql.replace(/\s+/g, " ").trim().toLowerCase();
    const hasGroupId = cleanSql.includes("group by user_id");
    const hasSum = cleanSql.includes("sum(amount)") || cleanSql.includes("sum(transactions.amount)");
    const hasSelect = cleanSql.includes("select user_id") || cleanSql.includes("select transactions.user_id");

    if (hasGroupId && hasSum && hasSelect) {
      setSuccess(true);
      setFeedback("Medium SQL query compiled successfully! Grouped aggregation successfully parsed. returning 5 records.");
    } else {
      setSuccess(false);
      setFeedback("SQL Syntax Error: Grouping column mismatch or missing SUM aggregate function. Review grouping criteria.");
    }
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    const cleanSql = hardSql.replace(/\s+/g, " ").trim().toLowerCase();
    
    // Check joins and aggregates
    const hasJoin = cleanSql.includes("join transactions") || cleanSql.includes("inner join transactions") || cleanSql.includes("join profiles");
    const hasGroup = cleanSql.includes("group by");
    const hasHaving = cleanSql.includes("having");
    const hasSumLimit = cleanSql.includes("sum(amount) > 1000") || cleanSql.includes("sum(transactions.amount) > 1000") || cleanSql.includes("total_spent > 1000");
    const hasCompleted = cleanSql.includes("status = 'completed'") || cleanSql.includes("status = \"completed\"");

    const logs = ["[DB] Compiling raw SQL query planner..."];

    if (hasJoin && hasGroup && hasHaving && hasSumLimit && hasCompleted) {
      setSuccess(true);
      setFeedback("Hard SQL query executed successfully! Plan cost optimized. Correct aggregate and filtering boundaries mapped. Returning 2 records.");
      logs.push("SUCCESS: Execution planner matches query schema constraint index mapping.");
      setDbLogs(logs);
    } else {
      setSuccess(false);
      setFeedback("SQL compilation failed. Silent execution output: 0 records returned.");
      logs.push("ERROR: Execution analyzer rejected query path. Review table aliases, aggregates, and HAVING predicates.");
      setDbLogs(logs);
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setEasyStatusSelect("");
    setEasySql("SELECT name, amount FROM users JOIN transactions ON users.id = transactions.user_id WHERE users.status = '[INSERT_STATUS]';");
    setMediumSql("SELECT user_id, ... FROM transactions ...;");
    setHardSql("-- Write complex multi-table query from scratch\n");
    setDbLogs([]);
  };

  return (
    <div className="flex-1 flex overflow-hidden font-body-md">
      {/* LEFT PANEL: DATABASE CONSOLE */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        {/* Header */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">SQL Database Triage Console</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Draft, debug, and execute database queries to verify schema logic mappings.</p>
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
              {success ? "SQL Verification Passed" : "Query Diagnostic Failure"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Revise Query" : "Try Again"}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col gap-6">
            
            {/* EASY WORKSPACE: Basic template with inline drop select */}
            {difficulty === "easy" && (
              <div className="flex flex-col gap-4">
                <div className="bg-inverse-surface rounded-2xl p-5 text-white font-mono text-[12px] leading-relaxed shadow-lg">
                  <span className="text-surface-variant font-bold">{"-- Pre-configured JOIN Query"}</span>
                  <div className="mt-2">
                    <span className="text-blue-300">SELECT</span> name, amount
                  </div>
                  <div>
                    <span className="text-blue-300">FROM</span> users
                  </div>
                  <div>
                    <span className="text-blue-300">JOIN</span> transactions <span className="text-blue-300">ON</span> users.id = transactions.user_id
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-blue-300">WHERE</span> users.status = 
                    <select
                      value={easyStatusSelect}
                      onChange={(e) => setEasyStatusSelect(e.target.value)}
                      className="bg-black/60 border border-white/20 rounded px-2 py-0.5 font-mono text-[11px] text-green-300 focus:outline-none"
                    >
                      <option value="">Select status...</option>
                      <option value="active">{"'active'"}</option>
                      <option value="pending">{"'pending'"}</option>
                      <option value="suspended">{"'suspended'"}</option>
                    </select>
                    <span className="text-white">;</span>
                  </div>
                </div>

                <div className="bg-primary/5 border border-primary/20 p-4 rounded-xl flex items-start gap-2.5">
                  <span className="material-symbols-outlined text-primary text-[18px]">lightbulb</span>
                  <div className="font-body-sm text-[12px] text-on-surface-variant">
                    <span className="font-bold text-primary">Hint:</span> Choose the status {"'active'"} to correctly filter and fetch user financial transactions.
                  </div>
                </div>

                <button
                  onClick={handleEasySubmit}
                  disabled={!easyStatusSelect}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container transition-all"
                >
                  Compile & Run SQL
                </button>
              </div>
            )}

            {/* MEDIUM WORKSPACE: Prompts user to write JOIN/GROUP BY queries */}
            {difficulty === "medium" && (
              <div className="flex flex-col gap-4">
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-4 font-body-sm text-xs text-on-surface-variant leading-relaxed shadow-sm">
                  <h3 className="font-label-sm text-xs font-bold text-on-surface mb-1">Scenario Checklist:</h3>
                  Write a query to retrieve the sum of transaction amounts (`amount`) for each user ID (`user_id`). The output must contain columns `user_id` and the summed total, grouped by `user_id`.
                </div>

                <div className="flex flex-col gap-2">
                  <span className="font-mono text-[10px] text-outline">{"// SQL Query Console"}</span>
                  <textarea
                    value={mediumSql}
                    onChange={(e) => setMediumSql(e.target.value)}
                    className="w-full h-32 bg-inverse-surface text-green-400 font-mono text-xs p-4 rounded-2xl outline-none resize-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <button
                  onClick={handleMediumSubmit}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container transition-all"
                >
                  Verify Query Stack
                </button>
              </div>
            )}

            {/* HARD WORKSPACE: Blank canvas, silent compile/errors */}
            {difficulty === "hard" && (
              <div className="flex flex-col gap-4">
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-4 font-body-sm text-xs text-on-surface-variant leading-relaxed shadow-sm">
                  <h3 className="font-label-sm text-xs font-bold text-on-surface mb-1">Scenario Checklist:</h3>
                  Write a SQL query that retrieves user emails (`email`), the sum of their transactions (`SUM(amount) AS total_spent`), and the transaction counts (`COUNT(transactions.id) AS tx_count`). 
                  - Join `users` and `transactions` using user ID references.
                  - Filter only transactions with status equal to {"'completed'"}.
                  - Group results by user email.
                  - Only show users whose total spent is greater than 1000.
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Editor */}
                  <div className="flex flex-col gap-2">
                    <span className="font-mono text-[10px] text-outline">{"// Scratchpad console"}</span>
                    <textarea
                      value={hardSql}
                      onChange={(e) => setHardSql(e.target.value)}
                      className="w-full h-44 bg-black/90 text-green-400 font-mono text-xs p-4 rounded-2xl outline-none resize-none focus:ring-1 focus:ring-error"
                    />
                  </div>

                  {/* Silent Logs monitor */}
                  <div className="flex flex-col gap-2">
                    <span className="font-label-sm text-xs font-bold text-on-surface">Execution logs:</span>
                    <div className="h-44 bg-black border border-white/10 rounded-2xl p-4 font-mono text-[9px] text-white/80 overflow-y-auto scrollbar-thin flex flex-col gap-1 select-none">
                      {dbLogs.length === 0 ? (
                        <div className="text-white/40">{"// No queries compiled yet. Console is idle."}</div>
                      ) : (
                        dbLogs.map((log, idx) => (
                          <div key={idx} className={log.includes("ERROR") ? "text-error" : log.includes("SUCCESS") ? "text-green-400" : "text-white/60"}>
                            {log}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleHardSubmit}
                  className="self-end py-2.5 px-6 bg-error text-white font-label-md text-xs rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container transition-all font-semibold"
                >
                  Compile & Execute SQL Planner
                </button>
              </div>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: SCHEMA GUIDE */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">storage</span>
          Database Schema
        </h3>

        <div className="flex flex-col gap-4 font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
          <div className="bg-surface-container border border-outline-variant/15 p-3.5 rounded-xl font-mono">
            <h4 className="font-bold text-on-surface text-xs uppercase mb-1">users Table</h4>
            <div className="text-[10px] text-outline flex flex-col">
              <span>id (INT, PK)</span>
              <span>name (VARCHAR)</span>
              <span>email (VARCHAR)</span>
              <span>status (VARCHAR) -- {"'active','suspended'"}</span>
            </div>
          </div>

          <div className="bg-surface-container border border-outline-variant/15 p-3.5 rounded-xl font-mono">
            <h4 className="font-bold text-on-surface text-xs uppercase mb-1">transactions Table</h4>
            <div className="text-[10px] text-outline flex flex-col">
              <span>id (INT, PK)</span>
              <span>user_id (INT, FK)</span>
              <span>amount (DECIMAL)</span>
              <span>status (VARCHAR) -- {"'completed','pending'"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
