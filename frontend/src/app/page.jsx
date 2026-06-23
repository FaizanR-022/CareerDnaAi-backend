"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function Home() {
  // Simple scroll effect for navbar

  return (
    <>
      {/* Section 1: TopNavBar */}
      <header
        className="fixed top-0 left-0 w-full z-50 h-20 bg-surface/90 backdrop-blur-md border-b border-outline-variant/20 flex items-center transition-all duration-300"
        id="navbar"
      >
        <div className="max-w-container-max mx-auto w-full px-margin-mobile md:px-margin-desktop flex justify-between items-center">

          {/* Left: Logo */}
          <div className="flex-1 flex justify-start">
            <div className="flex items-center gap-2 cursor-pointer group">
              <div className="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-xl group-hover:scale-110 transition-transform duration-300">
                  genetics
                </span>
              </div>
              <div className="font-headline-md text-[22px] font-bold text-on-surface flex items-center tracking-tight">
                Career<span className="text-primary ml-1">DNA</span>
              </div>
            </div>
          </div>

          {/* Center: Navigation */}
          <nav className="hidden md:flex items-center justify-center gap-10 flex-none">
            <a
              className="text-sm text-on-surface font-semibold hover:text-primary transition-colors duration-200"
              href="#"
            >
              Features
            </a>
            <a
              className="text-sm text-on-surface font-semibold hover:text-primary transition-colors duration-200"
              href="#"
            >
              How it Works
            </a>
            <a
              className="text-sm text-on-surface font-semibold hover:text-primary transition-colors duration-200"
              href="#"
            >
              Pricing
            </a>
          </nav>

          {/* Right: Actions */}
          <div className="flex-1 flex justify-end">
            <Link href="/login">
              <button className="px-6 py-2 rounded-full border border-primary text-primary text-sm font-semibold hover:bg-primary/5 transition-colors duration-200 bg-transparent">
                Sign In
              </button>
            </Link>
          </div>

        </div>
      </header>

      <main>
        {/* Section 2: Hero Section */}
        <section className="relative pt-24 pb-16 md:pt-32 md:pb-24 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="flex flex-col items-start gap-6 z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container/20 text-primary font-label-sm text-label-sm border border-primary/20">
                <span className="material-symbols-outlined text-sm">auto_awesome</span>
                AI-Powered Career Discovery
              </div>
              <h1 className="font-headline-lg-mobile md:font-headline-xl text-headline-lg-mobile md:text-headline-xl text-on-background tracking-tight">
                Decode Your Tech Future with{" "}
                <span className="text-primary">Career DNA AI</span>
              </h1>
              <p className="font-body-lg text-body-lg text-on-surface-variant max-w-xl">
                Leverage artificial intelligence to discover the exact tech role that
                perfectly matches your skills, personality, and ambitions.
              </p>
              <div className="flex flex-wrap items-center gap-4 mt-2">
                {/* Linked Main Button to Onboarding */}
                <Link href="/onboarding">
                  <button className="px-6 py-3 rounded-xl bg-primary text-on-primary font-label-md text-label-md shadow-md hover:shadow-lg transition-all duration-300 flex items-center gap-2">
                    Discover Your Path
                    <span className="material-symbols-outlined text-sm">
                      arrow_forward
                    </span>
                  </button>
                </Link>
                <button className="px-6 py-3 rounded-xl border border-outline-variant text-on-surface font-label-md text-label-md hover:bg-surface-variant transition-all duration-300">
                  Watch Demo
                </button>
              </div>
              {/* Updated Stats */}
              <div className="mt-8 flex items-center gap-6 text-on-surface-variant font-label-md text-label-md">
                <span className="text-on-surface"><strong className="text-on-surface">50k+</strong> assessments</span>
                <span className="w-px h-4 bg-outline-variant"></span>
                <span className="text-on-surface"><strong className="text-on-surface">98%</strong> match accuracy</span>
              </div>
            </div>
            <div className="relative z-10 hidden md:block">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl bg-surface">
                <img
                  alt="Career DNA AI Platform Illustration"
                  className="w-full h-auto object-cover"
                  src="/hero-dna.jpg"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Explore Domains */}
        <section className="py-16 md:py-24 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <p className="text-tertiary font-label-md uppercase tracking-wider mb-2">CORE FEATURE</p>
            <h2 className="font-headline-lg text-headline-lg text-on-surface mb-4 tracking-tight">
              Explore Your Potential <span className="text-primary">Career Domains</span>
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Five high-impact tech roles, decoded for your unique strengths.
            </p>
          </div>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* PM */}
            <div className="bg-surface rounded-2xl p-8 shadow-sm border border-outline-variant/10 hover:shadow-md transition-all duration-300">
              <div className="w-12 h-12 rounded-lg bg-surface-variant flex items-center justify-center text-on-surface mb-6">
                <span className="material-symbols-outlined text-2xl">target</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface mb-3">Product Manager</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">
                Lead vision, strategy and execution. Bridge users, business and engineering to ship products that matter.
              </p>
              <Link className="inline-flex items-center gap-1 font-label-md text-label-md text-tertiary-container hover:text-tertiary transition-colors" href="/simulation/pm">
                View Role <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Link>
            </div>

            {/* SQA */}
            <div className="bg-surface rounded-2xl p-8 shadow-sm border border-outline-variant/10 hover:shadow-md transition-all duration-300">
              <div className="w-12 h-12 rounded-lg bg-surface-variant flex items-center justify-center text-on-surface mb-6">
                <span className="material-symbols-outlined text-2xl">verified_user</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface mb-3">SQA Engineer</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">
                Guard product quality. Design test strategies, automate flows and catch issues before users do.
              </p>
              <Link className="inline-flex items-center gap-1 font-label-md text-label-md text-tertiary-container hover:text-tertiary transition-colors" href="/simulation/sqa">
                View Role <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Link>
            </div>

            {/* Data Analyst */}
            <div className="bg-surface rounded-2xl p-8 shadow-sm border border-outline-variant/10 hover:shadow-md transition-all duration-300">
              <div className="w-12 h-12 rounded-lg bg-surface-variant flex items-center justify-center text-on-surface mb-6">
                <span className="material-symbols-outlined text-2xl">bar_chart</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface mb-3">Data Analyst</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">
                Turn raw data into clear stories. Drive decisions with dashboards, metrics and deep insight.
              </p>
              <Link className="inline-flex items-center gap-1 font-label-md text-label-md text-tertiary-container hover:text-tertiary transition-colors" href="/simulation/da">
                View Role <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Link>
            </div>

            {/* Frontend Engineer - Centered Row 2 */}
            <div className="lg:col-start-1 bg-surface rounded-2xl p-8 shadow-sm border border-outline-variant/10 hover:shadow-md transition-all duration-300">
              <div className="w-12 h-12 rounded-lg bg-surface-variant flex items-center justify-center text-on-surface mb-6">
                <span className="material-symbols-outlined text-2xl">web</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface mb-3">Frontend Engineer</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">
                Craft fast, beautiful interfaces. Translate design into responsive, accessible web experiences.
              </p>
              <Link className="inline-flex items-center gap-1 font-label-md text-label-md text-tertiary-container hover:text-tertiary transition-colors" href="#">
                View Role <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Link>
            </div>

            {/* Backend Engineer - Centered Row 2 */}
            <div className="bg-surface rounded-2xl p-8 shadow-sm border border-outline-variant/10 hover:shadow-md transition-all duration-300">
              <div className="w-12 h-12 rounded-lg bg-surface-variant flex items-center justify-center text-on-surface mb-6">
                <span className="material-symbols-outlined text-2xl">dns</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface mb-3">Backend Engineer</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">
                Build the engine behind the product. APIs, databases and systems that scale reliably.
              </p>
              <Link className="inline-flex items-center gap-1 font-label-md text-label-md text-tertiary-container hover:text-tertiary transition-colors" href="#">
                View Role <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Section 4: Footer */}
      <footer className="w-full py-12 px-margin-desktop bg-surface-container-low mt-20">
        <div className="max-w-container-max mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="font-headline-md text-headline-md font-bold text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined">science</span>
              Career DNA
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              © 2024 Career DNA AI. All rights reserved.
            </p>
          </div>
          <nav className="flex flex-wrap justify-center gap-8">
            <a className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors" href="#">Privacy Policy</a>
            <a className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors" href="#">Terms of Service</a>
            <a className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors" href="#">Contact Us</a>
          </nav>
        </div>
      </footer>
    </>
  );
}