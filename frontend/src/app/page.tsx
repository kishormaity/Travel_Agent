"use client";

import React from "react";
import { Navbar } from "../components/Navbar";
import { HeroPlanner } from "../components/HeroPlanner";
import { TripWorkspace } from "../components/TripWorkspace";
import { ProgressModal } from "../components/ProgressModal";
import { Compass, ShieldCheck } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#FAF9F6] text-stone-900 flex flex-col font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Top Navigation */}
      <Navbar />

      {/* Hero & Trip Planning Form */}
      <HeroPlanner />

      {/* Generated Trip Workspace (Dynamic Tabs: Overview, Itinerary, Flights, Hotels, Budget, Map) */}
      <TripWorkspace />

      {/* Real-time Agent Progress Overlay */}
      <ProgressModal />

      {/* Clean, Minimal Footer */}
      <footer className="mt-auto border-t border-stone-200/80 bg-white py-8 text-xs text-stone-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-lg bg-[#1B4332] text-white flex items-center justify-center">
              <Compass className="h-3.5 w-3.5" />
            </div>
            <span className="font-semibold text-stone-800">Wayfarer</span>
            <span>•</span>
            <span>AI Travel Agent Platform</span>
          </div>

          <div className="flex items-center gap-4 text-stone-400">
            <span className="flex items-center gap-1 text-emerald-800 font-medium">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              StateGraph DAG Orchestration
            </span>
            <span>•</span>
            <span>HasData Google Hotels MCP</span>
            <span>•</span>
            <span>Groq LLM</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
