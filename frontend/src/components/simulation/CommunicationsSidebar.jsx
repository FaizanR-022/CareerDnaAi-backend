"use client";

import React, { useState, useEffect } from "react";

export default function CommunicationsSidebar({ difficulty }) {
  const [inputValue, setInputValue] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [memosPlayed, setMemosPlayed] = useState(false);
  
  // Set up dialogue state based on difficulty
  const [chatMessages, setChatMessages] = useState([]);

  // Initialize conversations when difficulty changes
  useEffect(() => {
    switch (difficulty) {
      case "easy":
        setChatMessages([
          { id: 1, sender: "Sara", content: "Just reviewed the new design mockups. Looks solid! Are we still targeting Sprint 1 for the profile upload?", type: "received" },
          { id: 2, sender: "You", content: "Let me check the MoSCoW board to see our current priorities. Give me 5 mins.", type: "sent" }
        ]);
        break;
      case "hard":
        setChatMessages([
          { id: 1, sender: "Sara", content: "CRITICAL: Database migrations failed on staging! Prod is blocked!", type: "received" },
          { id: 2, sender: "Sara", content: "We need a rollback plan or hotfix ASAP. The client is asking for status!", type: "received" },
          { id: 3, sender: "You", content: "Investigating database metrics now.", type: "sent" },
          { id: 4, sender: "Sara", content: "Client just emailed. Happiness is dropping. What do I tell them?", type: "received" }
        ]);
        break;
      case "medium":
      default:
        setChatMessages([
          { id: 1, sender: "Sara", content: "Heads up — front-end estimates just came back higher.", type: "received" },
          { id: 2, sender: "Sara", content: "Are we sure about this feature timeline?", type: "received" },
          { id: 3, sender: "You", content: "Looking at MoSCoW now — I'll get back in 5.", type: "sent" }
        ]);
        break;
    }
  }, [difficulty]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: "You",
      content: inputValue,
      type: "sent"
    };

    setChatMessages((prev) => [...prev, userMessage]);
    const sentText = inputValue;
    setInputValue("");

    // Simulate Sara responding after 2 seconds
    setTimeout(() => {
      let replyContent = "Acknowledged. Let's resolve this.";
      if (difficulty === "easy") {
        replyContent = "Got it! Let me know what we decide on the MoSCoW board.";
      } else if (difficulty === "medium") {
        replyContent = "Okay, standing by for your MoSCoW alignment. Keep me posted.";
      } else if (difficulty === "hard") {
        replyContent = "Time is ticking. We need that rollback strategy or hotfix decision now.";
      }

      setChatMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "Sara",
          content: replyContent,
          type: "received"
        }
      ]);
    }, 1500);
  };

  // Memo details by difficulty
  const getMemoDetails = () => {
    switch (difficulty) {
      case "easy":
        return {
          title: "Incoming Client Memo",
          badge: "NEW",
          badgeClass: "bg-secondary-container text-on-secondary-container",
          meta: "From: Acme Corp — 10:15 AM",
          duration: "1:24",
          waveformBars: [3, 5, 4, 6, 3, 5, 2, 4, 5, 3, 4],
        };
      case "hard":
        return {
          title: "Incoming Client Memos",
          badge: "3 NEW · URGENT",
          badgeClass: "bg-error text-on-error animate-pulse",
          meta: "From: Acme Corp — 02:45 PM",
          duration: "0:15",
          waveformBars: [8, 7, 9, 8, 9, 8, 7, 9, 8, 9, 7, 8, 9],
        };
      case "medium":
      default:
        return {
          title: "Incoming Client Memos",
          badge: "2 NEW",
          badgeClass: "bg-secondary-container text-on-secondary-container",
          meta: "From: Acme Corp — 11:24 AM",
          duration: "0:42",
          waveformBars: [3, 5, 8, 4, 6, 7, 3, 5, 4, 6],
        };
    }
  };

  const memo = getMemoDetails();

  // Chat input placeholder
  const getInputPlaceholder = () => {
    if (difficulty === "easy") return "Type your response...";
    if (difficulty === "hard") return "Type your response... (URGENT)";
    return "Type your response... (Semi-adaptive)";
  };

  return (
    <aside className="w-[340px] md:w-[360px] h-full shrink-0 flex flex-col bg-inverse-surface shadow-xl z-40 fixed left-0 top-20 border-r border-on-surface-variant/10">
      {/* Sidebar Title */}
      <div className="px-6 pt-6 pb-4 border-b border-on-surface-variant/20">
        <h2 className="font-label-sm text-label-sm tracking-widest text-surface-variant uppercase">
          COMMUNICATIONS HUB
        </h2>
      </div>

      {/* Sidebar Content (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {/* Incoming Client Memos Panel */}
        <div className={`bg-white/5 rounded-xl p-4 border border-white/10 transition-all duration-300 ${
          difficulty === "hard" ? "border-l-4 border-l-error" : ""
        }`}>
          <div className="flex justify-between items-center mb-4 gap-2">
            <div className="flex items-center gap-2">
              <span className={`material-symbols-outlined text-inverse-primary ${isPlaying ? "animate-bounce" : ""}`} style={{ fontVariationSettings: "'FILL' 1" }}>
                mic
              </span>
              <h3 className="font-label-md text-label-md text-inverse-primary truncate">
                {memo.title}
              </h3>
            </div>
            <span className={`${memo.badgeClass} px-2 py-0.5 rounded-full font-label-sm text-label-sm whitespace-nowrap`}>
              {memo.badge}
            </span>
          </div>
          
          <p className="font-body-sm text-body-sm text-surface-variant mb-4">
            {memo.meta}
          </p>
          
          {/* Waveform Player */}
          <div className="flex items-center gap-4 mb-6 bg-black/20 p-2 rounded-lg">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center shadow-md hover:bg-primary transition-colors shrink-0"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                {isPlaying ? "pause" : "play_arrow"}
              </span>
            </button>
            
            {/* Waveform Visualization */}
            <div className="flex-1 flex items-end gap-1 h-8 opacity-75 justify-center">
              {memo.waveformBars.map((height, i) => (
                <div
                  key={i}
                  className={`w-1 bg-inverse-primary rounded-full transition-all duration-300 ${
                    isPlaying ? "animate-pulse" : ""
                  }`}
                  style={{
                    height: `${height * 10}%`,
                    animationDelay: `${i * 0.1}s`,
                  }}
                />
              ))}
            </div>
            <span className="font-body-sm text-body-sm text-inverse-primary shrink-0">
              {isPlaying ? "Playing" : memo.duration}
            </span>
          </div>

          <div className="flex gap-2">
            <button className="flex-1 py-2 px-3 rounded-lg border border-outline-variant/30 text-inverse-primary font-label-sm text-label-sm flex items-center justify-center gap-1 hover:bg-white/5 transition-colors">
              <span className="material-symbols-outlined text-[16px]">mic</span> Voice
            </button>
            <button className="flex-1 py-2 px-3 rounded-lg border border-outline-variant/30 text-inverse-primary font-label-sm text-label-sm flex items-center justify-center gap-1 hover:bg-white/5 transition-colors">
              <span className="material-symbols-outlined text-[16px]">chat_bubble</span> Text
            </button>
            {difficulty !== "easy" && (
              <button className="flex-1 py-2 px-3 rounded-lg border border-outline-variant/30 text-inverse-primary font-label-sm text-label-sm flex items-center justify-center gap-1 hover:bg-white/5 transition-colors">
                <span className="material-symbols-outlined text-[16px]">
                  {difficulty === "hard" ? "notification_important" : "help"}
                </span>{" "}
                {difficulty === "hard" ? "Esc" : "Pool"}
              </button>
            )}
          </div>
        </div>

        {/* Engineering (Sara) Panel */}
        <div className="bg-white/5 rounded-xl p-4 border border-white/10 flex-1 flex flex-col min-h-[250px]">
          <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-2">
            <div className={`w-2.5 h-2.5 rounded-full ${difficulty === "hard" ? "bg-error animate-ping" : "bg-primary-container"}`}></div>
            <h3 className="font-label-md text-label-md text-inverse-primary">Engineering (Sara)</h3>
          </div>

          {/* Messages Thread */}
          <div className="flex-1 flex flex-col gap-4 overflow-y-auto mb-4 pr-1 scrollbar-thin">
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col gap-1 max-w-[85%] ${
                  msg.type === "sent" ? "self-end items-end" : "self-start items-start"
                }`}
              >
                <span className="font-label-sm text-[10px] text-surface-variant/80">
                  {msg.sender}
                </span>
                <div
                  className={`p-3 rounded-xl font-body-sm text-body-sm transition-all duration-300 ${
                    msg.type === "sent"
                      ? "bg-primary-container text-on-primary-container rounded-tr-none"
                      : "bg-white/10 border border-white/5 text-inverse-primary rounded-tl-none"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
          </div>

          {/* Input Area */}
          <form onSubmit={handleSendMessage} className="relative mt-auto">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="w-full bg-white/5 border border-outline-variant/30 rounded-lg py-3 pl-4 pr-12 font-body-sm text-body-sm text-inverse-primary placeholder:text-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
              placeholder={getInputPlaceholder()}
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-primary-container hover:text-primary transition-colors focus:outline-none"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                send
              </span>
            </button>
          </form>
        </div>
      </div>
    </aside>
  );
}
