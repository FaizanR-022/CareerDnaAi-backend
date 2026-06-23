"use client";

import React, { useState } from "react";

export default function SqaSidebar({ difficulty }) {
  const [activeChannel, setActiveChannel] = useState("frontend-dev");
  const [isChannelMenuExpanded, setIsChannelMenuExpanded] = useState(false);
  const [inputValue, setInputValue] = useState("");

  // Initialize conversations directly using lazy state initializers
  const [devMessages, setDevMessages] = useState(() => {
    if (difficulty === "easy") {
      return [
        {
          id: 101,
          sender: "Dan (Frontend Dev)",
          time: "10:02 AM",
          avatar: "D",
          color: "bg-blue-600",
          content: "Hey! I pushed the new staging build for review.",
          type: "received",
        },
        {
          id: 102,
          sender: "Dan (Frontend Dev)",
          time: "10:03 AM",
          avatar: "D",
          color: "bg-blue-600",
          content: "Let me know if there are any issues. If you find something, log it and I'll jump on it immediately. Thanks, fixing now!",
          type: "received",
        },
      ];
    } else if (difficulty === "hard") {
      return [
        {
          id: 101,
          sender: "Dan (Frontend Dev)",
          time: "10:02 AM",
          avatar: "D",
          color: "bg-error",
          content: "Look, we are trying to ship this tonight. Please don't open blocking tickets unless they are absolute showstoppers.",
          type: "received",
        },
        {
          id: 102,
          sender: "Dan (Frontend Dev)",
          time: "10:03 AM",
          avatar: "D",
          color: "bg-error",
          content: "I saw you marked the guest checkout validation issue as Critical. I can't reproduce this on my end, and the PM explicitly told me this is a feature, not a bug. Justify the severity or lower it. We can't block the release.",
          type: "received",
        },
      ];
    } else {
      // Medium
      return [
        {
          id: 101,
          sender: "Dan (Frontend Dev)",
          time: "10:02 AM",
          avatar: "D",
          color: "bg-tertiary-container",
          content: "Hey, I saw your QA slack tag. Did we test the card payment form?",
          type: "received",
        },
        {
          id: 102,
          sender: "Dan (Frontend Dev)",
          time: "10:03 AM",
          avatar: "D",
          color: "bg-tertiary-container",
          content: "Let me know if you run into failures. But please, if something fails, can you provide the exact reproduction steps? My local logs look clean.",
          type: "received",
        },
      ];
    }
  });

  const [teamMessages, setTeamMessages] = useState(() => {
    return [
      {
        id: 201,
        sender: "Sarah (Product Manager)",
        time: "09:45 AM",
        avatar: "S",
        color: "bg-purple-600",
        content: "Hey QA squad! Make sure to verify the PRD specifications first before running live validation checks.",
        type: "received",
      },
      {
        id: 202,
        sender: "Sarah (Product Manager)",
        time: "09:46 AM",
        avatar: "S",
        color: "bg-purple-600",
        content: "We need 100% test coverage on the registration path. Look out for requirement gaps!",
        type: "received",
      },
    ];
  });

  const [squadMessages, setSquadMessages] = useState(() => {
    return [
      {
        id: 301,
        sender: "Alex (QA Lead)",
        time: "09:50 AM",
        avatar: "A",
        color: "bg-green-600",
        content: "Team, remember the severity definitions: Critical (blocks core flow), High (major feature broken, workaround exists), Low (UI tweak).",
        type: "received",
      },
      {
        id: 302,
        sender: "Alex (QA Lead)",
        time: "09:52 AM",
        avatar: "A",
        color: "bg-green-600",
        content: "On Hard mode, Dan is going to push back on severity. You will have to write a structured justification in the triage panel.",
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
    let npcReplyContent = "Understood. Re-running the checks.";

    if (activeChannel === "frontend-dev") {
      setMessagesFn = setDevMessages;
      npcReplyName = "Dan (Frontend Dev)";
      npcColor = difficulty === "hard" ? "bg-error" : difficulty === "medium" ? "bg-tertiary-container" : "bg-blue-600";

      if (difficulty === "easy") {
        npcReplyContent = "Got it! Thanks, fixing now! Pushing hotfix shortly.";
      } else if (difficulty === "medium") {
        npcReplyContent = "I'll take a look. Can you provide the exact reproduction steps? I need device detail logs.";
      } else {
        npcReplyContent = "I still can't reproduce this, and PM says this is a feature, not a bug. Justify the severity. We can't delay shipping for minor edge case checks.";
      }
    } else if (activeChannel === "product-team") {
      setMessagesFn = setTeamMessages;
      npcReplyName = "Sarah (Product Manager)";
      npcColor = "bg-purple-600";
      npcReplyContent = "Thanks for verifying this. Let's make sure we log all gaps in the Specs tab.";
    } else {
      setMessagesFn = setSquadMessages;
      npcReplyName = "Alex (QA Lead)";
      npcColor = "bg-green-600";
      npcReplyContent = "Nice catch. Make sure to attach the test case ID to the bug report.";
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
      case "product-team":
        return teamMessages;
      case "qa-squad":
        return squadMessages;
      case "frontend-dev":
      default:
        return devMessages;
    }
  };

  const channels = [
    { id: "frontend-dev", label: "frontend-dev", notification: difficulty === "hard" ? 2 : 0 },
    { id: "product-team", label: "product-team", notification: 0 },
    { id: "qa-squad", label: "qa-squad", notification: 1 },
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
