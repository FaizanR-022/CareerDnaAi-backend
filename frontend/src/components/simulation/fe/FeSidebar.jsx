"use client";
/* eslint-disable react-hooks/purity */

import React, { useState } from "react";

export default function FeSidebar({ difficulty }) {
  const [activeChannel, setActiveChannel] = useState("client-feedback");
  const [isChannelMenuExpanded, setIsChannelMenuExpanded] = useState(false);
  const [inputValue, setInputValue] = useState("");

  // Easy Selection State
  const [easySelection, setEasySelection] = useState(null);

  // Medium Selection State
  const [medReason, setMedReason] = useState("");

  // Dialogue states
  const [clientMessages, setClientMessages] = useState(() => {
    return [
      {
        id: 101,
        sender: "Stacy (Client Stakeholder)",
        time: "10:02 AM",
        avatar: "ST",
        color: "bg-purple-600",
        content: "Hey team, we need to add an interactive 3D product showcase to our hero section. But we have strict SEO loading targets. Can we make the website render in 3D without using WebGL to save CPU cycles and load time?",
        type: "received",
      }
    ];
  });

  const [designMessages, setDesignMessages] = useState(() => {
    return [
      {
        id: 201,
        sender: "Marcus (UX Designer)",
        time: "09:40 AM",
        avatar: "M",
        color: "bg-green-600",
        content: "Hi! I just shared the new typography and grid variables in the Specs/DesignReview tab. Make sure we check for contrast compliance (AA criteria) before wireframing.",
        type: "received",
      }
    ];
  });

  const [engMessages, setEngMessages] = useState(() => {
    return [
      {
        id: 301,
        sender: "Dave (Tech Lead)",
        time: "09:45 AM",
        avatar: "D",
        color: "bg-blue-600",
        content: "Hey, we are seeing responsiveness issues on tablet viewports in the mock landing page check. Head over to the CodeSandbox tab and check media queries.",
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
    let npcReplyContent = "Understood. Reviewing standard specifications.";
    let npcName = "Stacy (Client Stakeholder)";
    let npcColor = "bg-purple-600";

    if (activeChannel === "client-feedback") {
      setMessagesFn = setClientMessages;
      
      const lower = content.toLowerCase();
      // Simple validation for client pushback keywords
      const hasKeywords = lower.includes("webgl") || lower.includes("gpu") || lower.includes("sprite") || lower.includes("3d") || lower.includes("canvas") || lower.includes("performance") || lower.includes("hardware");

      if (difficulty === "easy") {
        npcReplyContent = "Ah, thank you! That makes complete sense. We didn't realize GPU rendering required native WebGL canvas bindings. Let's proceed with the 2.5D static CSS transforms instead.";
      } else if (difficulty === "medium") {
        npcReplyContent = "Interesting. I didn't realize pure DOM matrix limitations made complex rendering so expensive. Let's go with the pre-rendered 360-degree image sprites workaround.";
      } else {
        if (hasKeywords && content.length > 25) {
          npcReplyContent = "That makes complete sense. Explaining the hardware-accelerated limitations of canvas WebGL context vs pure CSS transformations helps a lot. We will approve the lightweight sprite animation pipeline.";
        } else {
          npcReplyContent = "I don't quite understand. If CSS can do 3D box model rotations, why can't we load complex 3D meshes without WebGL? Can you explain the GPU rendering difference more thoroughly?";
        }
      }
    } else if (activeChannel === "design-system") {
      setMessagesFn = setDesignMessages;
      npcName = "Marcus (UX Designer)";
      npcColor = "bg-green-600";
      npcReplyContent = "Awesome! Let me know if you need the updated Figma token variables.";
    } else {
      setMessagesFn = setEngMessages;
      npcName = "Dave (Tech Lead)";
      npcColor = "bg-blue-600";
      npcReplyContent = "Sounds good. Make sure to double check standard flex layout wrap constraints.";
    }

    setMessagesFn((prev) => [...prev, userMessage]);
    
    // Simulate response
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
        },
      ]);
    }, 1500);
  };

  const getActiveMessages = () => {
    switch (activeChannel) {
      case "design-system":
        return designMessages;
      case "engineering":
        return engMessages;
      case "client-feedback":
      default:
        return clientMessages;
    }
  };

  const channels = [
    { id: "client-feedback", label: "client-feedback", notification: difficulty === "hard" ? 2 : 0 },
    { id: "design-system", label: "design-system", notification: 0 },
    { id: "engineering", label: "engineering", notification: 1 },
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

        {/* Input response area based on difficulty (Only for client-feedback) */}
        {activeChannel === "client-feedback" ? (
          <div className="p-4 shrink-0 bg-inverse-surface border-t border-white/5 flex flex-col gap-3">
            
            {/* EASY DIFFICULTY: Scripted Buttons */}
            {difficulty === "easy" && (
              <div className="flex flex-col gap-2">
                <span className="text-[10px] text-surface-variant uppercase font-bold tracking-wider">Select Guided Response:</span>
                {[
                  "Explain GPU WebGL context requirements & suggest static 2.5D CSS Transforms.",
                  "Recommend pre-rendered 360-degree image sprites for fast loading SEO support.",
                  "Explain WebGL loading costs and propose simple SVG layouts as compromise."
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
                <span className="text-[10px] text-surface-variant uppercase font-bold tracking-wider">Select Technical Constraint:</span>
                <select
                  value={medReason}
                  onChange={(e) => setMedReason(e.target.value)}
                  className="bg-black/40 border border-white/20 rounded-lg p-2 font-body-sm text-[12px] text-inverse-primary focus:outline-none"
                >
                  <option value="" className="bg-inverse-surface">Select limitation reason...</option>
                  <option value="Browser security/sandbox restricts direct GPU access without WebGL bindings." className="bg-inverse-surface">WebGL/GPU sandbox bindings required</option>
                  <option value="Pure DOM tree matrix math cannot parse 3D meshes without canvas rendering contexts." className="bg-inverse-surface">DOM mesh rendering limit</option>
                  <option value="Standard CSS 3D is limited to box model matrix rotations, not complex interactive models." className="bg-inverse-surface">CSS 3D rotation constraint</option>
                </select>
                <button
                  disabled={!medReason}
                  onClick={() => {
                    handleSendMessage(medReason);
                    setMedReason("");
                  }}
                  className="py-1.5 px-4 bg-primary text-white text-xs rounded-lg hover:bg-primary-container transition-all"
                >
                  Send Response
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
                  placeholder="Type professional GPU/WebGL pushback explanation..."
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
