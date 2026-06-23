"use client";

import React, { useState } from "react";

export default function DaSidebar({ difficulty }) {
  const [activeChannel, setActiveChannel] = useState("vp-analytics");
  const [isChannelMenuExpanded, setIsChannelMenuExpanded] = useState(false);
  const [inputValue, setInputValue] = useState("");

  // Initialize conversations directly using lazy state initializers
  const [vpMessages, setVpMessages] = useState(() => {
    if (difficulty === "easy") {
      return [
        {
          id: 101,
          sender: "VP of Analytics (NPC)",
          time: "10:02 AM",
          avatar: "VP",
          color: "bg-green-600",
          content: "Hi there! Welcome to the analytics project. I'm excited to see what patterns we can pull from this trading volume data.",
          type: "received",
        },
        {
          id: 102,
          sender: "VP of Analytics (NPC)",
          time: "10:03 AM",
          avatar: "VP",
          color: "bg-green-600",
          content: "For our Easy run, I've had the engineering team prepare a clean Schema Explorer for you. Click 'One-Click Clean' to filter the transaction tables instantly. Let me know if you run into any schema questions!",
          type: "received",
        },
      ];
    } else if (difficulty === "hard") {
      return [
        {
          id: 101,
          sender: "VP of Analytics (NPC)",
          time: "10:02 AM",
          avatar: "VP",
          color: "bg-error",
          content: "We have a major problem. The institutional trends look completely wrong in the latest client reporting draft. I'm seeing massive RSI anomalies that don't match the historical trend. Your cleaning pipeline is flawed.",
          type: "received",
        },
        {
          id: 102,
          sender: "VP of Analytics (NPC)",
          time: "10:03 AM",
          avatar: "VP",
          color: "bg-error",
          content: "We have a tight deadline and you're wasting time on raw data. There is no schema explorer ready—you'll have to request access or inspect the raw JSON yourself. Fix this pipeline immediately or I will have to flag it to the client.",
          type: "received",
        },
      ];
    } else {
      // Medium
      return [
        {
          id: 101,
          sender: "VP of Analytics (NPC)",
          time: "10:02 AM",
          avatar: "VP",
          color: "bg-tertiary-container",
          content: "Good morning. The client has been asking why trade logs don't align with transaction counts. Are we sure we handles the nulls and duplicates properly?",
          type: "received",
        },
        {
          id: 102,
          sender: "VP of Analytics (NPC)",
          time: "10:03 AM",
          avatar: "VP",
          color: "bg-tertiary-container",
          content: "I noticed some duplicate timestamps and null fields in the raw trade data. Make sure you use the manual step tools in the explorer tab to clean them up. We can't afford bad records.",
          type: "received",
        },
      ];
    }
  });

  const [deMessages, setDeMessages] = useState(() => {
    return [
      {
        id: 201,
        sender: "Data Eng Lead",
        time: "09:45 AM",
        avatar: "DE",
        color: "bg-blue-600",
        content: "Hi! We dumped the raw transaction tables in your workspace.",
        type: "received",
      },
      {
        id: 202,
        sender: "Data Eng Lead",
        time: "09:46 AM",
        avatar: "DE",
        color: "bg-blue-600",
        content: difficulty === "hard"
          ? "For Hard mode, we locked the Schema Explorer behind the 'Request Schema Access' button due to security policies. You will have to request access to decrypt the columns."
          : difficulty === "medium"
          ? "For Medium mode, the Schema Explorer is open but clean. Look out for the constraint flags on null values."
          : "For Easy mode, everything is ready. Just click One-Click Clean to tidy it up.",
        type: "received",
      },
    ];
  });

  const [teamMessages, setTeamMessages] = useState(() => {
    return [
      {
        id: 301,
        sender: "Sarah (Associate)",
        time: "09:50 AM",
        avatar: "SA",
        color: "bg-purple-600",
        content: "Hey team! Let's get the final recommendations ready for the VP.",
        type: "received",
      },
      {
        id: 302,
        sender: "Sarah (Associate)",
        time: "09:52 AM",
        avatar: "SA",
        color: "bg-purple-600",
        content: "We need to find the correct correlation between institutional volumes and RSI divergence. Let me know what findings you get in the Insights tab!",
        type: "received",
      },
    ];
  });

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: "You",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      avatar: "Y",
      color: "bg-primary-container",
      content: inputValue,
      type: "sent",
    };

    let setMessagesFn;
    let npcReplyName;
    let npcColor;
    let npcReplyContent = "Understood. Checking the logs.";

    if (activeChannel === "vp-analytics") {
      setMessagesFn = setVpMessages;
      npcReplyName = "VP of Analytics (NPC)";
      npcColor = difficulty === "hard" ? "bg-error" : difficulty === "medium" ? "bg-tertiary-container" : "bg-green-600";

      if (difficulty === "easy") {
        npcReplyContent = "Thanks! The annotations should guide you on what each data point represents. You are doing great.";
      } else if (difficulty === "medium") {
        npcReplyContent = "Did you actually review the constraint flags? We need to make sure we aren't dropping valid records by accident.";
      } else {
        npcReplyContent = "That doesn't answer the core problem. The raw logs contain duplicate keys. You need to write custom logic or SQL queries in the visualization tab to isolate the anomalies.";
      }
    } else if (activeChannel === "data-engineering") {
      setMessagesFn = setDeMessages;
      npcReplyName = "Data Eng Lead";
      npcColor = "bg-blue-600";
      npcReplyContent = "We are currently running another pipeline. Let us know if you need us to trigger a full db rebuild.";
    } else {
      setMessagesFn = setTeamMessages;
      npcReplyName = "Sarah (Associate)";
      npcColor = "bg-purple-600";
      npcReplyContent = "Awesome! Let me know when you submit the recommendation so I can draft the slides.";
    }

    setMessagesFn((prev) => [...prev, userMessage]);
    setInputValue("");

    // Simulate response
    setTimeout(() => {
      setMessagesFn((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: npcReplyName,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          avatar: npcReplyName.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase(),
          color: npcColor,
          content: npcReplyContent,
          type: "received",
        },
      ]);
    }, 1500);
  };

  const getActiveMessages = () => {
    switch (activeChannel) {
      case "data-engineering":
        return deMessages;
      case "project-team":
        return teamMessages;
      case "vp-analytics":
      default:
        return vpMessages;
    }
  };

  const channels = [
    { id: "vp-analytics", label: "vp-analytics", notification: difficulty === "hard" ? 2 : 0 },
    { id: "data-engineering", label: "data-engineering", notification: 0 },
    { id: "project-team", label: "project-team", notification: 1 },
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
          {getActiveMessages().length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-surface-variant/50 gap-2">
              <span className="material-symbols-outlined text-[48px]">forum</span>
              <p className="font-body-sm text-[13px]">No messages in #{activeChannel} yet.</p>
            </div>
          ) : (
            getActiveMessages().map((msg) => (
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
            ))
          )}
        </div>

        {/* Slack-Style Input Area */}
        <div className="p-4 shrink-0 bg-inverse-surface border-t border-white/5">
          <form 
            onSubmit={handleSendMessage} 
            className="bg-white/5 border border-white/20 rounded-xl flex flex-col focus-within:border-primary-container focus-within:bg-white/10 transition-all overflow-hidden shadow-inner"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="w-full bg-transparent border-none text-body-sm text-inverse-primary px-3 py-3 placeholder:text-surface-variant/40 focus:ring-0 focus:outline-none"
              placeholder={`Message #${activeChannel}`}
            />
            
            {/* Input Toolbar */}
            <div className="flex justify-between items-center px-2 pb-2">
              <div className="flex gap-1">
                <button type="button" className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-surface-variant transition-colors" title="Attach picture">
                  <span className="material-symbols-outlined text-[18px]">image</span>
                </button>
                <button type="button" className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-surface-variant transition-colors" title="Record voice">
                  <span className="material-symbols-outlined text-[18px]">mic</span>
                </button>
              </div>
              
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

      </div>
    </aside>
  );
}
