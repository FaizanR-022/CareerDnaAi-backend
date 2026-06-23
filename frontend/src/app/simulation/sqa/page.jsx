"use client";

import React, { useState, useEffect } from "react";
import SqaHeader from "@/components/simulation/sqa/SqaHeader";
import SqaSidebar from "@/components/simulation/sqa/SqaSidebar";
import SpecsTab from "@/components/simulation/sqa/SpecsTab";
import TestExecutionTab from "@/components/simulation/sqa/TestExecutionTab";
import BugReportingTab from "@/components/simulation/sqa/BugReportingTab";

export default function SqaSimulationPage() {
  const [difficulty, setDifficulty] = useState("medium");
  const [activeTab, setActiveTab] = useState("specs");

  // Shared SQA simulation states
  const [bugsFound, setBugsFound] = useState(0);
  const [testCoverage, setTestCoverage] = useState(40);

  // Update HTML Document Title dynamically
  useEffect(() => {
    document.title = `SQA Simulation (${difficulty.toUpperCase()}) | Career DNA AI`;
  }, [difficulty]);

  // Clean state reset when difficulty levels are switched
  const handleDifficultyChange = (newDifficulty) => {
    setDifficulty(newDifficulty);
    setBugsFound(0);
    setTestCoverage(newDifficulty === "easy" ? 60 : 40); // Easy starts with a guided baseline coverage
    setActiveTab("specs"); // reset to starting tab
  };

  return (
    <div className="bg-surface text-on-surface font-body-md antialiased overflow-hidden flex h-screen w-screen relative">
      {/* 1. Header (HUD) - keyed by difficulty to reset timers cleanly */}
      <SqaHeader 
        key={`header-${difficulty}`}
        difficulty={difficulty} 
        setDifficulty={handleDifficultyChange} 
        bugsFound={bugsFound}
        testCoverage={testCoverage}
      />

      {/* 2. Collapsible Slack-Style Sidebar - keyed by difficulty to reset chat logs */}
      <SqaSidebar 
        key={`sidebar-${difficulty}`}
        difficulty={difficulty} 
      />

      {/* 3. Main content workspace */}
      <main className="flex-1 ml-[340px] md:ml-[360px] mt-20 flex flex-col h-[calc(100vh-80px)] bg-surface-container-lowest relative">
        {/* Sub-navigation Tabs */}
        <div className="px-gutter pt-4 border-b border-outline-variant bg-surface flex justify-between items-end relative z-10 shrink-0">
          <div className="flex gap-8">
            <button
              id="tab-specs"
              onClick={() => setActiveTab("specs")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "specs"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Specs Analysis
            </button>
            <button
              id="tab-execution"
              onClick={() => setActiveTab("execution")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "execution"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Test Execution
            </button>
            <button
              id="tab-reporting"
              onClick={() => setActiveTab("reporting")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "reporting"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Bug Triage
            </button>
          </div>

          {/* Guide badge */}
          <div className="pb-3 flex items-center gap-2 text-outline font-label-sm text-label-sm">
            <span className="material-symbols-outlined text-[18px]">
              {difficulty === "hard" ? "psychology" : "lightbulb"}
            </span>
            <span>
              {difficulty === "easy" && "Guided mode · highlights active"}
              {difficulty === "medium" && "Semi-guided mode · dev console open"}
              {difficulty === "hard" && "Expert mode · black-box testing active"}
            </span>
          </div>
        </div>

        {/* Workspace Tab View Container */}
        <div key={`workspace-${difficulty}`} className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === "specs" && (
            <SpecsTab
              difficulty={difficulty}
              testCoverage={testCoverage}
              setTestCoverage={setTestCoverage}
            />
          )}

          {activeTab === "execution" && (
            <TestExecutionTab
              difficulty={difficulty}
              bugsFound={bugsFound}
              setBugsFound={setBugsFound}
              testCoverage={testCoverage}
              setTestCoverage={setTestCoverage}
            />
          )}

          {activeTab === "reporting" && (
            <BugReportingTab
              difficulty={difficulty}
              bugsFound={bugsFound}
              setBugsFound={setBugsFound}
              testCoverage={testCoverage}
              setTestCoverage={setTestCoverage}
            />
          )}
        </div>
      </main>
    </div>
  );
}
