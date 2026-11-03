"use client";

import React from "react";
import { Loader2, CheckCircle2, AlertCircle, Compass } from "lucide-react";
import { useTripStore } from "../store/useTripStore";

export function ProgressModal() {
  const { isLoading, currentProgressMessage, progressEvents } = useTripStore();

  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-stone-200/90 shadow-2xl p-6 sm:p-8 max-w-lg w-full space-y-5 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 pb-3 border-b border-stone-100">
          <div className="h-10 w-10 rounded-xl bg-emerald-50 text-[#1B4332] flex items-center justify-center">
            <Compass className="h-5 w-5 animate-spin" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-stone-900">
              Wayfarer Agent Orchestration
            </h3>
            <p className="text-xs text-stone-500">
              Coordinating LangGraph DAG tasks & Remote MCP tools
            </p>
          </div>
        </div>

        {/* Current task marquee */}
        <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200/60 flex items-center gap-2.5 text-xs text-emerald-950 font-medium">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-700 shrink-0" />
          <span className="truncate">{currentProgressMessage || "Executing planner DAG..."}</span>
        </div>

        {/* Task history feed */}
        <div className="space-y-2 max-h-56 overflow-y-auto pr-1 text-xs">
          {progressEvents.map((evt, idx) => (
            <div
              key={idx}
              className="flex items-start justify-between gap-2 p-2 rounded-lg bg-stone-50 border border-stone-100 text-stone-700"
            >
              <div className="flex items-center gap-2 truncate">
                {evt.status === "completed" ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                ) : (
                  <Loader2 className="h-3.5 w-3.5 text-stone-400 animate-spin shrink-0" />
                )}
                <span className="truncate">{evt.description}</span>
              </div>
              {evt.execution_time && (
                <span className="text-[10px] text-stone-400 shrink-0 font-mono">
                  {evt.execution_time.toFixed(1)}s
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

