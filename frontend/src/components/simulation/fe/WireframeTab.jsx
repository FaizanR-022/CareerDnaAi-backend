"use client";
/* eslint-disable react-hooks/purity */

import React, { useState } from "react";

export default function WireframeTab({ difficulty, responsiveScore, setResponsiveScore }) {
  // Draggable items list
  const availableBlocks = [
    { id: "header", name: "Header Block", icon: "vertical_align_top", desc: "Top site navigation bar" },
    { id: "hero", name: "Hero Block", icon: "image", desc: "Large visual showcase card" },
    { id: "button", name: "Primary Button", icon: "smart_button", desc: "Yellow text action trigger button" },
    { id: "footer", name: "Footer Block", icon: "vertical_align_bottom", desc: "Bottom legal footer text" },
    { id: "spacer", name: "Spacer Block", icon: "space_bar", desc: "16px grid gap spacer margin" }
  ];

  // Placed components state
  // For Easy: { slot1: null, slot2: null, slot3: null, slot4: null }
  const [easySlots, setEasySlots] = useState({
    slot_header: null,
    slot_hero: null,
    slot_button: null,
    slot_footer: null
  });

  // For Medium/Hard: Ordered array of placed blocks
  const [placedBlocks, setPlacedBlocks] = useState([]);
  
  // Drag-and-drop feedback
  const [submitted, setSubmitted] = useState(false);
  const [success, setSuccess] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [activeDragItem, setActiveDragItem] = useState(null);

  // Constraint violations (Hard)
  const [violations, setViolations] = useState([]);

  // Drag handlers
  const handleDragStart = (e, blockId) => {
    setActiveDragItem(blockId);
    e.dataTransfer.setData("text/plain", blockId);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleEasyDrop = (e, targetSlot) => {
    e.preventDefault();
    const blockId = e.dataTransfer.getData("text/plain") || activeDragItem;
    if (!blockId) return;

    // Check if correct target matching
    // targetSlot is e.g. slot_header, blockId is header
    const expected = targetSlot.replace("slot_", "");
    
    if (blockId === expected) {
      setEasySlots(prev => ({ ...prev, [targetSlot]: blockId }));
    } else {
      alert(`Invalid placement. This zone expects the ${expected.toUpperCase()} component.`);
    }
    setActiveDragItem(null);
  };

  const handleFreeDrop = (e) => {
    e.preventDefault();
    const blockId = e.dataTransfer.getData("text/plain") || activeDragItem;
    if (!blockId) return;

    // Add block to stack
    const newBlock = availableBlocks.find(b => b.id === blockId);
    if (newBlock) {
      const blockInstance = {
        ...newBlock,
        instanceId: Date.now() + Math.random()
      };
      
      const updated = [...placedBlocks, blockInstance];
      setPlacedBlocks(updated);

      if (difficulty === "hard") {
        checkHardConstraints(updated);
      }
    }
    setActiveDragItem(null);
  };

  // Check HCI constraints for Hard difficulty
  const checkHardConstraints = (blocks) => {
    const list = [];
    
    // Constraint 1: Spacing violation (two block elements like Hero and Button placed together without a Spacer)
    for (let i = 0; i < blocks.length - 1; i++) {
      const current = blocks[i].id;
      const next = blocks[i+1].id;
      if (current !== "spacer" && next !== "spacer") {
        list.push(`Spacing Violation: ${blocks[i].name} and ${blocks[i+1].name} placed adjacent without a spacer margin (HCI Rule: elements require >=8px gap).`);
      }
    }

    // Constraint 2: Contrast violation (Button placed in a low contrast zone. Let's say if Button is placed on a yellow slot or if card backgrounds conflict)
    // For our mock, we assume the canvas background has a light yellow warning region at slot index 2.
    // If the button is placed at index 2 (0-indexed), it violates contrast.
    blocks.forEach((blk, idx) => {
      if (blk.id === "button" && idx === 2) {
        list.push("Contrast Violation: Yellow Primary Button dropped on the Light Yellow grid zone (WCAG contrast < 3.0:1).");
      }
    });

    setViolations(list);
  };

  const removeBlock = (instanceId) => {
    const updated = placedBlocks.filter(b => b.instanceId !== instanceId);
    setPlacedBlocks(updated);
    if (difficulty === "hard") {
      checkHardConstraints(updated);
    }
  };

  const handleVerify = () => {
    setSubmitted(true);

    if (difficulty === "easy") {
      const allFilled = Object.values(easySlots).every(v => v !== null);
      if (allFilled) {
        setSuccess(true);
        setFeedback("Wireframe verified successfully! Standard snap layouts conform to alignment guidelines. Responsive Score +1 Breakpoint.");
        setResponsiveScore("1/3 Breakpoints");
      } else {
        setSuccess(false);
        setFeedback("Verification failed. Please populate all Drop Zones with correct components.");
      }
    } else if (difficulty === "medium") {
      if (placedBlocks.length < 3) {
        setSuccess(false);
        setFeedback("Verification failed. Standard layouts require at least 3 UI blocks to map visual hierarchy.");
      } else {
        setSuccess(true);
        setFeedback("Free wireframe layout verified! Stack ordering saved in assets directory. Responsive Score +1 Breakpoint.");
        setResponsiveScore("2/3 Breakpoints");
      }
    } else {
      // Hard
      if (placedBlocks.length < 4) {
        setSuccess(false);
        setFeedback("Triage Rejected. Complex layout requires at least 4 blocks containing spacer and validation margins.");
      } else if (violations.length > 0) {
        setSuccess(false);
        setFeedback(`HCI Errors Blocked Submission! Please correct the ${violations.length} spacing/contrast violations logged in the monitor.`);
      } else {
        setSuccess(true);
        setFeedback("HCI spacing compliance approved! Spacer bounds and contrast checks match WCAG target ratios. Responsive Score +1 Breakpoint.");
        setResponsiveScore("3/3 Breakpoints");
      }
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setEasySlots({
      slot_header: null,
      slot_hero: null,
      slot_button: null,
      slot_footer: null
    });
    setPlacedBlocks([]);
    setViolations([]);
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* LEFT PANEL: WIREFRAME BUILDER */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        {/* Header */}
        <div className="mb-5">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">Interactive Wireframe Canvas</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Drag layout components onto the canvas to model the desktop wireframe grids.</p>
        </div>

        {submitted ? (
          /* Submission Feedback Display */
          <div className="max-w-xl mx-auto w-full bg-surface border border-outline-variant/30 rounded-2xl p-8 shadow-xl text-center flex flex-col items-center gap-5 mt-4">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
              success ? "bg-primary-container text-white" : "bg-error-container/30 text-error"
            }`}>
              <span className="material-symbols-outlined text-[36px]">
                {success ? "check_circle" : "warning"}
              </span>
            </div>

            <h3 className="font-headline-md text-[20px] font-bold text-on-surface">
              {success ? "Layout Verified" : "Layout Violations Detected"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Reset Canvas" : "Revise Wireframe"}
              </button>
            </div>
          </div>
        ) : (
          /* Wireframe Layout workspace */
          <div className="grid grid-cols-5 gap-6">
            
            {/* Block Items Toolbar (Cols 2) */}
            <div className="col-span-2 flex flex-col gap-4">
              <h3 className="font-label-md text-xs font-bold text-on-surface uppercase tracking-wider">UI Component Blocks</h3>
              <p className="font-body-sm text-[11px] text-on-surface-variant">Drag items from here onto the layout zones to the right.</p>

              <div className="flex flex-col gap-3">
                {availableBlocks.map((block) => (
                  <div
                    key={block.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, block.id)}
                    className="p-3 bg-surface border border-outline-variant/30 rounded-xl cursor-grab active:cursor-grabbing flex items-center gap-3 hover:border-primary/45 transition-colors shadow-sm select-none"
                  >
                    <div className="w-8 h-8 rounded bg-primary-container/10 text-primary flex items-center justify-center">
                      <span className="material-symbols-outlined text-[18px]">{block.icon}</span>
                    </div>
                    <div>
                      <h4 className="font-label-sm text-xs font-bold text-on-surface">{block.name}</h4>
                      <p className="font-body-sm text-[10px] text-outline">{block.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Drop Canvas (Cols 3) */}
            <div className="col-span-3 flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <h3 className="font-label-md text-xs font-bold text-on-surface uppercase tracking-wider">Layout Canvas</h3>
                <span className="font-body-sm text-[10px] text-outline font-semibold">Drop Zone</span>
              </div>

              {/* EASY WORKSPACE: Target snap drop zones */}
              {difficulty === "easy" && (
                <div className="flex flex-col gap-3 bg-surface-container-low p-4 rounded-2xl border border-dashed border-outline-variant/40 min-h-[300px]">
                  {Object.keys(easySlots).map((slotKey) => {
                    const blockId = easySlots[slotKey];
                    return (
                      <div
                        key={slotKey}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleEasyDrop(e, slotKey)}
                        className={`h-14 border rounded-xl flex items-center justify-center font-mono text-[11px] transition-all ${
                          blockId 
                            ? "bg-primary-container text-white border-primary shadow-sm font-semibold" 
                            : "bg-surface border-outline-variant/20 text-outline hover:bg-surface-container-high border-dashed"
                        }`}
                      >
                        {blockId ? (
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px]">check_circle</span>
                            {blockId.toUpperCase()} Snapped
                          </div>
                        ) : (
                          `Drop ${slotKey.replace("slot_", "").toUpperCase()} Here`
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* MEDIUM/HARD WORKSPACE: Free flow/Constraint placement canvas */}
              {difficulty !== "easy" && (
                <div 
                  onDragOver={handleDragOver}
                  onDrop={handleFreeDrop}
                  className="flex flex-col gap-2 bg-surface-container-low p-4 rounded-2xl border border-dashed border-outline-variant/40 min-h-[320px] relative overflow-hidden"
                >
                  {/* Warning Zones representation for Hard contrast */}
                  {difficulty === "hard" && (
                    <div className="absolute top-28 left-0 right-0 h-14 bg-yellow-400/5 border-y border-dashed border-yellow-400/20 flex items-center justify-center font-mono text-[9px] text-yellow-600/60 pointer-events-none uppercase tracking-wider">
                      Light Yellow High-Light Zone (Contrast Warning Area)
                    </div>
                  )}

                  {placedBlocks.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-center py-16 text-outline select-none">
                      <span className="material-symbols-outlined text-[48px] text-outline-variant mb-2">dashboard_customize</span>
                      <p className="font-body-sm text-[12px]">Canvas is empty.</p>
                      <p className="font-body-sm text-[10px] text-outline-variant">Drag and drop components to build the page structure.</p>
                    </div>
                  ) : (
                    placedBlocks.map((block, index) => (
                      <div
                        key={block.instanceId}
                        className={`h-14 border rounded-xl flex items-center justify-between px-4 transition-all duration-200 ${
                          block.id === "spacer" 
                            ? "bg-outline-variant/10 border-outline-variant/30 text-outline" 
                            : block.id === "button" && difficulty === "hard" && index === 2
                            ? "bg-yellow-100/50 border-yellow-400 text-yellow-800 font-semibold"
                            : "bg-surface border-outline-variant/35 text-on-surface font-semibold shadow-sm"
                        }`}
                      >
                        <div className="flex items-center gap-2 font-mono text-xs">
                          <span className="material-symbols-outlined text-[16px] text-primary">{block.icon}</span>
                          <span>{block.name}</span>
                          <span className="text-[10px] text-outline font-normal">Index: {index}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeBlock(block.instanceId)}
                          className="w-6 h-6 rounded-full hover:bg-outline-variant/20 flex items-center justify-center text-outline hover:text-error transition-colors"
                        >
                          <span className="material-symbols-outlined text-[16px]">close</span>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Verify Trigger */}
              <button
                onClick={handleVerify}
                className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container hover:scale-[1.01] transition-all"
              >
                Verify Wireframe Grid
              </button>
            </div>

          </div>
        )}
      </div>

      {/* RIGHT PANEL: DESIGN SYSTEM CONSTRAINTS */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">assessment</span>
          Constraints Monitor
        </h3>

        {/* Hard Mode: Constraint violation log */}
        {difficulty === "hard" ? (
          <div className="flex flex-col gap-4">
            <div className="bg-error-container/20 border border-error/20 p-3.5 rounded-xl">
              <h4 className="font-label-sm text-xs font-bold text-error mb-2 flex items-center gap-1.5 uppercase">
                <span className="material-symbols-outlined text-[16px]">gavel</span>
                Real-time HCI Bounds
              </h4>
              
              {violations.length === 0 ? (
                <div className="text-green-700 font-semibold text-[11px] flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[14px]">check_circle</span>
                  No layout violations detected.
                </div>
              ) : (
                <ul className="list-disc pl-4 font-body-sm text-[11px] text-on-surface-variant flex flex-col gap-2">
                  {violations.map((violation, i) => (
                    <li key={i} className="leading-relaxed text-error/85 font-mono text-[10px]">{violation}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-surface-container border border-outline-variant/10 p-3.5 rounded-xl font-body-sm text-[11px] text-on-surface-variant leading-relaxed">
              <span className="font-bold block uppercase mb-1">Layout Rules:</span>
              1. Never drop component blocks right next to each other without placing a <code className="bg-surface px-1 text-[10px]">Spacer Block</code> in between.<br />
              2. Keep the <code className="bg-surface px-1 text-[10px]">Primary Button</code> away from index 2 warning zone where background contrast is insufficient.
            </div>
          </div>
        ) : (
          /* Easy/Medium guidelines */
          <div className="flex flex-col gap-4 font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
            <div className="bg-surface-container border border-outline-variant/15 p-4 rounded-xl">
              <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Spacing bounds</h4>
              <p>HCI spacing models require margins between header elements, image grids, and action items to prevent mobile click overlaps.</p>
            </div>
            
            <div className="bg-surface-container border border-outline-variant/15 p-4 rounded-xl">
              <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Stack sequence</h4>
              <p>A standard landing page layout starts with Header block details on top, leading into a Hero segment, followed by action buttons, and footer links.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
