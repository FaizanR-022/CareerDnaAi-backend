"use client";

import React, { useState, useEffect } from "react";
import SimulationHeader from "@/components/simulation/SimulationHeader";
import CommunicationsSidebar from "@/components/simulation/CommunicationsSidebar";
import MoscowBoard from "@/components/simulation/MoscowBoard";
import PrdDocument from "@/components/simulation/PrdDocument";
import EventToast from "@/components/simulation/EventToast";

export default function PmSimulationPage() {
  const [difficulty, setDifficulty] = useState("medium");
  const [activeTab, setActiveTab] = useState("moscow");
  const [showToast, setShowToast] = useState(true);
  const [toastFeedback, setToastFeedback] = useState(null);

  // SEO: Update page title dynamically on the client
  useEffect(() => {
    document.title = `PM Simulation (${difficulty.toUpperCase()}) | Career DNA AI`;
  }, [difficulty]);

  return (
    <div className="bg-surface text-on-surface font-body-md antialiased overflow-hidden flex h-screen w-screen relative">
      {/* 1. Header (HUD) */}
      <SimulationHeader difficulty={difficulty} setDifficulty={setDifficulty} />

      {/* 2. Left Sidebar (Communications Hub) */}
      <CommunicationsSidebar difficulty={difficulty} />

      {/* 3. Main Content Workspace */}
      <main className="flex-1 ml-[340px] md:ml-[360px] mt-20 flex flex-col h-[calc(100vh-80px)] bg-surface-container-lowest relative">
        {/* Workspace Sub-navigation Tabs */}
        <div className="px-gutter pt-4 border-b border-outline-variant bg-surface flex justify-between items-end relative z-10 shrink-0">
          <div className="flex gap-8">
            <button
              id="tab-moscow"
              onClick={() => setActiveTab("moscow")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "moscow"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              MoSCoW Board
            </button>
            <button
              id="tab-prd"
              onClick={() => setActiveTab("prd")}
              className={`pb-2 font-label-md text-label-md transition-colors px-2 border-b-2 font-semibold ${
                activeTab === "prd"
                  ? "text-primary border-primary"
                  : "text-on-surface-variant border-transparent hover:text-primary hover:border-primary/45"
              }`}
            >
              PRD Document
            </button>
          </div>

          {/* Guide / Hint Badge on Right */}
          <div className="pb-3 flex items-center gap-2 text-outline font-label-sm text-label-sm">
            <span className="material-symbols-outlined text-[18px]">
              {difficulty === "hard" ? "psychology" : "lightbulb"}
            </span>
            <span>
              {difficulty === "easy" && "Guided mode · hints available"}
              {difficulty === "medium" && "Semi-guided mode · hints available"}
              {difficulty === "hard" && "Expert mode · no hints"}
            </span>
          </div>
        </div>

        {/* Tab View Container */}
        <div className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === "moscow" ? (
            <MoscowBoard difficulty={difficulty} />
          ) : (
            <PrdDocument difficulty={difficulty} />
          )}
        </div>

        {/* 4. Event Toast Notification */}
        <EventToast
          showToast={showToast}
          setShowToast={setShowToast}
          toastFeedback={toastFeedback}
          setToastFeedback={setToastFeedback}
        />
      </main>
    </div>
  );
}
