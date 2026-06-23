"use client";

import React, { useState } from "react";

export default function DataExplorerTab({ 
  difficulty, 
  data, 
  setData, 
  isCleaned, 
  setIsCleaned,
  originalData
}) {
  // Hard difficulty Schema Lock state
  const [schemaAccessRequested, setSchemaAccessRequested] = useState(false);
  const [schemaAccessApproved, setSchemaAccessApproved] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(false);

  // Manual step strategies for Medium difficulty
  const [nullStrategy, setNullStrategy] = useState("");
  const [dupStrategy, setDupStrategy] = useState("");

  // Terminal command state for Hard difficulty cleaning
  const [terminalCommand, setTerminalCommand] = useState("");
  const [terminalLogs, setTerminalLogs] = useState([]);

  // Raw JSON edit state for Hard difficulty (lazy state initialization)
  const [rawJsonText, setRawJsonText] = useState(() => JSON.stringify(data, null, 2));

  // One-Click Clean for Easy
  const handleOneClickClean = () => {
    // Drop duplicates
    let cleaned = [];
    const timestampsSeen = new Set();
    
    originalData.forEach((row) => {
      if (!timestampsSeen.has(row.timestamp)) {
        timestampsSeen.add(row.timestamp);
        // Impute nulls with a reasonable default/average (e.g. 28000)
        const volumeVal = row.volume === null ? 28000 : row.volume;
        cleaned.push({
          ...row,
          volume: volumeVal,
        });
      }
    });

    setData(cleaned);
    setRawJsonText(JSON.stringify(cleaned, null, 2));
    setIsCleaned(true);
  };

  // Manual pipeline clean for Medium
  const handleMediumClean = () => {
    if (!nullStrategy || !dupStrategy) {
      alert("Please select both a Null Handling and a Duplicate Handling strategy first!");
      return;
    }

    let cleaned = [];
    const timestampsSeen = new Set();

    originalData.forEach((row) => {
      // Duplicate handling
      let skip = false;
      if (dupStrategy === "drop_dups") {
        if (timestampsSeen.has(row.timestamp)) {
          skip = true;
        } else {
          timestampsSeen.add(row.timestamp);
        }
      }

      if (skip) return;

      // Null handling
      let volumeVal = row.volume;
      if (row.volume === null) {
        if (nullStrategy === "drop_nulls") {
          return; // skips this row
        } else if (nullStrategy === "fill_avg") {
          volumeVal = 28000;
        } else if (nullStrategy === "fill_zero") {
          volumeVal = 0;
        }
      }

      cleaned.push({
        ...row,
        volume: volumeVal,
      });
    });

    setData(cleaned);
    setRawJsonText(JSON.stringify(cleaned, null, 2));
    setIsCleaned(true);
  };

  // Schema Unlock flow for Hard
  const handleRequestSchema = () => {
    setSchemaAccessRequested(true);
    setLoadingSchema(true);
    setTimeout(() => {
      setLoadingSchema(false);
      setSchemaAccessApproved(true);
    }, 1500);
  };

  // Terminal execution for Hard
  const executeTerminalCommand = (e) => {
    e.preventDefault();
    if (!terminalCommand.trim()) return;

    const cmd = terminalCommand.trim().toLowerCase();
    let logs = [`$ ${terminalCommand}`];

    if (cmd === "clean_data --drop-nulls --drop-duplicates" || cmd === "python clean.py") {
      logs.push("Executing data cleaning pipeline...");
      logs.push("Analyzing records: 10 rows loaded.");
      logs.push("SUCCESS: Removed 1 duplicate row.");
      logs.push("SUCCESS: Imputed 2 null fields in 'volume' column.");
      logs.push("Dataset successfully written back to memory.");
      
      // Clean data
      const timestampsSeen = new Set();
      let cleaned = [];
      originalData.forEach((row) => {
        if (!timestampsSeen.has(row.timestamp)) {
          timestampsSeen.add(row.timestamp);
          const volumeVal = row.volume === null ? 28000 : row.volume;
          cleaned.push({ ...row, volume: volumeVal });
        }
      });
      setData(cleaned);
      setRawJsonText(JSON.stringify(cleaned, null, 2));
      setIsCleaned(true);
    } else if (cmd === "help") {
      logs.push("Available commands:");
      logs.push("  clean_data --drop-nulls --drop-duplicates   - Runs the built-in clean wrapper script");
      logs.push("  python clean.py                             - Runs pandas data cleaning scripts");
      logs.push("  cat schema.json                             - Displays the database schema");
    } else if (cmd === "cat schema.json") {
      if (!schemaAccessApproved) {
        logs.push("ERROR: Access Denied. Schema token is locked. Run 'Request Schema Access' or authorize.");
      } else {
        logs.push(JSON.stringify({
          columns: {
            timestamp: "VARCHAR(10) PRIMARY KEY",
            volume: "INT NULLABLE",
            rsi: "INT CHECK(rsi BETWEEN 0 AND 100)",
            type: "VARCHAR(20) [Retail, Institutional]"
          }
        }, null, 2));
      }
    } else {
      logs.push(`bash: command not found: ${terminalCommand}. Type 'help' for instructions.`);
    }

    setTerminalLogs((prev) => [...prev, ...logs]);
    setTerminalCommand("");
  };

  // Manual save for Hard JSON edits
  const handleSaveJsonEdit = () => {
    try {
      const parsed = JSON.parse(rawJsonText);
      if (!Array.isArray(parsed)) {
        alert("Data must be an array of objects!");
        return;
      }
      setData(parsed);
      
      // Basic check if they fixed it manually
      const hasNull = parsed.some(r => r.volume === null || r.volume === undefined);
      const timestamps = parsed.map(r => r.timestamp);
      const hasDup = new Set(timestamps).size !== timestamps.length;
      
      if (!hasNull && !hasDup) {
        setIsCleaned(true);
        alert("JSON updated successfully! No nulls or duplicates detected.");
      } else {
        setIsCleaned(false);
        alert("JSON updated, but data still contains nulls or duplicates.");
      }
    } catch (err) {
      alert("Invalid JSON format! Please check syntax brackets and commas.");
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: DATA VIEWER & PIPELINE CONTROLS */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Financial Transaction Log</h2>
            <p className="font-body-sm text-[13px] text-on-surface-variant">Clean the trading dataset to enable visualization trends.</p>
          </div>
          
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${isCleaned ? "bg-primary animate-pulse" : "bg-error"}`}></span>
            <span className="font-label-sm text-label-sm font-semibold uppercase">
              {isCleaned ? "Data Cleaned" : "Data Dirty / Unverified"}
            </span>
          </div>
        </div>

        {/* Dynamic Controls based on Difficulty */}
        {difficulty === "easy" && (
          <div className="bg-primary-fixed border border-primary-fixed-dim rounded-xl p-4 mb-6 flex items-center justify-between shadow-sm">
            <div className="flex gap-3 items-center">
              <span className="material-symbols-outlined text-[24px] text-primary">auto_fix_high</span>
              <div>
                <h3 className="font-label-md text-label-md font-bold text-on-primary-fixed">One-Click Clean Available</h3>
                <p className="font-body-sm text-[12px] text-on-primary-fixed-variant">System detects 2 nulls and 1 duplicate. Click to execute automatically.</p>
              </div>
            </div>
            <button
              onClick={handleOneClickClean}
              className="py-2 px-5 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              One-Click Clean
            </button>
          </div>
        )}

        {difficulty === "medium" && (
          <div className="bg-surface-container border border-outline-variant/30 rounded-xl p-5 mb-6 shadow-sm">
            <h3 className="font-label-md text-label-md font-bold text-on-surface mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px] text-tertiary-container">tune</span>
              Manual Pipeline Configuration
            </h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Null Handling */}
              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-[12px] text-outline font-semibold">1. Null Handling Strategy</label>
                <select
                  value={nullStrategy}
                  onChange={(e) => setNullStrategy(e.target.value)}
                  className="bg-surface border border-outline-variant rounded-lg p-2 font-body-sm text-[13px] focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">Select strategy...</option>
                  <option value="drop_nulls">Drop rows with null values</option>
                  <option value="fill_avg">Impute with volume average (28,000)</option>
                  <option value="fill_zero">Fill null values with 0</option>
                </select>
              </div>

              {/* Duplicate Handling */}
              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-[12px] text-outline font-semibold">2. Duplicate Handling Strategy</label>
                <select
                  value={dupStrategy}
                  onChange={(e) => setDupStrategy(e.target.value)}
                  className="bg-surface border border-outline-variant rounded-lg p-2 font-body-sm text-[13px] focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">Select strategy...</option>
                  <option value="drop_dups">Drop duplicate rows (keep first)</option>
                  <option value="keep_all">Keep all rows (allow duplicates)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-outline-variant/20">
              <span className="font-body-sm text-[11px] text-outline-variant italic">Select pipelines to unlock visualization rendering.</span>
              <button
                onClick={handleMediumClean}
                className="py-2 px-5 bg-tertiary-container text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-tertiary hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                Execute Cleaning Pipeline
              </button>
            </div>
          </div>
        )}

        {difficulty === "hard" && (
          <div className="bg-inverse-surface border border-white/5 rounded-xl p-5 mb-6 text-white shadow-xl flex flex-col gap-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-label-md text-label-md font-bold text-white flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-error">terminal</span>
                  CLI Cleaning Terminal & JSON Editor
                </h3>
                <p className="font-body-sm text-[12px] text-surface-variant">Type commands to clean or edit the raw JSON records manually.</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleSaveJsonEdit}
                  className="py-1 px-3 bg-primary text-white font-label-sm text-xs rounded hover:bg-primary-container transition-colors"
                >
                  Save JSON Changes
                </button>
              </div>
            </div>

            <div className="grid grid-cols-5 gap-4">
              {/* RAW JSON Textarea */}
              <div className="col-span-3 flex flex-col">
                <label className="font-label-sm text-[11px] text-surface-variant font-semibold mb-1">Raw Database Logs</label>
                <textarea
                  value={rawJsonText}
                  onChange={(e) => setRawJsonText(e.target.value)}
                  className="w-full h-44 bg-black/40 border border-white/10 rounded-lg p-2 font-mono text-[11px] text-green-400 focus:outline-none focus:border-primary scrollbar-thin resize-none"
                />
              </div>

              {/* Interactive terminal output */}
              <div className="col-span-2 flex flex-col">
                <label className="font-label-sm text-[11px] text-surface-variant font-semibold mb-1">Terminal Output</label>
                <div className="flex-1 h-32 bg-black border border-white/10 rounded-lg p-2 font-mono text-[10px] text-white/90 overflow-y-auto scrollbar-thin flex flex-col gap-1">
                  <div className="text-surface-variant">{"Type 'help' for instructions."}</div>
                  {terminalLogs.map((log, i) => (
                    <div key={i} className={log.startsWith("$") ? "text-primary-fixed-dim" : log.startsWith("SUCCESS") ? "text-green-400" : log.startsWith("ERROR") ? "text-error" : "text-white/70"}>
                      {log}
                    </div>
                  ))}
                </div>
                <form onSubmit={executeTerminalCommand} className="mt-1 flex">
                  <input
                    type="text"
                    value={terminalCommand}
                    onChange={(e) => setTerminalCommand(e.target.value)}
                    placeholder="clean_data --drop-nulls..."
                    className="flex-1 bg-black/60 border border-white/10 border-r-0 rounded-l-lg px-2 py-1 font-mono text-[11px] text-white focus:outline-none focus:border-primary"
                  />
                  <button type="submit" className="px-3 bg-white/10 hover:bg-white/20 border border-white/10 rounded-r-lg font-mono text-[11px]">Run</button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* DATA TABLE VIEW */}
        <div className="flex-1 border border-outline-variant/20 rounded-xl overflow-hidden bg-surface shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left font-body-sm text-[13px]">
              <thead>
                <tr className="bg-surface-container border-b border-outline-variant/30 font-label-sm text-outline">
                  <th className="p-3">Index</th>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Volume</th>
                  <th className="p-3">RSI</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Issues</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {data.map((row, index) => {
                  // Identify dirty elements
                  const isNullVolume = row.volume === null || row.volume === undefined;
                  
                  // Check duplicate timestamps in original dataset
                  const isDuplicate = originalData.filter(r => r.timestamp === row.timestamp).length > 1;
                  
                  let issueText = "";
                  if (isNullVolume) issueText += "Null Volume ";
                  if (isDuplicate && !isCleaned) issueText += "Duplicate Timestamp";

                  return (
                    <tr 
                      key={index} 
                      className={`transition-colors duration-150 ${
                        isNullVolume ? "bg-error/5 hover:bg-error/10" : isDuplicate && !isCleaned ? "bg-tertiary-container/5 hover:bg-tertiary-container/10" : "hover:bg-surface-container-low"
                      }`}
                    >
                      <td className="p-3 text-outline font-mono text-[11px]">{index + 1}</td>
                      <td className="p-3 font-semibold font-mono">{row.timestamp}</td>
                      <td className={`p-3 font-mono ${isNullVolume ? "text-error font-extrabold" : ""}`}>
                        {isNullVolume ? "NULL" : row.volume.toLocaleString()}
                      </td>
                      <td className="p-3 font-mono">{row.rsi}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                          row.type === "Institutional" ? "bg-primary-fixed text-on-primary-fixed" : "bg-surface-container-high text-on-surface-variant"
                        }`}>
                          {row.type}
                        </span>
                      </td>
                      <td className="p-3 font-semibold text-[11px]">
                        {issueText ? (
                          <span className={`flex items-center gap-1 ${isNullVolume ? "text-error" : "text-tertiary-container"}`}>
                            <span className="material-symbols-outlined text-[14px]">warning</span>
                            {issueText}
                          </span>
                        ) : (
                          <span className="text-primary flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">check_circle</span>
                            OK
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: SCHEMA EXPLORER */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">schema</span>
          Schema Explorer
        </h3>

        {difficulty === "easy" && (
          <div className="flex flex-col gap-4">
            <div className="border border-outline-variant/30 rounded-xl p-3 bg-surface-container-low">
              <div className="flex justify-between items-start mb-1">
                <span className="font-mono text-xs font-bold text-primary">timestamp</span>
                <span className="font-label-sm text-[11px] text-outline font-semibold">VARCHAR</span>
              </div>
              <p className="font-body-sm text-[11px] text-on-surface-variant">Daily transaction timestamp. Identifies distinct days. Must be unique.</p>
            </div>
            
            <div className="border border-outline-variant/30 rounded-xl p-3 bg-surface-container-low">
              <div className="flex justify-between items-start mb-1">
                <span className="font-mono text-xs font-bold text-primary">volume</span>
                <span className="font-label-sm text-[11px] text-outline font-semibold">INTEGER</span>
              </div>
              <p className="font-body-sm text-[11px] text-on-surface-variant">Number of trades executed. Represents liquidity. Watch for null cells representing processing dropouts.</p>
            </div>

            <div className="border border-outline-variant/30 rounded-xl p-3 bg-surface-container-low">
              <div className="flex justify-between items-start mb-1">
                <span className="font-mono text-xs font-bold text-primary">rsi</span>
                <span className="font-label-sm text-[11px] text-outline font-semibold">INTEGER</span>
              </div>
              <p className="font-body-sm text-[11px] text-on-surface-variant">Relative Strength Index (0-100). Technical momentum indicator. Values &gt; 70 signify overbought conditions.</p>
            </div>

            <div className="border border-outline-variant/30 rounded-xl p-3 bg-surface-container-low">
              <div className="flex justify-between items-start mb-1">
                <span className="font-mono text-xs font-bold text-primary">type</span>
                <span className="font-label-sm text-[11px] text-outline font-semibold">VARCHAR</span>
              </div>
              <p className="font-body-sm text-[11px] text-on-surface-variant">Category of the primary volume actor: &quot;Retail&quot; (individual trades) or &quot;Institutional&quot; (large block trades).</p>
            </div>
          </div>
        )}

        {difficulty === "medium" && (
          <div className="flex flex-col gap-4">
            {/* Warning Flags */}
            <div className="bg-error-container/20 border border-error/20 p-3 rounded-lg flex flex-col gap-1.5 mb-2">
              <div className="flex items-center gap-1.5 text-error font-semibold text-xs uppercase">
                <span className="material-symbols-outlined text-[16px]">error</span>
                Flagged Constraints
              </div>
              <ul className="list-disc pl-4 font-body-sm text-[11px] text-on-surface-variant flex flex-col gap-1">
                <li>2 entries have null values in column <code className="font-mono text-[10px] font-semibold bg-surface px-1">volume</code></li>
                <li>1 duplicate primary key index on column <code className="font-mono text-[10px] font-semibold bg-surface px-1">timestamp</code></li>
              </ul>
            </div>

            {/* Unannotated columns */}
            {["timestamp", "volume", "rsi", "type"].map((col) => (
              <div key={col} className="border border-outline-variant/30 rounded-xl p-3 bg-surface-container-low">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs font-bold text-primary">{col}</span>
                  <span className="font-label-sm text-[11px] text-outline font-semibold">
                    {col === "volume" || col === "rsi" ? "INTEGER" : "VARCHAR"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {difficulty === "hard" && (
          <div className="flex flex-col gap-4">
            {/* Hidden behind Auth Access */}
            {!schemaAccessRequested && (
              <div className="flex-1 flex flex-col items-center justify-center py-12 text-center gap-3">
                <span className="material-symbols-outlined text-[48px] text-outline-variant">lock_person</span>
                <div>
                  <h4 className="font-label-md text-label-md font-bold text-on-surface">Schema Encrypted</h4>
                  <p className="font-body-sm text-[11px] text-outline">Authorize credential token signature to unlock decrypted schema fields.</p>
                </div>
                <button
                  onClick={handleRequestSchema}
                  className="w-full mt-2 py-2 px-4 border border-outline text-on-surface font-label-md text-label-md rounded-lg hover:bg-surface-container transition-colors shadow-sm"
                >
                  Request Schema Access
                </button>
              </div>
            )}

            {loadingSchema && (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
                <span className="font-body-sm text-[11px] text-outline italic">Decrypting columns metadata...</span>
              </div>
            )}

            {schemaAccessApproved && (
              <>
                <div className="bg-error-container/20 border border-error/20 p-3 rounded-lg flex flex-col gap-1.5 mb-2">
                  <div className="flex items-center gap-1.5 text-error font-semibold text-xs uppercase">
                    <span className="material-symbols-outlined text-[16px]">gavel</span>
                    Unlabelled Constraints
                  </div>
                  <ul className="list-disc pl-4 font-mono text-[10px] text-on-surface-variant flex flex-col gap-1">
                    <li>ERR_CODE: 0x82f (Primary Key violation)</li>
                    <li>ERR_CODE: 0x09a (Cell Null violation)</li>
                  </ul>
                </div>

                {["timestamp", "volume", "rsi", "type"].map((col) => (
                  <div key={col} className="border border-outline-variant/30 rounded-xl p-3 bg-surface-container-low">
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-xs font-bold text-primary">{col}</span>
                      <span className="font-label-sm text-[11px] text-outline font-semibold">
                        {col === "volume" || col === "rsi" ? "INTEGER" : "VARCHAR"}
                      </span>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
