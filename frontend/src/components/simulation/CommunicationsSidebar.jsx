"use client";

import React, { useState, useEffect } from "react";

export default function CommunicationsSidebar({ difficulty }) {
  const [activeChannel, setActiveChannel] = useState("developer");
  const [isChannelMenuExpanded, setIsChannelMenuExpanded] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);

  // Set up dialogue state based on difficulty
  const [devMessages, setDevMessages] = useState([]);
  const [clientMessages, setClientMessages] = useState([]);

  // Initialize conversations when difficulty changes
  useEffect(() => {
    // Sara (Developer) Messages
    switch (difficulty) {
      case "easy":
        setDevMessages([
          { id: 1, sender: "Sara", time: "10:12 AM", avatar: "S", color: "bg-green-500", content: "Just reviewed the new design mockups. Looks solid! Are we still targeting Sprint 1 for the profile upload?", type: "received" },
          { id: 2, sender: "You", time: "10:15 AM", avatar: "Y", color: "bg-primary-container", content: "Let me check the MoSCoW board to see our current priorities. Give me 5 mins.", type: "sent" }
        ]);
        break;
      case "hard":
        setDevMessages([
          { id: 1, sender: "Sara", time: "02:40 PM", avatar: "S", color: "bg-green-500", content: "CRITICAL: Database migrations failed on staging! Prod is blocked!", type: "received" },
          { id: 2, sender: "Sara", time: "02:41 PM", avatar: "S", color: "bg-green-500", content: "We need a rollback plan or hotfix ASAP. The client is asking for status!", type: "received" },
          { id: 3, sender: "You", time: "02:43 PM", avatar: "Y", color: "bg-primary-container", content: "Investigating database metrics now.", type: "sent" },
          { id: 4, sender: "Sara", time: "02:45 PM", avatar: "S", color: "bg-green-500", content: "Client just emailed. Happiness is dropping. What do I tell them?", type: "received" }
        ]);
        break;
      case "medium":
      default:
        setDevMessages([
          { id: 1, sender: "Sara", time: "11:20 AM", avatar: "S", color: "bg-green-500", content: "Heads up — front-end estimates just came back higher.", type: "received" },
          { id: 2, sender: "Sara", time: "11:22 AM", avatar: "S", color: "bg-green-500", content: "Are we sure about this feature timeline?", type: "received" },
          { id: 3, sender: "You", time: "11:24 AM", avatar: "Y", color: "bg-primary-container", content: "Looking at MoSCoW now — I'll get back in 5.", type: "sent" }
        ]);
        break;
    }

    // Client Messages (Simulating the Voice Memo as a chat message)
    const clientInitial = [
      { id: 10, sender: "Acme Corp (Client)", time: difficulty === "hard" ? "02:45 PM" : "11:24 AM", avatar: "A", color: "bg-secondary-container", content: "Sent a voice memo.", isAudio: true, type: "received" }
    ];
    setClientMessages(clientInitial);

  }, [difficulty]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: "You",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      avatar: "Y",
      color: "bg-primary-container",
      content: inputValue,
      type: "sent"
    };

    if (activeChannel === "developer") {
      setDevMessages((prev) => [...prev, userMessage]);
    } else if (activeChannel === "client") {
      setClientMessages((prev) => [...prev, userMessage]);
    }

    setInputValue("");

    // Simulate NPC responding after 1.5 seconds
    setTimeout(() => {
      let replyContent = "Acknowledged. Let's resolve this.";
      if (activeChannel === "developer") {
        if (difficulty === "easy") replyContent = "Got it! Let me know what we decide on the MoSCoW board.";
        if (difficulty === "medium") replyContent = "Okay, standing by for your MoSCoW alignment. Keep me posted.";
        if (difficulty === "hard") replyContent = "Time is ticking. We need that rollback strategy or hotfix decision now.";
        
        setDevMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, sender: "Sara", time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), avatar: "S", color: "bg-green-500", content: replyContent, type: "received" }
        ]);
      } else if (activeChannel === "client") {
        replyContent = "Thanks for the update. We are monitoring the situation closely.";
        setClientMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, sender: "Acme Corp (Client)", time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), avatar: "A", color: "bg-secondary-container", content: replyContent, type: "received" }
        ]);
      }
    }, 1500);
  };

  const channels = [
    { id: "developer", label: "developer", notification: difficulty === "hard" ? 2 : 0 },
    { id: "designer", label: "designer", notification: 0 },
    { id: "client", label: "client", notification: difficulty === "hard" ? 1 : 1 },
    { id: "project-team", label: "project-team", notification: 0 },
  ];

  // Get active messages based on channel
  const activeMessages = activeChannel === "developer" ? devMessages 
                       : activeChannel === "client" ? clientMessages 
                       : []; // Empty for designer/project-team for now

  return (
   <aside className="w-[340px] md:w-[360px] bottom-0 shrink-0 flex bg-inverse-surface shadow-xl z-40 fixed left-0 top-20 border-r border-on-surface-variant/10 text-inverse-primary transition-all duration-300">
      
      {/* 1. Inner Left Sidebar (Channels) */}
      <div className={`flex flex-col border-r border-white/10 bg-black/10 transition-all duration-300 ${isChannelMenuExpanded ? 'w-[140px]' : 'w-[60px]'}`}>
        
        {/* Toggle Button */}
        <div className="h-14 flex items-center justify-center border-b border-white/10">
          <button 
            onClick={() => setIsChannelMenuExpanded(!isChannelMenuExpanded)}
            className="w-8 h-8 flex items-center justify-center rounded hover:bg-white/10 transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">
              {isChannelMenuExpanded ? 'menu_open' : 'menu'}
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
                activeChannel === chan.id ? 'bg-primary-container text-on-primary-container' : 'hover:bg-white/5 text-surface-variant'
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
                  activeChannel === chan.id ? 'bg-white text-primary' : 'bg-error text-white'
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
          {activeMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-surface-variant/50 gap-2">
              <span className="material-symbols-outlined text-[48px]">forum</span>
              <p className="font-body-sm text-[13px]">No messages in #{activeChannel} yet.</p>
            </div>
          ) : (
            activeMessages.map((msg) => (
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
                  
                  {/* Standard Text Message */}
                  {!msg.isAudio && (
                    <p className="font-body-sm text-[13px] text-inverse-primary leading-relaxed break-words">
                      {msg.content}
                    </p>
                  )}

                  {/* Audio Message UI (Client Memo) */}
                  {msg.isAudio && (
                    <div className="mt-2 bg-black/20 border border-white/10 p-3 rounded-lg flex flex-col gap-3">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setIsPlaying(!isPlaying)}
                          className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center shadow-md hover:bg-primary transition-colors shrink-0"
                        >
                          <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                            {isPlaying ? "pause" : "play_arrow"}
                          </span>
                        </button>
                        <div className="flex-1 flex items-end gap-[3px] h-6 opacity-75 justify-center">
                          {[3, 5, 8, 4, 6, 7, 3, 5, 4, 6, 8, 5, 4].map((height, i) => (
                            <div
                              key={i}
                              className={`w-1 bg-inverse-primary rounded-full transition-all duration-300 ${isPlaying ? "animate-pulse" : ""}`}
                              style={{ height: `${height * 10}%`, animationDelay: `${i * 0.1}s` }}
                            />
                          ))}
                        </div>
                        <span className="font-body-sm text-[11px] text-surface-variant shrink-0">
                          {isPlaying ? "Playing" : "0:42"}
                        </span>
                      </div>
                      <p className="font-body-sm text-[11px] text-outline-variant italic border-l-2 border-white/20 pl-2">
                        {difficulty === "hard" 
                          ? "We need to pivot the data architecture immediately. Current spec is insufficient."
                          : "We are excited about Sprint 1! Can we ensure the Stripe flow handles EU cards?"}
                      </p>
                    </div>
                  )}
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
                {/* Picture Button */}
                <button type="button" className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-surface-variant transition-colors" title="Attach picture">
                  <span className="material-symbols-outlined text-[18px]">image</span>
                </button>
                {/* Voice Button */}
                <button type="button" className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-surface-variant transition-colors" title="Record voice">
                  <span className="material-symbols-outlined text-[18px]">mic</span>
                </button>
              </div>
              
              {/* Send Button */}
              <button
                type="submit"
                disabled={!inputValue.trim()}
                className={`w-7 h-7 flex items-center justify-center rounded transition-colors ${
                  inputValue.trim() 
                    ? 'bg-primary text-white hover:bg-primary-container' 
                    : 'bg-white/10 text-surface-variant/50 cursor-not-allowed'
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