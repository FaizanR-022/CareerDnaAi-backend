"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function OnboardingPage() {
  const router = useRouter();

  // Stateful onboarding steps: 1 (Path Selection), 2 (Initialization Dashboard)
  const [step, setStep] = useState(1);
  const [selectedPath, setSelectedPath] = useState(null);

  // Guidelines panel display toggle
  const [showGuidelines, setShowGuidelines] = useState(false);

  // Handle path selection trigger
  const handlePathSelect = (path) => {
    setSelectedPath(path);
  };

  // Launch baseline simulation checks
  const handleStartSimulation = () => {
    if (!selectedPath) return;

    if (selectedPath === "pm" || selectedPath === "da" || selectedPath === "sqa" || selectedPath === "fe") {
      router.push(`/simulation/${selectedPath}`);
    } else {
      alert(`The simulation for ${selectedPath.toUpperCase()} is queued. Redirecting to Product Manager baseline sandbox.`);
      router.push("/simulation/pm");
    }
  };

  // Roles list configuration for Step 1
  const roles = [
    {
      id: "pm",
      title: "Product Manager",
      icon: "target",
      desc: "Lead vision, strategy, and execution. Bridge users, business, and engineering team needs.",
      skills: ["Synthesis", "Strategy"],
      skillColors: ["bg-primary-container text-on-primary-container", "bg-tertiary-container text-on-tertiary-container"]
    },
    {
      id: "fe",
      title: "Frontend Dev",
      icon: "web",
      desc: "Craft fast, beautiful client-side web apps. Translate layouts into accessible UX.",
      skills: ["UX Design", "Logic"],
      skillColors: ["bg-secondary-container text-on-secondary-container", "bg-primary-container text-on-primary-container"]
    },
    {
      id: "be",
      title: "Backend Dev",
      icon: "dns",
      desc: "Build scalable system engines behind the scene. Design databases, queues, and APIs.",
      skills: ["Architecture", "Logic"],
      skillColors: ["bg-tertiary-container text-on-tertiary-container", "bg-primary-container text-on-primary-container"]
    },
    {
      id: "da",
      title: "Data Analyst",
      icon: "bar_chart",
      desc: "Decode logs into clear insights. Drive stakeholder direction using metrics and statistics.",
      skills: ["Analysis", "Synthesis"],
      skillColors: ["bg-secondary-container text-on-secondary-container", "bg-tertiary-container text-on-tertiary-container"]
    },
    {
      id: "sqa",
      title: "SQA Engineer",
      icon: "verified_user",
      desc: "Guard build quality. Formulate test plans, automate workflows, and catch logic conflicts.",
      skills: ["Analysis", "Detail"],
      skillColors: ["bg-primary-container text-on-primary-container", "bg-secondary-container text-on-secondary-container"]
    }
  ];

  return (
    <div className="bg-surface text-on-surface min-h-screen w-screen flex flex-col font-body-md antialiased transition-all duration-500 ease-in-out">
      
      {/* STEP 1: PATH SELECTION PANEL */}
      {step === 1 && (
        <div className="flex-1 flex flex-col justify-between p-6 md:p-8 animate-fade-in">
          
          {/* Step 1 Header */}
          <header className="flex justify-between items-center w-full mb-8">
            <div className="flex items-center gap-2 group cursor-pointer" onClick={() => router.push("/")}>
              <div className="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-xl">genetics</span>
              </div>
              <div className="font-headline-md text-[20px] font-bold tracking-tight">
                Career<span className="text-primary ml-0.5">DNA</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="font-label-sm text-xs font-bold text-outline uppercase tracking-wider">
                Step 01 / 03
              </span>
              <div className="w-24 h-1.5 bg-surface-container-high rounded-full overflow-hidden">
                <div className="h-full bg-primary w-1/3" />
              </div>
            </div>
          </header>

          {/* Titles */}
          <div className="text-center max-w-2xl mx-auto mb-10 flex flex-col gap-2.5">
            <h2 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight">
              Which professional path would you like to explore first?
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Select a tech domain below to calibrate your baseline cognitive assessment.
              You can explore other roles after completing this baseline.
            </p>
          </div>

          {/* Selection Grid */}
          <div className="max-w-container-max mx-auto w-full grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-5 mb-10">
            {roles.map((role) => {
              const isActive = selectedPath === role.id;
              return (
                <div
                  key={role.id}
                  onClick={() => handlePathSelect(role.id)}
                  className={`bg-surface border rounded-2xl p-5 cursor-pointer shadow-sm flex flex-col justify-between hover:shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 ${
                    isActive 
                      ? "ring-2 ring-primary border-primary bg-primary/5" 
                      : "border-outline-variant/35 hover:border-outline-variant"
                  }`}
                >
                  <div>
                    {/* Icon */}
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 transition-colors ${
                      isActive ? "bg-primary text-white" : "bg-surface-container-high text-on-surface"
                    }`}>
                      <span className="material-symbols-outlined text-[20px]">{role.icon}</span>
                    </div>
                    
                    {/* Info */}
                    <h3 className="font-label-md text-label-md font-bold text-on-surface mb-2">{role.title}</h3>
                    <p className="font-body-sm text-[12px] text-on-surface-variant leading-relaxed mb-4">
                      {role.desc}
                    </p>
                  </div>

                  {/* Badges section */}
                  <div className="border-t border-outline-variant/10 pt-3 mt-2">
                    <span className="font-label-sm text-[9px] text-outline font-bold uppercase tracking-wider block mb-2">Core Cognitive Skills</span>
                    <div className="flex gap-1.5 flex-wrap">
                      {role.skills.map((skill, idx) => (
                        <span 
                          key={skill}
                          className={`px-2 py-0.5 rounded text-[9px] font-semibold tracking-wide ${role.skillColors[idx]}`}
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer Action */}
          <div className="flex justify-end pt-4 border-t border-outline-variant/20 max-w-container-max mx-auto w-full">
            <button
              disabled={!selectedPath}
              onClick={() => setStep(2)}
              className="py-3 px-8 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/40 disabled:cursor-not-allowed disabled:shadow-none hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center gap-2 font-semibold"
            >
              Continue to Interests
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: INITIALIZATION DASHBOARD PANEL */}
      {step === 2 && (
        <div className="flex-1 flex flex-col justify-between p-6 md:p-8 animate-fade-in bg-surface-container-lowest">
          
          {/* Step 2 Header */}
          <header className="flex flex-col items-center w-full mb-8">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-xl">genetics</span>
              </div>
              <div className="font-headline-md text-[20px] font-bold tracking-tight">
                Career<span className="text-primary ml-0.5">DNA</span>
              </div>
            </div>

            {/* Step Indicators (1, 2, 3) where 2 is highlighted black */}
            <div className="flex items-center gap-2 select-none">
              <div className="w-7 h-7 rounded-full bg-primary/10 text-primary font-semibold text-xs flex items-center justify-center">
                <span className="material-symbols-outlined text-[14px]">check</span>
              </div>
              <div className="w-8 h-0.5 bg-primary/20"></div>
              <div className="w-7 h-7 rounded-full bg-black text-white font-bold text-xs flex items-center justify-center shadow-sm">
                2
              </div>
              <div className="w-8 h-0.5 bg-outline-variant/40"></div>
              <div className="w-7 h-7 rounded-full bg-surface-container-high text-outline font-semibold text-xs flex items-center justify-center">
                3
              </div>
            </div>
          </header>

          {/* Main Layout Split Screen */}
          <div className="max-w-4xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch mb-8">
            
            {/* Left Column: Calibration Action Panel */}
            <div className="bg-surface border border-outline-variant/20 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div className="flex flex-col gap-4">
                <div className="bg-primary/5 text-primary border border-primary/20 rounded-full px-3 py-1 font-label-sm text-[11px] font-bold uppercase tracking-wider inline-flex items-center gap-1.5 self-start shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
                  PHASE 01: BASELINE CALIBRATION
                </div>

                <h1 className="font-headline-lg text-[28px] font-extrabold text-on-surface tracking-tight">
                  Initialize Cognitive Profile
                </h1>

                <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                  Welcome to the baseline calibration simulation. Over the next 10 minutes, the assessment engine will monitor your logic paths, scenario debugging accuracy, and analytical constraints to calibrate your career DNA profile.
                </p>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowGuidelines(!showGuidelines)}
                  className="flex-1 py-3 border border-outline font-label-md text-xs text-on-surface rounded-lg hover:bg-surface-container-low transition-colors font-semibold"
                >
                  {showGuidelines ? "Hide Guidelines" : "Review Guidelines"}
                </button>
                <button
                  onClick={handleStartSimulation}
                  className="flex-1 py-3 bg-black text-white font-label-md text-xs rounded-lg shadow-md hover:bg-black/90 hover:scale-[1.02] active:scale-[0.98] transition-all font-bold flex items-center justify-center gap-1.5"
                >
                  Start Simulation Baseline
                  <span className="material-symbols-outlined text-[16px]">play_arrow</span>
                </button>
              </div>
            </div>

            {/* Right Column: Outlined Cards stack */}
            <div className="flex flex-col gap-4">
              <div className="border border-outline-variant/30 rounded-xl p-4 flex gap-4 items-start bg-surface shadow-sm hover:border-primary/30 transition-all duration-200">
                <div className="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center justify-center text-primary shrink-0">
                  <span className="material-symbols-outlined text-[20px]">psychology</span>
                </div>
                <div>
                  <h4 className="font-label-md text-label-md font-bold text-on-surface mb-1">Analytical Depth</h4>
                  <p className="font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
                    Evaluates logic choices, requirement triage decisions, and custom code adjustments across core scenarios.
                  </p>
                </div>
              </div>

              <div className="border border-outline-variant/30 rounded-xl p-4 flex gap-4 items-start bg-surface shadow-sm hover:border-primary/30 transition-all duration-200">
                <div className="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center justify-center text-primary shrink-0">
                  <span className="material-symbols-outlined text-[20px]">insights</span>
                </div>
                <div>
                  <h4 className="font-label-md text-label-md font-bold text-on-surface mb-1">Cognitive Profile</h4>
                  <p className="font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
                    Maps problem-solving response speed, mistake discovery checks, and detailed accuracy trends.
                  </p>
                </div>
              </div>

              <div className="border border-outline-variant/30 rounded-xl p-4 flex gap-4 items-start bg-surface shadow-sm hover:border-primary/30 transition-all duration-200">
                <div className="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center justify-center text-primary shrink-0">
                  <span className="material-symbols-outlined text-[20px]">groups</span>
                </div>
                <div>
                  <h4 className="font-label-md text-label-md font-bold text-on-surface mb-1">Role Matching</h4>
                  <p className="font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
                    Cross-references cognitive metrics directly with target guidelines to trace your optimal career match.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Guidelines expandable block */}
          {showGuidelines && (
            <div className="max-w-4xl mx-auto w-full bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm animate-fade-in font-body-sm text-[13px] text-on-surface-variant leading-relaxed flex flex-col gap-2 mb-6">
              <h4 className="font-label-md text-sm font-bold text-on-surface flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[20px]">rule</span>
                Calibration Guidelines
              </h4>
              <ul className="list-disc pl-5 flex flex-col gap-1.5">
                <li>Make sure to follow scenario timers inside the simulation workspace.</li>
                <li>Submit completed workbooks or logs to trigger profile indexing scans.</li>
                <li>Write clear bug severities and resolve database constraint anomalies where applicable.</li>
              </ul>
            </div>
          )}

          {/* Bottom Info Row (Duration, Difficulty, Status) */}
          <div className="max-w-4xl mx-auto w-full grid grid-cols-3 gap-4 mb-8">
            {/* Duration */}
            <div className="bg-surface-container-low border border-outline-variant/20 rounded-xl p-4 flex items-center gap-3 shadow-inner">
              <span className="material-symbols-outlined text-[24px] text-primary">schedule</span>
              <div>
                <span className="font-label-sm text-[10px] text-outline uppercase font-bold block">Duration</span>
                <span className="font-headline-md text-sm font-bold text-on-surface">10:00 Mins</span>
              </div>
            </div>

            {/* Difficulty */}
            <div className="bg-surface-container-low border border-outline-variant/20 rounded-xl p-4 flex items-center gap-3 shadow-inner">
              <span className="material-symbols-outlined text-[24px] text-primary">bar_chart</span>
              <div>
                <span className="font-label-sm text-[10px] text-outline uppercase font-bold block mb-1.5">Difficulty</span>
                {/* Visual 4 dash indicator representation */}
                <div className="flex gap-1.5 select-none">
                  <span className="w-5 h-1.5 bg-primary rounded-full"></span>
                  <span className="w-5 h-1.5 bg-primary rounded-full"></span>
                  <span className="w-5 h-1.5 bg-primary rounded-full"></span>
                  <span className="w-5 h-1.5 bg-outline-variant/30 rounded-full"></span>
                </div>
              </div>
            </div>

            {/* Status */}
            <div className="bg-surface-container-low border border-outline-variant/20 rounded-xl p-4 flex items-center gap-3 shadow-inner">
              <span className="material-symbols-outlined text-[24px] text-primary">sensors</span>
              <div>
                <span className="font-label-sm text-[10px] text-outline uppercase font-bold block">Status</span>
                <span className="font-headline-md text-sm font-bold text-on-surface flex items-center">
                  <span className="relative flex h-2 w-2 mr-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  Ready
                </span>
              </div>
            </div>
          </div>

          {/* Legal Disclaimer Footer */}
          <footer className="w-full text-center border-t border-outline-variant/20 pt-4">
            <p className="font-body-sm text-[11px] text-outline leading-relaxed max-w-xl mx-auto">
              By launching this calibration step, you consent to our telemetry collection agreements. Assessment inputs are encrypted and utilized only for career DNA profiling indexes.
            </p>
          </footer>
        </div>
      )}
    </div>
  );
}
