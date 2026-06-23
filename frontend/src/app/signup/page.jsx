"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) {
      alert("Please fill in all the registration fields.");
      return;
    }
    // Simulate signup success and route to onboarding
    router.push("/onboarding");
  };

  return (
    <div className="bg-surface-container-lowest text-on-surface min-h-screen w-screen flex flex-col items-center justify-center font-body-md antialiased p-6">
      
      {/* Brand logo header */}
      <div 
        className="flex items-center gap-2 group cursor-pointer mb-8" 
        onClick={() => router.push("/")}
      >
        <div className="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center">
          <span className="material-symbols-outlined text-primary text-xl">genetics</span>
        </div>
        <div className="font-headline-md text-[20px] font-bold tracking-tight">
          Career<span className="text-primary ml-0.5">DNA</span>
        </div>
      </div>

      {/* Card panel */}
      <div className="w-full max-w-[420px] bg-surface border border-outline-variant/30 p-8 rounded-2xl shadow-xl flex flex-col gap-6">
        <div className="text-center flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-full bg-primary-container/10 flex items-center justify-center text-primary mb-1">
            <span className="material-symbols-outlined text-[28px]">person_add</span>
          </div>
          <h2 className="font-headline-md text-[22px] font-bold text-on-surface leading-none">
            Create your account
          </h2>
          <p className="font-body-sm text-[13px] text-on-surface-variant max-w-xs">
            Join Career DNA to begin your tech career discovery.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="font-label-sm text-[11px] text-outline font-bold uppercase">Full Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-label-sm text-[11px] text-outline font-bold uppercase">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-label-sm text-[11px] text-outline font-bold uppercase">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="bg-surface border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary rounded-lg p-2.5 font-body-sm text-[13px] outline-none transition-all"
            />
          </div>

          <button
            type="submit"
            className="w-full mt-2 py-3 bg-primary text-white font-label-md text-label-md rounded-lg shadow-md hover:bg-primary-container hover:scale-[1.01] active:scale-[0.99] transition-all font-semibold"
          >
            Create Account
          </button>
        </form>

        <div className="border-t border-outline-variant/20 pt-4 text-center">
          <button
            onClick={() => router.push("/login")}
            className="font-body-sm text-xs text-primary hover:underline font-semibold"
          >
            Already have an account? Sign in
          </button>
        </div>
      </div>
    </div>
  );
}
