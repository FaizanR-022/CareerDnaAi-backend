"use client";

import React from "react";

export default function EventToast({
  showToast,
  setShowToast,
  toastFeedback,
  setToastFeedback,
}) {
  if (!showToast) return null;

  const handleFeasibility = () => {
    setToastFeedback(
      "Feasibility Analysis: This requires telepathic brain-computer interfaces not supported by modern web browsers or standard CSS. Estimated R&D: 85 years. Cost: $42M. Suggestion: Deflect or push back."
    );
  };

  const handlePushBack = () => {
    setToastFeedback(
      "Push Back Success: You successfully negotiated with Acme Corp's stakeholder, explaining current sprint constraints. They agreed to defer the onboarding feature to Q4. Client Happiness remains at MVP baseline!"
    );
  };

  return (
    <div className="absolute bottom-8 right-8 w-[420px] bg-surface rounded-xl shadow-xl border border-outline-variant/20 border-l-4 border-l-tertiary-container overflow-hidden z-50 transition-all duration-300">
      <div className="p-6 flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-tertiary-container">
            <span className="material-symbols-outlined">warning</span>
            <span className="font-label-sm text-label-sm uppercase tracking-wide font-bold">
              URGENT · CLIENT REQUEST
            </span>
          </div>
          <button
            onClick={() => {
              setShowToast(false);
              setToastFeedback(null);
            }}
            className="text-outline hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Content */}
        <div>
          <h3 className="font-headline-md text-[18px] text-on-surface mb-2">
            Client Requesting Impossible Feature
          </h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant italic bg-surface-container-low p-3 rounded-lg border border-outline-variant/10">
            "Can we also have real-time telepathic onboarding by Friday?"
          </p>
        </div>

        {/* Action Buttons */}
        {!toastFeedback ? (
          <div className="flex gap-3 mt-2">
            <button
              onClick={handleFeasibility}
              className="flex-1 py-2.5 px-4 rounded-lg border border-on-surface text-on-surface font-label-md text-label-md hover:bg-surface-container transition-colors focus:outline-none"
            >
              Analyze Feasibility
            </button>
            <button
              onClick={handlePushBack}
              className="flex-1 py-2.5 px-4 rounded-lg bg-tertiary-container text-on-tertiary font-label-md text-label-md hover:bg-tertiary shadow-md transition-all focus:outline-none"
            >
              Push Back
            </button>
          </div>
        ) : (
          /* Feedback display section */
          <div className="mt-2 bg-primary/5 p-4 rounded-lg border border-primary/20 flex flex-col gap-3">
            <p className="font-body-sm text-body-sm text-on-surface">
              {toastFeedback}
            </p>
            <button
              onClick={() => setToastFeedback(null)}
              className="self-end text-xs font-semibold text-primary hover:underline"
            >
              Clear Feedback
            </button>
          </div>
        )}

        {/* Footer info line */}
        <div className="flex items-center gap-2 text-outline mt-2 pt-4 border-t border-outline-variant/20">
          <span className="material-symbols-outlined text-[16px]">notifications</span>
          <span className="font-body-sm text-[12px] italic">
            Subtle impossibility detected by scoring agent
          </span>
        </div>
      </div>
    </div>
  );
}
