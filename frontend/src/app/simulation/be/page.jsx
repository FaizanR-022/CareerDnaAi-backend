"use client";

import React, { useState, useEffect } from "react";
import BeHeader from "@/components/simulation/be/BeHeader";
import BeSidebar from "@/components/simulation/be/BeSidebar";
import ApiTab from "@/components/simulation/be/ApiTab";
import DatabaseTab from "@/components/simulation/be/DatabaseTab";
import ArchitectureTab from "@/components/simulation/be/ArchitectureTab";

export default function BeSimulationPage() {
  const [difficulty, setDifficulty] = useState("medium");
  const [activeTab, setActiveTab] = useState("api");

  // Latency adjusts dynamically based on difficulty
  const getLatency = (diff) => {
    return diff === "hard" ? "850ms" : "45ms";
  };

  const [apiLatency, setApiLatency] = useState(() => getLatency("medium"));

  // Update SEO Document title
  useEffect(() => {
    document.title = `Backend Engineer Simulation (${difficulty.toUpperCase()}) | Career DNA AI`;
  }, [difficulty]);

  // Handle difficulty changes cleanly (resets tabs and latency states)
  const handleDifficultyChange = (newDifficulty) => {
    setDifficulty(newDifficulty);
    setApiLatency(getLatency(newDifficulty));
    setActiveTab("api");
  };

  return (
    <div className="bg-surface text-on-surface font-body-md antialiased overflow-hidden flex h-screen w-screen relative">
      {/* 1. Header (HUD) - keyed by difficulty to reset timer */}
      <BeHeader
        key={`header-${difficulty}`}
        difficulty={difficulty}
        setDifficulty={handleDifficultyChange}
        systemUptime="99.99%"
        apiLatency={apiLatency}
      />

      {/* 2. Collapsible Slack-Style Sidebar - keyed by difficulty to reset chat thread */}
      <BeSidebar
        key={`sidebar-${difficulty}`}
        difficulty={difficulty}
      />

      {/* 3. Main Workspace */}
      <main className="flex-1 ml-[340px] md:ml-[360px] mt-20 flex flex-col h-[calc(100vh-80px)] bg-surface-container-lowest relative">
        {/* Workspace Sub-navigation Tabs */}
        <div className="px-gutter pt-4 border-b border-outline-variant bg-surface flex justify-between items-end relative z-10 shrink-0">
          <div className="flex gap-8">
            <button
              id="tab-api"
              onClick={() => setActiveTab("api")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "api"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              API Design
            </button>
            <button
              id="tab-database"
              onClick={() => setActiveTab("database")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "database"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              SQL Database
            </button>
            <button
              id="tab-architecture"
              onClick={() => setActiveTab("architecture")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "architecture"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              System Architecture
            </button>
          </div>

          {/* Dynamic Guide Badge */}
          <div className="pb-3 flex items-center gap-2 text-outline font-label-sm text-label-sm">
            <span className="material-symbols-outlined text-[18px]">
              {difficulty === "hard" ? "psychology" : "lightbulb"}
            </span>
            <span>
              {difficulty === "easy" && "Guided mode · inline indicators active"}
              {difficulty === "medium" && "Semi-guided mode · request hints active"}
              {difficulty === "hard" && "Expert mode · console traces active · silent errors"}
            </span>
          </div>
        </div>

        {/* Tab View Container - keyed by difficulty so tabs reset cleanly */}
        <div key={`workspace-${difficulty}`} className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === "api" && (
            <ApiTab
              difficulty={difficulty}
              apiLatency={apiLatency}
              setApiLatency={setApiLatency}
            />
          )}

          {activeTab === "database" && (
            <DatabaseTab
              difficulty={difficulty}
            />
          )}

          {activeTab === "architecture" && (
            <ArchitectureTab
              difficulty={difficulty}
            />
          )}
        </div>
      </main>
    </div>
  );
}
