"use client";

import React, { useState, useEffect } from "react";

export default function SqaHeader({ difficulty, setDifficulty, bugsFound = 0, testCoverage = 40 }) {
  // Timer state (seconds remaining)
  const [secondsLeft, setSecondsLeft] = useState(() => {
    if (difficulty === "hard") return 180; // 3 minutes
    return 480; // 8 minutes default for medium
  });

  // Calculate elapsed percentage
  const totalSeconds = difficulty === "hard" ? 180 : 480;
  const elapsedPercent = ((totalSeconds - secondsLeft) / totalSeconds) * 100;

  // Timer countdown logic
  useEffect(() => {
    if (difficulty === "easy") return;

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [difficulty]);

  // Format seconds to MM:SS
  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remainingSecs.toString().padStart(2, "0")}`;
  };

  // Metrics configuration based on difficulty
  const getMetrics = () => {
    switch (difficulty) {
      case "easy":
        return {
          badgeText: "EASY DIFFICULTY",
          badgeClass: "bg-primary-fixed text-on-primary-fixed border-primary-fixed-dim",
          timerHtml: null,
          bugsText: `${bugsFound}/3`,
          bugsVal: (bugsFound / 3) * 100,
          bugsIconClass: "text-primary",
          coverageVal: testCoverage,
          coverageText: `${testCoverage}%`,
          coverageIconClass: "text-primary",
        };
      case "hard":
        return {
          badgeText: "HARD DIFFICULTY",
          badgeClass: "bg-error-container text-on-error-container border-error/50",
          timerClass: "border-error/50 bg-error-container/20 animate-pulse text-error",
          timerTextClass: "text-error font-extrabold",
          bugsText: "Hidden",
          bugsVal: 0,
          bugsIconClass: "text-outline opacity-50",
          coverageVal: testCoverage,
          coverageText: `${testCoverage}%`,
          coverageIconClass: "text-error",
        };
      case "medium":
      default: {
        // Medium: warning amber at 70% elapsed (30% remaining: 144 seconds or less)
        const isAmber = elapsedPercent >= 70;
        return {
          badgeText: "MEDIUM DIFFICULTY",
          badgeClass: "bg-surface-container-high border-primary text-primary",
          timerClass: isAmber 
            ? "border-tertiary-container bg-tertiary-container/10 text-tertiary-container animate-pulse" 
            : "border-outline-variant/50 bg-surface-container text-primary",
          timerTextClass: isAmber ? "text-tertiary-container font-extrabold" : "text-primary font-bold",
          bugsText: "? / ?",
          bugsVal: 50, // indeterminate indicator
          bugsIconClass: "text-primary",
          coverageVal: testCoverage,
          coverageText: `${testCoverage}%`,
          coverageIconClass: "text-primary",
        };
      }
    }
  };

  const metrics = getMetrics();

  return (
    <header className="bg-surface border-b border-outline-variant shadow-sm px-gutter py-4 flex justify-between items-center fixed top-0 left-0 right-0 z-50 h-20">
      {/* Left: Brand & Info */}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-primary-container flex items-center justify-center text-on-primary-container shadow-sm shrink-0">
          <span className="material-symbols-outlined">bug_report</span>
        </div>
        <div>
          <div className="font-label-sm text-label-sm text-outline tracking-wider uppercase mb-0.5">
            Simulation
          </div>
          <div className="flex items-center gap-3">
            <h1 className="font-headline-md text-headline-md font-bold text-on-surface leading-none">
              SQA Engineer
            </h1>
            
            {/* Interactive Dropdown Badge */}
            <div className="relative inline-flex items-center">
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className={`appearance-none cursor-pointer border rounded-full px-3 py-1 pr-7 font-label-sm text-label-sm tracking-wide focus:outline-none focus:ring-1 focus:ring-primary transition-all duration-300 ${metrics.badgeClass}`}
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

      {/* Center: Countdown Timer */}
      {difficulty !== "easy" ? (
        <div className={`flex items-center gap-3 border rounded-full px-5 py-2 shadow-sm transition-all duration-300 ${metrics.timerClass}`}>
          <span className="material-symbols-outlined">{difficulty === "hard" ? "alarm" : "timer"}</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">Time Limit</span>
          <span className={`font-headline-md text-headline-md tracking-widest ${metrics.timerTextClass}`}>
            {formatTime(secondsLeft)}
          </span>
          <span className="font-body-sm text-body-sm text-outline">remaining</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 border border-outline-variant bg-surface-container-low rounded-full px-5 py-2 text-primary">
          <span className="material-symbols-outlined">verified_user</span>
          <span className="font-label-md text-label-md font-semibold">Untimed Sandbox Mode</span>
        </div>
      )}

      {/* Right: Metrics */}
      <div className="flex items-center gap-8">
        {/* Bugs Found */}
        {difficulty !== "hard" ? (
          <div className="flex flex-col gap-1 w-32 md:w-36 transition-all duration-300">
            <div className="flex justify-between items-end">
              <div className="flex items-center gap-1 text-on-surface-variant">
                <span className={`material-symbols-outlined text-[16px] ${metrics.bugsIconClass}`}>
                  bug_report
                </span>
                <span className="font-label-sm text-label-sm">Bugs Found</span>
              </div>
              <span className="font-label-md text-label-md">{metrics.bugsText}</span>
            </div>
            <div className="h-2 bg-surface-container-high rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  difficulty === "medium" ? "bg-primary/45" : "bg-primary-container"
                }`}
                style={{ width: `${metrics.bugsVal}%` }}
              ></div>
            </div>
          </div>
        ) : (
          /* Hard mode: Black-box testing hide bugs found count */
          <div className="flex flex-col gap-1 w-32 md:w-36 transition-all duration-300">
            <div className="flex justify-between items-end">
              <div className="flex items-center gap-1 text-outline/50">
                <span className="material-symbols-outlined text-[16px]">lock</span>
                <span className="font-label-sm text-label-sm">Bugs Found</span>
              </div>
              <span className="font-label-md text-label-md text-outline/50 italic text-xs">Black-box</span>
            </div>
            <div className="h-2 bg-surface-container-high rounded-full overflow-hidden opacity-30">
              <div className="h-full bg-outline rounded-full w-full"></div>
            </div>
          </div>
        )}

        {/* Test Coverage */}
        <div className="flex flex-col gap-1 w-36 md:w-40 transition-all duration-300">
          <div className="flex justify-between items-end">
            <div className="flex items-center gap-1 text-on-surface-variant">
              <span className={`material-symbols-outlined text-[16px] ${metrics.coverageIconClass}`}>
                fact_check
              </span>
              <span className="font-label-sm text-label-sm">Test Coverage</span>
            </div>
            <span className="font-label-md text-label-md">{metrics.coverageText}</span>
          </div>
          <div className="h-2 bg-surface-container-high rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                difficulty === "hard" ? "bg-error" : "bg-primary-container"
              }`}
              style={{ width: `${metrics.coverageVal}%` }}
            ></div>
          </div>
        </div>
      </div>
    </header>
  );
}
