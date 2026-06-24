"use client";

import React, { useState, useEffect } from "react";
import FeHeader from "@/components/simulation/fe/FeHeader";
import FeSidebar from "@/components/simulation/fe/FeSidebar";
import DesignReviewTab from "@/components/simulation/fe/DesignReviewTab";
import WireframeTab from "@/components/simulation/fe/WireframeTab";
import CodeSandboxTab from "@/components/simulation/fe/CodeSandboxTab";

export default function FeSimulationPage() {
  const [difficulty, setDifficulty] = useState("medium");
  const [activeTab, setActiveTab] = useState("design");

  // Initial a11y score based on difficulty
  const getInitialA11yScore = (diff) => {
    if (diff === "easy") return 98;
    if (diff === "medium") return 70;
    return 50;
  };

  const [a11yScore, setA11yScore] = useState(() => getInitialA11yScore("medium"));
  const [responsiveScore, setResponsiveScore] = useState("0/3 Breakpoints");

  // Update document title for SEO
  useEffect(() => {
    document.title = `Frontend Engineer Simulation (${difficulty.toUpperCase()}) | Career DNA AI`;
  }, [difficulty]);

  // Handle difficulty changes cleanly to prevent memory leaks / state desync
  const handleDifficultyChange = (newDifficulty) => {
    setDifficulty(newDifficulty);
    setA11yScore(getInitialA11yScore(newDifficulty));
    setResponsiveScore("0/3 Breakpoints");
    setActiveTab("design");
  };

  return (
    <div className="bg-surface text-on-surface font-body-md antialiased overflow-hidden flex h-screen w-screen relative">
      {/* 1. Header (HUD) - keyed by difficulty to reset inner timer */}
      <FeHeader
        key={`header-${difficulty}`}
        difficulty={difficulty}
        setDifficulty={handleDifficultyChange}
        a11yScore={a11yScore}
        responsiveScore={responsiveScore}
      />

      {/* 2. Collapsible Slack-Style Sidebar - keyed by difficulty to reset chat history */}
      <FeSidebar
        key={`sidebar-${difficulty}`}
        difficulty={difficulty}
      />

      {/* 3. Main Workspace */}
      <main className="flex-1 ml-[340px] md:ml-[360px] mt-20 flex flex-col h-[calc(100vh-80px)] bg-surface-container-lowest relative">
        {/* Workspace Sub-navigation Tabs */}
        <div className="px-gutter pt-4 border-b border-outline-variant bg-surface flex justify-between items-end relative z-10 shrink-0">
          <div className="flex gap-8">
            <button
              id="tab-design"
              onClick={() => setActiveTab("design")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "design"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Design Review
            </button>
            <button
              id="tab-wireframe"
              onClick={() => setActiveTab("wireframe")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "wireframe"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              Wireframe Builder
            </button>
            <button
              id="tab-sandbox"
              onClick={() => setActiveTab("sandbox")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "sandbox"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              CSS Sandbox
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
              {difficulty === "hard" && "Expert mode · CLI active · constraints warnings active"}
            </span>
          </div>
        </div>

        {/* Tab View Container - keyed by difficulty so tabs reset cleanly */}
        <div key={`workspace-${difficulty}`} className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === "design" && (
            <DesignReviewTab
              difficulty={difficulty}
              a11yScore={a11yScore}
              setA11yScore={setA11yScore}
            />
          )}

          {activeTab === "wireframe" && (
            <WireframeTab
              difficulty={difficulty}
              responsiveScore={responsiveScore}
              setResponsiveScore={setResponsiveScore}
            />
          )}

          {activeTab === "sandbox" && (
            <CodeSandboxTab
              difficulty={difficulty}
              responsiveScore={responsiveScore}
              setResponsiveScore={setResponsiveScore}
            />
          )}
        </div>
      </main>
    </div>
  );
}
