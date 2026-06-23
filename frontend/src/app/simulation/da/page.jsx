"use client";

import React, { useState, useEffect } from "react";
import DaHeader from "@/components/simulation/da/DaHeader";
import DaSidebar from "@/components/simulation/da/DaSidebar";
import DataExplorerTab from "@/components/simulation/da/DataExplorerTab";
import VisualizationsTab from "@/components/simulation/da/VisualizationsTab";
import InsightsTab from "@/components/simulation/da/InsightsTab";

// Static original raw dirty financial dataset
const originalDataset = [
  { timestamp: "2026-06-15", volume: 12500, rsi: 55, type: "Retail" },
  { timestamp: "2026-06-16", volume: 14200, rsi: 62, type: "Retail" },
  { timestamp: "2026-06-17", volume: null, rsi: 45, type: "Retail" }, // null volume
  { timestamp: "2026-06-18", volume: 32000, rsi: 78, type: "Institutional" }, // RSI breakout
  { timestamp: "2026-06-19", volume: 28000, rsi: 76, type: "Institutional" },
  { timestamp: "2026-06-19", volume: 28000, rsi: 76, type: "Institutional" }, // duplicate record
  { timestamp: "2026-06-20", volume: 11500, rsi: 38, type: "Retail" },
  { timestamp: "2026-06-21", volume: 45000, rsi: 82, type: "Institutional" }, // RSI breakout
  { timestamp: "2026-06-22", volume: null, rsi: 50, type: "Retail" }, // null volume
  { timestamp: "2026-06-23", volume: 49000, rsi: 88, type: "Institutional" } // RSI breakout
];

export default function DaSimulationPage() {
  const [difficulty, setDifficulty] = useState("medium");
  const [activeTab, setActiveTab] = useState("data");
  
  // Data states (lazy initializers to avoid hydration issues and sync effects)
  const [data, setData] = useState(() => JSON.parse(JSON.stringify(originalDataset)));
  const [isCleaned, setIsCleaned] = useState(false);
  const [insightsFound, setInsightsFound] = useState(0);

  // SEO page title update
  useEffect(() => {
    document.title = `Data Analyst Simulation (${difficulty.toUpperCase()}) | Career DNA AI`;
  }, [difficulty]);

  // Handle difficulty changes cleanly (callback instead of useEffect)
  const handleDifficultyChange = (newDifficulty) => {
    setDifficulty(newDifficulty);
    setData(JSON.parse(JSON.stringify(originalDataset)));
    setIsCleaned(false);
    setInsightsFound(0);
    setActiveTab("data"); // reset back to data tab
  };

  return (
    <div className="bg-surface text-on-surface font-body-md antialiased overflow-hidden flex h-screen w-screen relative">
      {/* 1. Header (HUD) - keyed by difficulty to reset inner timer */}
      <DaHeader 
        key={`header-${difficulty}`}
        difficulty={difficulty} 
        setDifficulty={handleDifficultyChange} 
        insightsFound={insightsFound} 
      />

      {/* 2. Collapsible Slack-Style Sidebar - keyed by difficulty to reset chat history */}
      <DaSidebar 
        key={`sidebar-${difficulty}`}
        difficulty={difficulty} 
      />

      {/* 3. Main Workspace */}
      <main className="flex-1 ml-[340px] md:ml-[360px] mt-20 flex flex-col h-[calc(100vh-80px)] bg-surface-container-lowest relative">
        {/* Workspace Sub-navigation Tabs */}
        <div className="px-gutter pt-4 border-b border-outline-variant bg-surface flex justify-between items-end relative z-10 shrink-0">
          <div className="flex gap-8">
            <button
              id="tab-data"
              onClick={() => setActiveTab("data")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "data"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Data Explorer
            </button>
            <button
              id="tab-visuals"
              onClick={() => setActiveTab("visuals")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "visuals"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Visualizations
            </button>
            <button
              id="tab-insights"
              onClick={() => setActiveTab("insights")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "insights"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Insights & Recommendation
            </button>
          </div>

          {/* Dynamic Guide Badge */}
          <div className="pb-3 flex items-center gap-2 text-outline font-label-sm text-label-sm">
            <span className="material-symbols-outlined text-[18px]">
              {difficulty === "hard" ? "psychology" : "lightbulb"}
            </span>
            <span>
              {difficulty === "easy" && "Guided mode · automated helpers active"}
              {difficulty === "medium" && "Semi-guided mode · hints active"}
              {difficulty === "hard" && "Expert mode · CLI active · auth checks required"}
            </span>
          </div>
        </div>

        {/* Tab View Container - keyed by difficulty so tabs reset cleanly */}
        <div key={`workspace-${difficulty}`} className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === "data" && (
            <DataExplorerTab
              difficulty={difficulty}
              data={data}
              setData={setData}
              isCleaned={isCleaned}
              setIsCleaned={setIsCleaned}
              originalData={originalDataset}
            />
          )}

          {activeTab === "visuals" && (
            <VisualizationsTab
              difficulty={difficulty}
              data={data}
              isCleaned={isCleaned}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === "insights" && (
            <InsightsTab
              difficulty={difficulty}
              insightsFound={insightsFound}
              setInsightsFound={setInsightsFound}
            />
          )}
        </div>
      </main>
    </div>
  );
}
