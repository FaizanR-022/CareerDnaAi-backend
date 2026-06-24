"use client";
/* eslint-disable react-hooks/purity */

import React, { useState } from "react";

export default function BeSidebar({ difficulty }) {
  const [activeChannel, setActiveChannel] = useState("frontend-team");
  const [isChannelMenuExpanded, setIsChannelMenuExpanded] = useState(false);
  const [inputValue, setInputValue] = useState("");

  // Response selections
  const [easySelection, setEasySelection] = useState(null);
  const [medReason, setMedReason] = useState("");

  // Slack style messages thread states
  const [devopsMessages, setDevopsMessages] = useState(() => {
    return [
      {
        id: 101,
        sender: "AWS-CloudWatch (Bot)",
        time: "11:58 AM",
        avatar: "CW",
        color: "bg-red-600",
        content: difficulty === "hard"
          ? "[ALERT] RDS database storage write latency exceeded 2000ms. CPU utilization at 92%. Memory pressure high."
          : "[INFO] RDS CPU utilization is stable at 24%. Daily backups successfully shipped to S3 bucket.",
        type: "received",
      }
    ];
  });

  const [frontendMessages, setFrontendMessages] = useState(() => {
    let initialMessage = "";
    if (difficulty === "easy") {
      initialMessage = "Hey! I'm getting a 404 (Not Found) error on '/api/users/profile' when trying to fetch the user profile page. Is the route configured properly?";
    } else if (difficulty === "medium") {
      initialMessage = "The user dashboard isn't loading at all on staging. Chrome DevTools shows a 500 (Internal Server Error) response from the API server. Can you look into this?";
    } else {
      initialMessage = "Backend is down again, my widgets are completely blank! Why is nothing responding? Fix it ASAP please, we have a client review in 15 mins.";
    }

    return [
      {
        id: 201,
        sender: "Aiden (Frontend Lead)",
        time: "12:02 PM",
        avatar: "AI",
        color: "bg-purple-600",
        content: initialMessage,
        type: "received",
      }
    ];
  });

  const [backendMessages, setBackendMessages] = useState(() => {
    return [
      {
        id: 301,
        sender: "Elena (Senior Backend)",
        time: "11:50 AM",
        avatar: "EL",
        color: "bg-blue-600",
        content: "Hey folks, reminder that we are migrating the production database schema tonight. Keep transaction logs clean.",
        type: "received",
      }
    ];
  });

  const handleSendMessage = (content, customSender = "You", customColor = "bg-primary-container", customType = "sent") => {
    const userMessage = {
      id: Date.now(),
      sender: customSender,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      avatar: customSender === "You" ? "Y" : customSender.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase(),
      color: customColor,
      content,
      type: customType,
    };

    let setMessagesFn;
    let npcReplyContent = "Checking it right now.";
    let npcName = "Aiden (Frontend Lead)";
    let npcColor = "bg-purple-600";

    if (activeChannel === "frontend-team") {
      setMessagesFn = setFrontendMessages;
      const lower = content.toLowerCase();

      // Check keywords for Hard mode justification
      const hasKeywords = lower.includes("log") || lower.includes("trace") || lower.includes("crash") || lower.includes("timeout") || lower.includes("query") || lower.includes("db") || lower.includes("database") || lower.includes("server") || lower.includes("uptime") || lower.includes("latency");

      if (difficulty === "easy") {
        npcReplyContent = "Ah, nice catch! The endpoint suffix was registered incorrectly as `/api/user/profile` instead of `/api/users/profile`. I'll update my query path and verify it works.";
      } else if (difficulty === "medium") {
        if (content.includes("Null pointer exception")) {
          npcReplyContent = "Aha! That explains the unhandled 500 error. The user dashboard config was indeed returning null for guest accounts. Thanks for patching that user schema validation.";
        } else {
          npcReplyContent = "Got it. Let me reload the staging environment and inspect if database connection limits are still exhausted.";
        }
      } else {
        // Hard
        if (hasKeywords && content.length > 20) {
          npcReplyContent = "Thanks for verifying. Checking the system logs and database stack trace is definitely the right approach. Let me know when the deadlock queries are terminated so I can verify the widgets.";
        } else {
          npcReplyContent = "I don't get it. How does that fix the blank widgets? Can you check the API server logs or the database connections directly and tell me what the error output is?";
        }
      }
    } else if (activeChannel === "devops-alerts") {
      setMessagesFn = setDevopsMessages;
      npcName = "AWS-CloudWatch (Bot)";
      npcColor = "bg-red-600";
      npcReplyContent = "[SYSTEM RESUME] RDS alert cleared. Write latency stabilized back to 22ms. Threshold normal.";
    } else {
      setMessagesFn = setBackendMessages;
      npcName = "Elena (Senior Backend)";
      npcColor = "bg-blue-600";
      npcReplyContent = "Sounds like a plan. Let's make sure the read replicas are synced before we touch the main table schemas.";
    }

    setMessagesFn((prev) => [...prev, userMessage]);
    setInputValue("");

    // NPC Reply
    setTimeout(() => {
      setMessagesFn((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: npcName,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          avatar: npcName.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase(),
          color: npcColor,
          content: npcReplyContent,
          type: "received",
        }
      ]);
    }, 1500);
  };

  const getActiveMessages = () => {
    switch (activeChannel) {
      case "devops-alerts":
        return devopsMessages;
      case "backend-squad":
        return backendMessages;
      case "frontend-team":
      default:
        return frontendMessages;
    }
  };

  const channels = [
    { id: "devops-alerts", label: "devops-alerts", notification: difficulty === "hard" ? 1 : 0 },
    { id: "frontend-team", label: "frontend-team", notification: 1 },
    { id: "backend-squad", label: "backend-squad", notification: 0 },
  ];

  return (
    <aside className="w-[340px] md:w-[360px] bottom-0 shrink-0 flex bg-inverse-surface shadow-xl z-40 fixed left-0 top-20 border-r border-on-surface-variant/10 text-inverse-primary transition-all duration-300">
      {/* 1. Inner Left Sidebar (Channels) */}
      <div className={`flex flex-col border-r border-white/10 bg-black/10 transition-all duration-300 ${isChannelMenuExpanded ? "w-[140px]" : "w-[60px]"}`}>
        
        {/* Toggle Button */}
        <div className="h-14 flex items-center justify-center border-b border-white/10">
          <button 
            onClick={() => setIsChannelMenuExpanded(!isChannelMenuExpanded)}
            className="w-8 h-8 flex items-center justify-center rounded hover:bg-white/10 text-white transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">
              {isChannelMenuExpanded ? "menu_open" : "menu"}
            </span>
          </button>
        </div>

        {/* Channel List */}
        <div className="flex-1 py-4 flex flex-col gap-2 px-2">
          {channels.map((chan) => (
            <button
              key={chan.id}
              onClick={() => setActiveChannel(chan.id)}
              className={`flex items-center gap-3 p-2 rounded-lg transition-colors overflow-hidden ${
                activeChannel === chan.id ? "bg-primary-container text-on-primary-container" : "hover:bg-white/5 text-surface-variant"
              }`}
              title={`#${chan.label}`}
            >
              <span className="material-symbols-outlined text-[18px] shrink-0">tag</span>
              
              {/* Expanded Text */}
              {isChannelMenuExpanded && (
                <span className="font-label-sm text-[13px] truncate flex-1 text-left">
                  {chan.label}
                </span>
              )}

              {/* Notification Badge */}
              {chan.notification > 0 && (
                <span className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] ${
                  activeChannel === chan.id ? "bg-white text-primary" : "bg-error text-white"
                }`}>
                  {chan.notification}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Chat Header */}
        <div className="h-14 flex items-center px-4 border-b border-white/10 bg-white/5 shrink-0">
          <h2 className="font-headline-md text-[16px] font-bold text-white flex items-center gap-1">
            <span className="material-symbols-outlined text-[18px] text-surface-variant">tag</span>
            {activeChannel}
          </h2>
        </div>

        {/* Messages Thread */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6 scrollbar-thin">
          {getActiveMessages().map((msg) => (
            <div key={msg.id} className="flex gap-3">
              {/* Avatar */}
              <div className={`w-8 h-8 rounded shrink-0 flex items-center justify-center text-white font-bold text-xs ${msg.color}`}>
                {msg.avatar}
              </div>
              
              {/* Message Content */}
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="font-label-md text-sm text-white font-bold">{msg.sender}</span>
                  <span className="font-label-sm text-[10px] text-surface-variant/70">{msg.time}</span>
                </div>
                
                <p className="font-body-sm text-[13px] text-inverse-primary leading-relaxed break-words">
                  {msg.content}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Input response area based on difficulty (Only for frontend-team) */}
        {activeChannel === "frontend-team" ? (
          <div className="p-4 shrink-0 bg-inverse-surface border-t border-white/5 flex flex-col gap-3">
            
            {/* EASY DIFFICULTY: Scripted Buttons */}
            {difficulty === "easy" && (
              <div className="flex flex-col gap-2">
                <span className="text-[10px] text-surface-variant uppercase font-bold tracking-wider">Select Response Strategy:</span>
                {[
                  "Register endpoints prefix mapping for /api/users/profile in router stack.",
                  "Inspect HTTP method signatures (GET requests expecting route definitions).",
                  "Examine URL trailing slash filters on middleware security parameters."
                ].map((option, idx) => (
                  <button
                    key={idx}
                    disabled={easySelection !== null}
                    onClick={() => {
                      setEasySelection(idx);
                      handleSendMessage(option);
                    }}
                    className={`text-left p-2 bg-white/5 border border-white/10 rounded-lg text-xs text-inverse-primary transition-all duration-200 hover:bg-white/10 hover:border-primary-container ${
                      easySelection === idx ? "opacity-50 cursor-not-allowed" : ""
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}

            {/* MEDIUM DIFFICULTY: Dropdown option */}
            {difficulty === "medium" && (
              <div className="flex flex-col gap-2">
                <span className="text-[10px] text-surface-variant uppercase font-bold tracking-wider">Select Internal Code Diagnosis:</span>
                <select
                  value={medReason}
                  onChange={(e) => setMedReason(e.target.value)}
                  className="bg-black/40 border border-white/20 rounded-lg p-2 font-body-sm text-[12px] text-inverse-primary focus:outline-none"
                >
                  <option value="" className="bg-inverse-surface">Select diagnostic reason...</option>
                  <option value="Null pointer exception when mapping the user's dashboard configuration payload." className="bg-inverse-surface">Null Pointer exception in user dashboard config mapping</option>
                  <option value="Database connection pool limits exhausted, rejecting connection sockets." className="bg-inverse-surface">DB Connection Pool exhaustion</option>
                  <option value="Third-party microservice endpoint timed out during profile synchronization checks." className="bg-inverse-surface">Third-party service Sync Timeout</option>
                </select>
                <button
                  disabled={!medReason}
                  onClick={() => {
                    handleSendMessage(medReason);
                    setMedReason("");
                  }}
                  className="py-1.5 px-4 bg-primary text-white text-xs rounded-lg hover:bg-primary-container transition-all"
                >
                  Send Diagnostics
                </button>
              </div>
            )}

            {/* HARD DIFFICULTY: Typed professional text input */}
            {difficulty === "hard" && (
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!inputValue.trim()) return;
                  handleSendMessage(inputValue);
                  setInputValue("");
                }} 
                className="bg-white/5 border border-white/20 rounded-xl flex flex-col focus-within:border-primary-container focus-within:bg-white/10 transition-all overflow-hidden shadow-inner"
              >
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  className="w-full bg-transparent border-none text-body-sm text-inverse-primary px-3 py-2 placeholder:text-surface-variant/40 focus:ring-0 focus:outline-none resize-none h-16 scrollbar-thin"
                  placeholder="Type server diagnostic steps, log checking command, db pool status..."
                />
                
                <div className="flex justify-end p-2 border-t border-white/5 bg-black/10">
                  <button
                    type="submit"
                    disabled={!inputValue.trim()}
                    className={`w-7 h-7 flex items-center justify-center rounded transition-colors ${
                      inputValue.trim() 
                        ? "bg-primary text-white hover:bg-primary-container" 
                        : "bg-white/10 text-surface-variant/50 cursor-not-allowed"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                      send
                    </span>
                  </button>
                </div>
              </form>
            )}

          </div>
        ) : (
          /* Standard footer input for other channels */
          <div className="p-4 shrink-0 bg-inverse-surface border-t border-white/5">
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                if (!inputValue.trim()) return;
                handleSendMessage(inputValue);
                setInputValue("");
              }} 
              className="bg-white/5 border border-white/20 rounded-xl flex flex-col focus-within:border-primary-container focus-within:bg-white/10 transition-all overflow-hidden shadow-inner"
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="w-full bg-transparent border-none text-body-sm text-inverse-primary px-3 py-3 placeholder:text-surface-variant/40 focus:ring-0 focus:outline-none"
                placeholder={`Message #${activeChannel}`}
              />
              
              <div className="flex justify-end p-2 border-t border-white/5 bg-black/10">
                <button
                  type="submit"
                  disabled={!inputValue.trim()}
                  className={`w-7 h-7 flex items-center justify-center rounded transition-colors ${
                    inputValue.trim() 
                      ? "bg-primary text-white hover:bg-primary-container" 
                      : "bg-white/10 text-surface-variant/50 cursor-not-allowed"
                  }`}
                >
                  <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    send
                  </span>
                </button>
              </div>
            </form>
          </div>
        )}

      </div>
    </aside>
  );
}
