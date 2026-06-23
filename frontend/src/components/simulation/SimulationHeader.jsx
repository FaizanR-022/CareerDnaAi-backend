"use client";

import React from "react";

export default function SimulationHeader({ difficulty, setDifficulty }) {
  // Metrics configuration based on difficulty
  const getMetrics = () => {
    switch (difficulty) {
      case "easy":
        return {
          badgeText: "EASY DIFFICULTY",
          badgeClass: "bg-primary-fixed text-on-primary-fixed border-primary-fixed-dim",
          timerIcon: "schedule",
          timerClass: "text-primary border-primary/30 bg-surface-container-low",
          timerTextClass: "text-primary font-bold",
          timeRemaining: "04:32",
          happinessVal: 95,
          happinessText: "95%",
          happinessIcon: "sentiment_satisfied",
          happinessIconClass: "text-primary",
          budgetVal: 90,
          budgetText: "90%",
          budgetIcon: "attach_money",
          budgetIconClass: "text-primary",
        };
      case "hard":
        return {
          badgeText: "HARD DIFFICULTY",
          badgeClass: "bg-error-container text-on-error-container border-error/50",
          timerIcon: "alarm",
          timerClass: "border-error/50 bg-error-container/20 animate-pulse text-error",
          timerTextClass: "text-error font-extrabold",
          timeRemaining: "01:15",
          happinessVal: 42,
          happinessText: "42%",
          happinessIcon: "sentiment_very_dissatisfied",
          happinessIconClass: "text-error",
          budgetVal: 76, // 76% of budget spent
          budgetText: "$38k / $50k",
          budgetIcon: "monetization_on",
          budgetIconClass: "text-error",
        };
      case "medium":
      default:
        return {
          badgeText: "MEDIUM DIFFICULTY",
          badgeClass: "bg-surface-container-high border-primary text-primary",
          timerIcon: "timer",
          timerClass: "border-outline-variant/50 bg-surface-container text-tertiary-container",
          timerTextClass: "text-tertiary-container font-bold",
          timeRemaining: "04:32",
          happinessVal: 72,
          happinessText: "72%",
          happinessIcon: "favorite",
          happinessIconClass: "text-on-surface-variant",
          budgetVal: 24, // $12k / $50k is 24%
          budgetText: "$12k / $50k",
          budgetIcon: "monetization_on",
          budgetIconClass: "text-on-surface-variant",
        };
    }
  };

  const metrics = getMetrics();

  return (
    <header className="bg-surface border-b border-outline-variant shadow-sm px-gutter py-4 flex justify-between items-center fixed top-0 left-0 right-0 z-50 h-20">
      {/* Left: Brand & Info */}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-primary-container flex items-center justify-center text-on-primary-container shadow-sm shrink-0">
          <span className="material-symbols-outlined">auto_awesome</span>
        </div>
        <div>
          <div className="font-label-sm text-label-sm text-outline tracking-wider uppercase mb-0.5">
            Simulation
          </div>
          <div className="flex items-center gap-3">
            <h1 className="font-headline-md text-headline-md font-bold text-on-surface leading-none">
              Product Manager
            </h1>
            
            {/* Interactive Dropdown Badge */}
            <div className="relative inline-flex items-center">
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className={`appearance-none cursor-pointer border rounded-full px-3 py-1 pr-7 font-label-sm text-label-sm tracking-wide focus:outline-none focus:ring-1 focus:ring-primary ${metrics.badgeClass}`}
              >
                <option value="easy" className="bg-surface text-on-surface">EASY DIFFICULTY</option>
                <option value="medium" className="bg-surface text-on-surface">MEDIUM DIFFICULTY</option>
                <option value="hard" className="bg-surface text-on-surface">HARD DIFFICULTY</option>
              </select>
              <span className="material-symbols-outlined absolute right-2 pointer-events-none text-[16px] opacity-75">
                arrow_drop_down
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Center: Sprint Timer */}
      <div className={`flex items-center gap-3 border rounded-full px-5 py-2 shadow-sm transition-all duration-300 ${metrics.timerClass}`}>
        <span className="material-symbols-outlined">{metrics.timerIcon}</span>
        <span className="font-body-sm text-body-sm text-on-surface-variant">Sprint 1</span>
        <span className={`font-headline-md text-headline-md tracking-widest ${metrics.timerTextClass}`}>
          {metrics.timeRemaining}
        </span>
        <span className="font-body-sm text-body-sm text-outline">remaining</span>
      </div>

      {/* Right: Metrics */}
      <div className="flex items-center gap-8">
        {/* Client Happiness */}
        <div className="flex flex-col gap-1 w-32 md:w-36 transition-all duration-300">
          <div className="flex justify-between items-end">
            <div className="flex items-center gap-1 text-on-surface-variant">
              <span className={`material-symbols-outlined text-[16px] ${metrics.happinessIconClass}`}>
                {metrics.happinessIcon}
              </span>
              <span className="font-label-sm text-label-sm">Client Happiness</span>
            </div>
            <span className="font-label-md text-label-md">{metrics.happinessText}</span>
          </div>
          <div className="h-2 bg-surface-container-high rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                difficulty === "hard" ? "bg-error" : "bg-primary-container"
              }`}
              style={{ width: `${metrics.happinessVal}%` }}
            ></div>
          </div>
        </div>

        {/* Budget */}
        <div className="flex flex-col gap-1 w-36 md:w-40 transition-all duration-300">
          <div className="flex justify-between items-end">
            <div className="flex items-center gap-1 text-on-surface-variant">
              <span className={`material-symbols-outlined text-[16px] ${metrics.budgetIconClass}`}>
                {metrics.budgetIcon}
              </span>
              <span className="font-label-sm text-label-sm">Budget</span>
            </div>
            <span className="font-label-md text-label-md">{metrics.budgetText}</span>
          </div>
          <div className="h-2 bg-surface-container-high rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                difficulty === "hard" ? "bg-error" : "bg-primary-container"
              }`}
              style={{ width: `${metrics.budgetVal}%` }}
            ></div>
          </div>
        </div>
      </div>
    </header>
  );
}
