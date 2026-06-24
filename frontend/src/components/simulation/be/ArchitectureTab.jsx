"use client";

import React, { useState } from "react";

export default function ArchitectureTab({ difficulty }) {
  const [submitted, setSubmitted] = useState(false);
  const [success, setSuccess] = useState(false);
  const [feedback, setFeedback] = useState("");

  // Easy mode states
  const [easyOrder, setEasyOrder] = useState(["", "", ""]);
  const [easyIncidentSelection, setEasyIncidentSelection] = useState("");

  // Medium mode states
  const [medViolationSelection, setMedViolationSelection] = useState("");
  const [medIncidentSelection, setMedIncidentSelection] = useState("");

  // Hard mode states
  const [hardLb, setHardLb] = useState("");
  const [hardCache, setHardCache] = useState("");
  const [hardBroker, setHardBroker] = useState("");
  const [hardIncidentSelection, setHardIncidentSelection] = useState("");

  const handleEasySubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    
    const correctSequence = easyOrder[0] === "client" && easyOrder[1] === "load_balancer" && easyOrder[2] === "web_server";
    const correctIncident = easyIncidentSelection === "clean_logs";

    if (correctSequence && correctIncident) {
      setSuccess(true);
      setFeedback("Architecture flow connected! Standard linear request path (Client -> Load Balancer -> Web Server) and disk log cleanup verified successfully.");
    } else if (!correctSequence) {
      setSuccess(false);
      setFeedback("Triage Rejected. The request routing sequence is incorrect. Requests must hit the load balancer before reaching the web server.");
    } else {
      setSuccess(false);
      setFeedback("Triage Rejected. Obvious root-cause incident fix was not resolved. Storage saturation requires log cleaning.");
    }
  };

  const handleMediumSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);

    const correctViolation = medViolationSelection === "direct_db";
    const correctIncident = medIncidentSelection === "cache_miss";

    if (correctViolation && correctIncident) {
      setSuccess(true);
      setFeedback("Pattern checks cleared! Direct Database exposure is a major security vulnerability, and cache invalidation stampedes explain the Gateway timeouts.");
    } else if (!correctViolation) {
      setSuccess(false);
      setFeedback("Triage Rejected. The selected pattern violation is incorrect. Direct public DB access breaks standard isolation tiers.");
    } else {
      setSuccess(false);
      setFeedback("Triage Rejected. Cache invalidation rate spikes (98% miss) explain database query timeouts, not client-side memory leaks.");
    }
  };

  const handleHardSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);

    const correctArchitecture = hardLb === "nginx" && hardCache === "redis" && hardBroker === "rabbitmq";
    const correctIncident = hardIncidentSelection === "db_deadlock"; // avoids the CPU scaling red herring

    if (correctArchitecture && correctIncident) {
      setSuccess(true);
      setFeedback("System Redesign Approved! Integrating NGINX + Redis + RabbitMQ resolves request buffering, and releasing database transaction deadlocks safely fixes the CPU load anomaly.");
    } else if (!correctArchitecture) {
      setSuccess(false);
      setFeedback("System Rejected. Redesigned stack has routing gaps. Load Balancing (NGINX), Caching (Redis), and Broker (RabbitMQ) layers are required.");
    } else {
      setSuccess(false);
      setFeedback("System Rejected. Incident diagnostics failed. (Hint: CPU load is a side-effect symptom of transactional deadlocks holding threads open, scaling CPU will not clear locked tables).");
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setSuccess(false);
    setFeedback("");
    setEasyOrder(["", "", ""]);
    setEasyIncidentSelection("");
    setMedViolationSelection("");
    setMedIncidentSelection("");
    setHardLb("");
    setHardCache("");
    setHardBroker("");
    setHardIncidentSelection("");
  };

  return (
    <div className="flex-1 flex overflow-hidden font-body-md">
      {/* LEFT PANEL: ARCHITECTURE WORKSPACE */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-surface-container-lowest">
        
        {/* Header */}
        <div className="mb-6">
          <h2 className="font-headline-md text-[20px] font-bold text-on-surface">System Architecture & Incident Triage</h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant">Design reliable system tiers, verify query routing steps, and fix staging outages.</p>
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
              {success ? "Architecture Approved" : "Architecture Refused"}
            </h3>

            <p className="font-body-sm text-[13px] text-on-surface-variant leading-relaxed p-4 bg-surface-container-low rounded-xl border border-outline-variant/20">
              {feedback}
            </p>

            <div className="flex gap-4 w-full justify-center mt-2">
              <button
                onClick={handleReset}
                className="py-2.5 px-6 border border-outline font-label-md text-label-md text-on-surface rounded-lg hover:bg-surface-container transition-colors"
              >
                {success ? "Revise Design" : "Try Again"}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col gap-6">
            
            {/* EASY WORKSPACE: Linear routing order + obvious root cause */}
            {difficulty === "easy" && (
              <div className="flex flex-col gap-5">
                {/* Visual order */}
                <div className="bg-surface-container border border-outline-variant/20 p-5 rounded-2xl">
                  <h3 className="font-label-sm text-xs font-bold text-on-surface mb-3 uppercase tracking-wider">Connect Request Flow (Linear Path)</h3>
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    {/* Node 1 */}
                    <div className="flex-1 min-w-[120px] flex flex-col gap-2">
                      <span className="font-label-sm text-[10px] text-outline">Step 1 (Source):</span>
                      <select
                        value={easyOrder[0]}
                        onChange={(e) => setEasyOrder([e.target.value, easyOrder[1], easyOrder[2]])}
                        className="bg-surface border border-outline-variant rounded p-2 text-xs text-on-surface"
                      >
                        <option value="">Select...</option>
                        <option value="client">Client Browser</option>
                        <option value="load_balancer">Load Balancer</option>
                        <option value="web_server">Web Server</option>
                      </select>
                    </div>

                    <span className="material-symbols-outlined text-outline">arrow_forward</span>

                    {/* Node 2 */}
                    <div className="flex-1 min-w-[120px] flex flex-col gap-2">
                      <span className="font-label-sm text-[10px] text-outline">Step 2 (Proxy):</span>
                      <select
                        value={easyOrder[1]}
                        onChange={(e) => setEasyOrder([easyOrder[0], e.target.value, easyOrder[2]])}
                        className="bg-surface border border-outline-variant rounded p-2 text-xs text-on-surface"
                      >
                        <option value="">Select...</option>
                        <option value="client">Client Browser</option>
                        <option value="load_balancer">Load Balancer</option>
                        <option value="web_server">Web Server</option>
                      </select>
                    </div>

                    <span className="material-symbols-outlined text-outline">arrow_forward</span>

                    {/* Node 3 */}
                    <div className="flex-1 min-w-[120px] flex flex-col gap-2">
                      <span className="font-label-sm text-[10px] text-outline">Step 3 (Target):</span>
                      <select
                        value={easyOrder[2]}
                        onChange={(e) => setEasyOrder([easyOrder[0], easyOrder[1], e.target.value])}
                        className="bg-surface border border-outline-variant rounded p-2 text-xs text-on-surface"
                      >
                        <option value="">Select...</option>
                        <option value="client">Client Browser</option>
                        <option value="load_balancer">Load Balancer</option>
                        <option value="web_server">Web Server</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Incident report */}
                <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider">Incident Report #101</h3>
                    <span className="text-[9px] bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded uppercase">Storage Saturation</span>
                  </div>
                  <p className="font-body-sm text-[12px] text-on-surface-variant leading-relaxed mb-4">
                    <strong>Symptom:</strong> API Node server fails to append new records. Logs report: `ENOSPC: no space left on device, write /var/log/api.log`.
                  </p>
                  
                  <div className="flex flex-col gap-2">
                    <span className="font-label-sm text-[11px] text-outline uppercase font-bold">Select Triage Patch:</span>
                    {[
                      { id: "clean_logs", label: "Trigger logrotate to compress and clean local server log files." },
                      { id: "reboot", label: "Reboot physical server node instances in AWS pool." },
                      { id: "database", label: "Migrate relational database indexes to cluster replicas." }
                    ].map((opt) => (
                      <label key={opt.id} className="flex items-center gap-3 bg-surface-container-low border border-outline-variant/10 rounded-xl p-3 cursor-pointer hover:bg-surface-container transition-colors">
                        <input
                          type="radio"
                          name="easyIncident"
                          value={opt.id}
                          checked={easyIncidentSelection === opt.id}
                          onChange={(e) => setEasyIncidentSelection(e.target.value)}
                          className="accent-primary"
                        />
                        <span className="font-body-sm text-xs text-on-surface-variant">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleEasySubmit}
                  disabled={!easyOrder.every(x => x !== "") || !easyIncidentSelection}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container disabled:bg-outline-variant/30 disabled:cursor-not-allowed transition-all"
                >
                  Verify Staging Design
                </button>
              </div>
            )}

            {/* MEDIUM WORKSPACE: Spot pattern violation + 5-step branching + 2 possible causes */}
            {difficulty === "medium" && (
              <div className="flex flex-col gap-5">
                <div className="grid grid-cols-2 gap-4">
                  {/* Pattern violation */}
                  <div className="bg-surface-container border border-outline-variant/20 p-5 rounded-2xl flex flex-col gap-3">
                    <h3 className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider">Spot Architecture Flaw</h3>
                    
                    {/* Visual mockup of bad architecture diagram */}
                    <div className="bg-surface border border-outline-variant/10 rounded-xl p-3 font-mono text-[9px] text-outline leading-tight flex flex-col gap-2">
                      <div className="flex justify-between items-center border-b border-outline-variant/15 pb-1">
                        <span>[Browser Client]</span>
                        <span>{"===>"}</span>
                        <span>[Load Balancer]</span>
                      </div>
                      <div className="flex justify-between items-center border-b border-outline-variant/15 pb-1">
                        <span>[Load Balancer]</span>
                        <span>{"===>"}</span>
                        <span>[Node API Server]</span>
                      </div>
                      <div className="flex justify-between items-center bg-red-50 border border-red-200 text-red-800 rounded p-1.5 font-bold">
                        <span>[Browser Client]</span>
                        <span>{"===(Public Port 5432)===>"}</span>
                        <span>[Postgres Database]</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 mt-2">
                      <span className="font-label-sm text-[10px] text-outline font-semibold">Select Violation Reason:</span>
                      <select
                        value={medViolationSelection}
                        onChange={(e) => setMedViolationSelection(e.target.value)}
                        className="bg-surface border border-outline-variant rounded p-2 text-xs text-on-surface outline-none"
                      >
                        <option value="">Choose flaw reason...</option>
                        <option value="direct_db">Direct Database Exposure (Client connects to Postgres directly without server proxy)</option>
                        <option value="lb_missing">Missing SSL on API Server node cluster</option>
                        <option value="port_mismatch">Port mapping limits mismatch on docker layer</option>
                      </select>
                    </div>
                  </div>

                  {/* Incident report with 2 causes */}
                  <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm flex flex-col gap-3">
                    <h3 className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider">Incident Report #102</h3>
                    <p className="font-body-sm text-[11px] text-on-surface-variant leading-relaxed">
                      <strong>Symptom:</strong> Staging dashboard shows HTTP 504 Gateway Timeout rates spikes to 64% during peak morning hours.
                    </p>

                    <div className="flex flex-col gap-2 mt-2">
                      <span className="font-label-sm text-[10px] text-outline font-semibold">Select Root Cause:</span>
                      {[
                        { id: "cache_miss", label: "Cache stampede: Redis invalidation script cleared user sessions triggering expensive db lookups." },
                        { id: "memory_leak", label: "Staging memory leak in CSS animation renders client browsers lgy." }
                      ].map((opt) => (
                        <label key={opt.id} className="flex items-center gap-2 bg-surface-container-low border border-outline-variant/10 rounded-xl p-2.5 cursor-pointer hover:bg-surface-container transition-colors">
                          <input
                            type="radio"
                            name="medIncident"
                            value={opt.id}
                            checked={medIncidentSelection === opt.id}
                            onChange={(e) => setMedIncidentSelection(e.target.value)}
                            className="accent-primary"
                          />
                          <span className="font-body-sm text-[11px] text-on-surface-variant">{opt.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleMediumSubmit}
                  disabled={!medViolationSelection || !medIncidentSelection}
                  className="self-end py-2.5 px-6 bg-primary text-white font-label-md text-xs rounded-lg shadow-md hover:bg-primary-container transition-all"
                >
                  Triage Incident & Flaws
                </button>
              </div>
            )}

            {/* HARD WORKSPACE: Redesign stack canvas + conditional flows + 3 causes with trap */}
            {difficulty === "hard" && (
              <div className="flex flex-col gap-5">
                <div className="grid grid-cols-2 gap-4">
                  
                  {/* System redesign selectors */}
                  <div className="bg-surface-container border border-outline-variant/20 p-5 rounded-2xl flex flex-col gap-4">
                    <h3 className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider">Redesign Architecture Stack</h3>
                    
                    {/* Layer 1: LB */}
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">1. Edge Proxy Layer</label>
                      <select
                        value={hardLb}
                        onChange={(e) => setHardLb(e.target.value)}
                        className="bg-surface border border-outline-variant rounded p-1.5 text-xs text-on-surface outline-none"
                      >
                        <option value="">Select Edge proxy...</option>
                        <option value="nginx">NGINX Edge Load Balancer</option>
                        <option value="cors">CORS Origin middleware</option>
                      </select>
                    </div>

                    {/* Layer 2: Cache */}
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">2. Latency Cache Tier</label>
                      <select
                        value={hardCache}
                        onChange={(e) => setHardCache(e.target.value)}
                        className="bg-surface border border-outline-variant rounded p-1.5 text-xs text-on-surface outline-none"
                      >
                        <option value="">Select Caching layer...</option>
                        <option value="redis">Redis Cluster Cache</option>
                        <option value="s3">AWS S3 Raw Assets Storage</option>
                      </select>
                    </div>

                    {/* Layer 3: Broker */}
                    <div className="flex flex-col gap-1">
                      <label className="font-label-sm text-[10px] text-outline uppercase font-bold">3. Message Broker</label>
                      <select
                        value={hardBroker}
                        onChange={(e) => setHardBroker(e.target.value)}
                        className="bg-surface border border-outline-variant rounded p-1.5 text-xs text-on-surface outline-none"
                      >
                        <option value="">Select Broker...</option>
                        <option value="rabbitmq">RabbitMQ Queue Manager</option>
                        <option value="grpc">gRPC Protocol Buffer serializer</option>
                      </select>
                    </div>
                  </div>

                  {/* Incident Report with 3 causes + Red Herring */}
                  <div className="bg-surface border border-outline-variant/30 rounded-2xl p-5 shadow-sm flex flex-col gap-3">
                    <div className="flex justify-between items-center">
                      <h3 className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider">Outage Report #103</h3>
                      <span className="text-[9px] bg-error-container text-on-error-container font-bold px-2 py-0.5 rounded uppercase">CRITICAL FAULT</span>
                    </div>
                    <p className="font-body-sm text-[11px] text-on-surface-variant leading-relaxed">
                      <strong>Symptom:</strong> Checkout service hangs indefinitely. CPU usage spikes to 100% on API container. Memory allocation stable. Network bandwidth normal.
                    </p>

                    <div className="flex flex-col gap-2 mt-2">
                      <span className="font-label-sm text-[10px] text-outline font-semibold">Select Root Cause Triage:</span>
                      {[
                        { id: "scale_cpu", label: "Red Herring: Autoscale CPU count on the Checkout service containers immediately." },
                        { id: "db_deadlock", label: "Patch: release database transaction deadlocks holding open threads on transaction rows." },
                        { id: "clear_cache", label: "Patch: Flush memory buffers on the caching microservices cluster." }
                      ].map((opt) => (
                        <label key={opt.id} className="flex items-start gap-2 bg-surface-container-low border border-outline-variant/10 rounded-xl p-2 cursor-pointer hover:bg-surface-container transition-colors">
                          <input
                            type="radio"
                            name="hardIncident"
                            value={opt.id}
                            checked={hardIncidentSelection === opt.id}
                            onChange={(e) => setHardIncidentSelection(e.target.value)}
                            className="accent-primary mt-1"
                          />
                          <span className="font-body-sm text-[11px] text-on-surface-variant">{opt.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleHardSubmit}
                  disabled={!hardLb || !hardCache || !hardBroker || !hardIncidentSelection}
                  className="self-end py-2.5 px-6 bg-error text-white font-label-md text-xs rounded-lg shadow-md hover:bg-error-container hover:text-on-error-container transition-all font-semibold"
                >
                  Deploy Redesigned Clusters
                </button>
              </div>
            )}

          </div>
        )}
      </div>

      {/* RIGHT PANEL: ROUTING SCHEMATIC */}
      <div className="w-[300px] border-l border-outline-variant bg-surface flex flex-col p-6 shadow-sm overflow-y-auto">
        <h3 className="font-headline-md text-[16px] font-bold text-on-surface mb-4 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[20px] text-primary">lan</span>
          Routing Schema
        </h3>

        <div className="flex flex-col gap-4 font-body-sm text-[12px] text-on-surface-variant leading-relaxed">
          <div className="bg-surface-container border border-outline-variant/15 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Gateway Proxy Tier</h4>
            <p>Load balancers distribute external client HTTP traffic to private API server subnets securely.</p>
          </div>

          <div className="bg-surface-container border border-outline-variant/15 p-4 rounded-xl">
            <h4 className="font-label-sm text-xs font-bold text-on-surface mb-1 uppercase tracking-wider">Transaction Deadlock</h4>
            <p>Deadlocks happen when two queries block each other by holding row locks. This pins threads, driving CPU use up to 100%.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
