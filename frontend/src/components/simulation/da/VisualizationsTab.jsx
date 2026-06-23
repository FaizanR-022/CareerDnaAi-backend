"use client";

import React, { useState } from "react";

export default function VisualizationsTab({ difficulty, data, isCleaned, setActiveTab }) {
  const [chartType, setChartType] = useState("line");
  const [yAxisField, setYAxisField] = useState("volume");
  const [selectedPoint, setSelectedPoint] = useState(null);

  // Medium/Hard specific states
  const [codeMode, setCodeMode] = useState("sql"); // "sql" or "python"
  const [codeText, setCodeText] = useState("-- Type SELECT timestamp, volume FROM data...");
  const [queryError, setQueryError] = useState(null);
  const [querySuccess, setQuerySuccess] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState([]);

  // Code/Query suggestions for click-to-insert (Drag-and-Drop alternative)
  const sqlTokens = [
    "SELECT timestamp, volume",
    "SELECT timestamp, rsi",
    "FROM transaction_log",
    "ORDER BY timestamp ASC",
  ];

  const pythonTokens = [
    "df.plot(x='timestamp', y='volume')",
    "df.plot(x='timestamp', y='rsi')",
    "print(df.describe())",
  ];

  const handleTokenClick = (token) => {
    setCodeText((prev) => {
      const cleanPrev = prev.startsWith("--") || prev.startsWith("#") ? "" : prev;
      return `${cleanPrev} ${token}`.trim();
    });
  };

  const handleRunQuery = (e) => {
    if (e) e.preventDefault();
    setQueryError(null);
    setQuerySuccess(false);

    const code = codeText.trim().toLowerCase();
    const newLogs = [`Running ${codeMode.toUpperCase()} query...`];

    // Simple validation: Needs fields timestamp and volume/rsi to compile successfully
    if (codeMode === "sql") {
      if (
        (code.includes("select") && code.includes("timestamp") && code.includes("volume")) ||
        (code.includes("select") && code.includes("timestamp") && code.includes("rsi"))
      ) {
        newLogs.push("Parsing syntax tree... OK");
        newLogs.push(`Accessing transaction_log partition: 8 rows scanned.`);
        newLogs.push(`Query complete. Rendering visualization...`);
        setTerminalLogs((prev) => [...prev, ...newLogs]);
        setQuerySuccess(true);
        // Determine Y Axis based on code query
        if (code.includes("rsi")) {
          setYAxisField("rsi");
        } else {
          setYAxisField("volume");
        }
      } else {
        setQueryError("SQL Error: column specifier missing. Make sure to SELECT timestamp and volume/rsi.");
        newLogs.push("ERROR: Query failed compilation.");
        setTerminalLogs((prev) => [...prev, ...newLogs]);
      }
    } else {
      // Python Mode
      if (code.includes("df.plot") && code.includes("timestamp") && (code.includes("volume") || code.includes("rsi"))) {
        newLogs.push("Python interpreter: loading pandas... OK");
        newLogs.push("DataFrame loaded: Shape (8, 4)");
        newLogs.push("Matplotlib: drawing axes... OK");
        setTerminalLogs((prev) => [...prev, ...newLogs]);
        setQuerySuccess(true);
        if (code.includes("rsi")) {
          setYAxisField("rsi");
        } else {
          setYAxisField("volume");
        }
      } else {
        setQueryError("SyntaxError: Invalid pandas plotting call. Try: df.plot(x='timestamp', y='volume')");
        newLogs.push("ERROR: Python script crashed with code 1.");
        setTerminalLogs((prev) => [...prev, ...newLogs]);
      }
    }
  };

  // Prevent visualization if data is dirty
  if (!isCleaned) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-surface-container-lowest p-8 text-center">
        <div className="max-w-md bg-surface border border-outline-variant/30 p-8 rounded-2xl shadow-xl flex flex-col items-center gap-4 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-error"></div>
          <div className="w-16 h-16 rounded-full bg-error-container/30 flex items-center justify-center text-error mb-2">
            <span className="material-symbols-outlined text-[36px]">database_off</span>
          </div>
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Data Integrity Unverified</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed">
            The visualization layer is blocked because the financial transaction log contains null values and duplicate timestamps. Running aggregations on raw anomalies will produce corrupted statistics.
          </p>
          <button
            onClick={() => setActiveTab("data")}
            className="mt-4 py-2.5 px-6 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container transition-colors"
          >
            Go to Data Explorer & Clean
          </button>
        </div>
      </div>
    );
  }

  // Draw chart computations
  const chartHeight = 240;
  const chartWidth = 540;
  const padding = 40;

  const getPoints = () => {
    // Sort data by timestamp to ensure path is correct chronologically
    const sorted = [...data].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Find min/max values
    const values = sorted.map(row => row[yAxisField]);
    const maxVal = Math.max(...values, 100);
    const minVal = Math.min(...values, 0);
    const range = maxVal - minVal;

    const points = sorted.map((row, index) => {
      const x = padding + (index / (sorted.length - 1)) * (chartWidth - padding * 2);
      const val = row[yAxisField] || 0;
      // invert Y coordinate for SVG
      const y = chartHeight - padding - ((val - minVal) / range) * (chartHeight - padding * 2);
      return { x, y, val, timestamp: row.timestamp, type: row.type };
    });

    return points;
  };

  const points = getPoints();
  
  // Build SVG Path
  const linePath = points.reduce((path, pt, i) => {
    return i === 0 ? `M ${pt.x} ${pt.y}` : `${path} L ${pt.x} ${pt.y}`;
  }, "");

  // Build Area Path for smooth gradient fill
  const areaPath = points.length > 0 
    ? `${linePath} L ${points[points.length - 1].x} ${chartHeight - padding} L ${points[0].x} ${chartHeight - padding} Z` 
    : "";

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: CHART OR INTERACTIVE CODE Terminal */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header description */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Trend Charting Engine</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Analyze volume breakouts and RSI momentum divergence.</p>
        </div>

        {/* Medium/Hard Mode: Requires writing query/code to compile chart */}
        {difficulty !== "easy" && !querySuccess ? (
          <div className="flex-1 flex flex-col gap-4">
            <div className="bg-surface-container border border-outline-variant/30 rounded-xl p-5 shadow-sm">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-label-md text-label-md font-bold text-on-surface flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[20px] text-primary">terminal</span>
                  Query Execution Editor
                </h3>
                
                {/* Console tabs */}
                <div className="flex bg-surface rounded-lg p-0.5 border border-outline-variant/20">
                  <button
                    onClick={() => {
                      setCodeMode("sql");
                      setCodeText("-- Type SELECT timestamp, volume FROM data...");
                    }}
                    className={`px-3 py-1 text-xs font-semibold rounded ${codeMode === "sql" ? "bg-primary text-white" : "text-outline hover:text-on-surface"}`}
                  >
                    SQL Console
                  </button>
                  <button
                    onClick={() => {
                      setCodeMode("python");
                      setCodeText("# Type df.plot(x='timestamp', y='volume')...");
                    }}
                    className={`px-3 py-1 text-xs font-semibold rounded ${codeMode === "python" ? "bg-primary text-white" : "text-outline hover:text-on-surface"}`}
                  >
                    Python Sandbox
                  </button>
                </div>
              </div>

              {/* Code TextArea */}
              <div className="flex flex-col gap-2 bg-inverse-surface rounded-xl p-4 text-white font-mono text-[13px] shadow-inner">
                <textarea
                  value={codeText}
                  onChange={(e) => setCodeText(e.target.value)}
                  className="w-full h-32 bg-transparent text-green-400 border-none outline-none focus:ring-0 resize-none font-mono scrollbar-thin"
                />
                
                {/* Clickable drag/drop tokens */}
                <div className="border-t border-white/10 pt-3 flex flex-col gap-2">
                  <span className="text-[10px] text-surface-variant uppercase tracking-wider font-semibold">Helper Snippet Tokens:</span>
                  <div className="flex flex-wrap gap-2">
                    {(codeMode === "sql" ? sqlTokens : pythonTokens).map((token) => (
                      <button
                        key={token}
                        onClick={() => handleTokenClick(token)}
                        className="py-1 px-2.5 bg-white/5 border border-white/10 rounded-md text-[11px] text-inverse-primary hover:bg-white/10 hover:border-primary-container transition-all"
                      >
                        {token}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center mt-4">
                <span className="font-body-sm text-[11px] text-outline italic">Compile code to render the animated chart workspace.</span>
                <button
                  onClick={handleRunQuery}
                  className="py-2.5 px-6 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container active:scale-[0.98] transition-all"
                >
                  Run Query Code
                </button>
              </div>

              {/* Error messages */}
              {queryError && (
                <div className="mt-4 bg-error-container/20 border border-error/30 text-error p-3 rounded-lg font-mono text-xs flex gap-2 items-center">
                  <span className="material-symbols-outlined text-[16px]">error</span>
                  {queryError}
                </div>
              )}
            </div>

            {/* Run logs console */}
            <div className="h-32 bg-black border border-white/10 rounded-xl p-3 font-mono text-[10px] text-white/70 overflow-y-auto scrollbar-thin flex flex-col gap-1">
              <div className="text-surface-variant">{"// Console standard output logs:"}</div>
              {terminalLogs.map((log, i) => (
                <div key={i} className={log.startsWith("ERROR") ? "text-error" : log.includes("Rendering") ? "text-green-400" : "text-white/80"}>
                  {log}
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Render visualization */
          <div className="flex-1 flex flex-col gap-6">
            
            {/* Compile Success Notification (if applicable) */}
            {difficulty !== "easy" && (
              <div className="bg-primary/5 border border-primary/20 p-3 rounded-lg flex items-center justify-between text-primary font-semibold text-xs">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>
                  Compilation Success: Query successfully resolved to dataset array.
                </div>
                <button 
                  onClick={() => setQuerySuccess(false)}
                  className="text-xs hover:underline text-outline"
                >
                  Reset Query Editor
                </button>
              </div>
            )}

            {/* Selection bar for Easy difficulty */}
            {difficulty === "easy" && (
              <div className="grid grid-cols-3 gap-4 bg-surface border border-outline-variant/30 p-4 rounded-xl shadow-sm">
                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[12px] text-outline font-semibold">Chart Format</label>
                  <select
                    value={chartType}
                    onChange={(e) => setChartType(e.target.value)}
                    className="bg-surface-container-low border border-outline-variant rounded-lg p-2 font-body-sm text-[13px] focus:outline-none"
                  >
                    <option value="line">Line Chart</option>
                    <option value="bar">Bar Chart</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[12px] text-outline font-semibold">X-Axis</label>
                  <select disabled className="bg-surface-container-low border border-outline-variant rounded-lg p-2 font-body-sm text-[13px] cursor-not-allowed opacity-75">
                    <option>timestamp</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="font-label-sm text-[12px] text-outline font-semibold">Y-Axis Metric</label>
                  <select
                    value={yAxisField}
                    onChange={(e) => setYAxisField(e.target.value)}
                    className="bg-surface-container-low border border-outline-variant rounded-lg p-2 font-body-sm text-[13px] focus:outline-none"
                  >
                    <option value="volume">volume (Trading Volume)</option>
                    <option value="rsi">rsi (Momentum Index)</option>
                  </select>
                </div>
              </div>
            )}

            {/* CHART RENDER CONTAINER */}
            <div className="bg-surface border border-outline-variant/20 rounded-2xl p-6 shadow-sm flex flex-col items-center">
              <div className="w-full flex justify-between items-center mb-4">
                <span className="font-label-md text-xs font-bold text-outline uppercase tracking-wider">
                  Y-Metric: <span className="text-primary font-mono lowercase">{yAxisField}</span>
                </span>
                {selectedPoint && (
                  <span className="font-mono text-xs bg-primary-fixed text-on-primary-fixed px-3 py-1 rounded-full font-semibold animate-fade-in">
                    {selectedPoint.timestamp} : {selectedPoint.val.toLocaleString()} ({selectedPoint.type})
                  </span>
                )}
              </div>

              {/* Render Animated SVG Chart */}
              <div className="w-full max-w-[540px] h-[240px] relative bg-surface-container-lowest rounded-xl border border-outline-variant/10 overflow-hidden">
                <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-full">
                  {/* Grid Lines */}
                  {[0.25, 0.5, 0.75].map((ratio, i) => (
                    <line
                      key={i}
                      x1={padding}
                      y1={padding + ratio * (chartHeight - padding * 2)}
                      x2={chartWidth - padding}
                      y2={padding + ratio * (chartHeight - padding * 2)}
                      stroke="#e2e8f0"
                      strokeDasharray="4 4"
                    />
                  ))}

                  {/* Gradient definition for Line fill */}
                  <defs>
                    <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4648d4" stopOpacity="0.4" />
                      <stop offset="100%" stopColor="#4648d4" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>

                  {/* Chart lines/bars */}
                  {chartType === "line" ? (
                    <>
                      {/* Gradient Area Fill */}
                      <path d={areaPath} fill="url(#chartGradient)" />
                      {/* Line Path */}
                      <path
                        d={linePath}
                        fill="none"
                        stroke="#4648d4"
                        strokeWidth="3.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="animate-draw-path"
                        style={{
                          strokeDasharray: 1000,
                          strokeDashoffset: 0,
                        }}
                      />
                    </>
                  ) : (
                    /* Bar Chart rendering */
                    points.map((pt, i) => {
                      const barWidth = 24;
                      const barHeight = chartHeight - padding - pt.y;
                      return (
                        <rect
                          key={i}
                          x={pt.x - barWidth / 2}
                          y={pt.y}
                          width={barWidth}
                          height={Math.max(barHeight, 2)}
                          fill={pt.type === "Institutional" ? "#6063ee" : "#c7c4d7"}
                          rx="3"
                          className="transition-all duration-300 hover:fill-primary"
                          onMouseEnter={() => setSelectedPoint(pt)}
                          onMouseLeave={() => setSelectedPoint(null)}
                        />
                      );
                    })
                  )}

                  {/* Nodes & Hover circles for Line Chart */}
                  {chartType === "line" && points.map((pt, i) => (
                    <g key={i}>
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r="5"
                        fill={pt.type === "Institutional" ? "#4648d4" : "#ffffff"}
                        stroke="#4648d4"
                        strokeWidth="2.5"
                        className="cursor-pointer transition-all duration-150 hover:r-7"
                        onMouseEnter={() => setSelectedPoint(pt)}
                        onMouseLeave={() => setSelectedPoint(null)}
                      />
                    </g>
                  ))}
                </svg>
              </div>

              {/* Chart Legend */}
              <div className="flex gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded bg-primary-container"></span>
                  <span className="font-body-sm text-[12px] text-outline font-semibold">Institutional Trading</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded bg-outline-variant"></span>
                  <span className="font-body-sm text-[12px] text-outline font-semibold">Retail Volume</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT PANEL: ANOMALY GUIDE */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">analytics</span>
          Anomaly Guide
        </h3>

        <div className="flex flex-col gap-4">
          <div className="bg-primary-fixed border border-primary-fixed-dim p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-primary-fixed mb-1 uppercase tracking-wider">Institutional Divergence</h4>
            <p className="font-body-sm text-[11px] text-on-primary-fixed-variant leading-relaxed">
              Institutional spikes represent block orders. Look closely at dates where Volume surges but RSI triggers a sharp decline—this implies institutional players are dumping assets.
            </p>
          </div>

          <div className="bg-surface-container border border-outline-variant/20 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">RSI Momentum Thresholds</h4>
            <p className="font-body-sm text-[11px] text-on-surface-variant leading-relaxed">
              - **&gt; 70**: Overbought asset index. Imminent sell-off potential.<br />
              - **&lt; 30**: Oversold asset index. Bounce back signals.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
