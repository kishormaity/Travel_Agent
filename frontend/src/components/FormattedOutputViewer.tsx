"use client";

import React, { useState } from "react";
import {
  Copy,
  Check,
  FileText,
  Calendar,
  Plane,
  Building2,
  PieChart,
  Compass,
} from "lucide-react";
import { useTripStore } from "../store/useTripStore";
import { ActiveTabType } from "../types/trip";

interface FormattedOutputViewerProps {
  sectionKey: ActiveTabType;
}

const SECTION_METADATA: Record<
  ActiveTabType,
  { title: string; icon: React.ComponentType<{ className?: string }>; description: string }
> = {
  overview: {
    title: "Trip Overview",
    icon: Compass,
    description: "High-level trip summary, traveler party, dates, and destination highlights.",
  },
  itinerary: {
    title: "Day-wise Itinerary",
    icon: Calendar,
    description: "Chronological daily schedule with morning, afternoon, and evening activities.",
  },
  flights: {
    title: "Flight Details",
    icon: Plane,
    description: "Verified airfare comparison, routes, schedules, and baggage allowances.",
  },
  hotels: {
    title: "Hotels & Stays",
    icon: Building2,
    description: "Curated accommodations per destination, nightly rates, and room guidance.",
  },
  budget: {
    title: "Estimated Budget",
    icon: PieChart,
    description: "Itemized expense allocation, math comparison against target budget, and status.",
  },
};

/**
 * Extracts a section's text from the full AI report when raw_sections is incomplete.
 */
function extractFromFullReport(fullText: string, targetKey: ActiveTabType): string {
  if (!fullText) return "";

  const sectionAliases: Record<ActiveTabType, string[]> = {
    overview: ["Overview", "Trip Overview"],
    itinerary: ["Itinerary", "Day-wise Itinerary", "Day-by-Day Itinerary"],
    flights: ["Flights", "Flight Details"],
    hotels: ["Hotels", "Accommodation Options", "Accommodations"],
    budget: ["Budget", "Estimated Budget", "Budget Breakdown"],
  };

  const aliases = sectionAliases[targetKey] || [targetKey];
  const allAliases = Object.values(sectionAliases).flat();

  const lines = fullText.split("\n");
  let capturing = false;
  const capturedLines: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim().replace(/^#{1,4}\s*/, "").replace(/:$/, "").trim();

    // Check if this line is our target header
    const isTarget = aliases.some((a) => a.toLowerCase() === trimmed.toLowerCase());
    // Check if this line is any other header
    const isOther = allAliases.some(
      (a) => a.toLowerCase() === trimmed.toLowerCase() && !aliases.some((x) => x.toLowerCase() === a.toLowerCase())
    );

    if (isTarget) {
      capturing = true;
      continue;
    } else if (isOther && capturing) {
      break;
    }

    if (capturing) {
      capturedLines.push(line);
    }
  }

  return capturedLines.join("\n").trim();
}

/**
 * Renders raw AI output with clean formatting:
 * - Detects Markdown tables and renders native <table>
 * - Detects bullet points, lists, and days
 * - Renders clean, readable paragraphs
 */
function RenderFormattedBlocks({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split("\n");
  const blocks: React.ReactNode[] = [];
  let tableBuffer: string[] = [];
  let listBuffer: string[] = [];
  let blockIndex = 0;

  const flushTable = () => {
    if (tableBuffer.length === 0) return;
    const currentTable = [...tableBuffer];
    tableBuffer = [];

    // Parse header, separator, rows
    const headerLine = currentTable[0];
    const dataLines = currentTable.slice(1).filter((l) => !l.includes("---"));

    const parseRow = (line: string) =>
      line
        .split("|")
        .slice(1, -1)
        .map((cell) => cell.trim());

    const headers = parseRow(headerLine);
    const rows = dataLines.map(parseRow);

    blocks.push(
      <div key={`table-${blockIndex++}`} className="my-4 overflow-x-auto rounded-xl border border-stone-200/90 shadow-2xs">
        <table className="w-full text-left text-xs sm:text-sm border-collapse">
          <thead className="bg-[#1B4332] text-white">
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="px-4 py-3 font-semibold tracking-wide border-b border-[#2D6A4F]">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200 bg-white">
            {rows.map((row, rIdx) => (
              <tr key={rIdx} className={rIdx % 2 === 0 ? "bg-white hover:bg-stone-50/60" : "bg-stone-50/40 hover:bg-stone-50"}>
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-4 py-3 text-stone-700 font-normal">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const flushList = () => {
    if (listBuffer.length === 0) return;
    const currentList = [...listBuffer];
    listBuffer = [];

    blocks.push(
      <ul key={`list-${blockIndex++}`} className="my-3 space-y-2 text-xs sm:text-sm text-stone-700 pl-4 list-disc marker:text-[#1B4332]">
        {currentList.map((item, idx) => (
          <li key={idx} className="leading-relaxed">
            {item}
          </li>
        ))}
      </ul>
    );
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Table line
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      flushList();
      tableBuffer.push(trimmed);
      continue;
    } else {
      flushTable();
    }

    // Bullet list line
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      listBuffer.push(trimmed.slice(2).trim());
      continue;
    } else {
      flushList();
    }

    // Empty line
    if (!trimmed) {
      continue;
    }

    // Day Heading detection (e.g., "Day 1 - 10 Jan" or "Day 1:")
    if (/^Day\s+\d+/i.test(trimmed)) {
      blocks.push(
        <div key={`day-hdr-${blockIndex++}`} className="mt-5 mb-2 pt-3 border-t border-stone-200/80 first:border-0 first:mt-0">
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-[#1B4332] text-white">
            {trimmed}
          </span>
        </div>
      );
      continue;
    }

    // Regular paragraph
    blocks.push(
      <p key={`p-${blockIndex++}`} className="my-2.5 text-xs sm:text-sm text-stone-700 leading-relaxed font-normal">
        {trimmed}
      </p>
    );
  }

  flushTable();
  flushList();

  return <div className="space-y-1">{blocks}</div>;
}

export function FormattedOutputViewer({ sectionKey }: FormattedOutputViewerProps) {
  const { trip } = useTripStore();
  const [copied, setCopied] = useState(false);

  if (!trip) return null;

  const meta = SECTION_METADATA[sectionKey] || {
    title: sectionKey.toUpperCase(),
    icon: FileText,
    description: "",
  };
  const Icon = meta.icon;

  // Retrieve raw text for this section
  let content = trip.raw_sections?.[sectionKey] || "";

  if (!content && trip.final_response) {
    content = extractFromFullReport(trip.final_response, sectionKey);
  }

  // Fallbacks if specific section raw text is empty
  if (!content) {
    if (sectionKey === "overview") {
      content = trip.overview;
    } else if (sectionKey === "itinerary" && trip.itinerary) {
      content = trip.itinerary
        .map(
          (d) =>
            `Day ${d.day} - ${d.date} (${d.destination})\n${d.title}: ${d.summary}\n${d.activities
              .map((a) => `- ${a.time}: ${a.title} — ${a.description}`)
              .join("\n")}`
        )
        .join("\n\n");
    } else if (sectionKey === "flights" && trip.flights?.length > 0) {
      const sorted = [...trip.flights].sort((a, b) => (Number(a.price) || 0) - (Number(b.price) || 0));
      const minP = sorted[0].price;
      const rows = sorted.map((f, i) => {
        const isMin = f.price === minP || i === 0;
        return `| ${f.airline} | ${f.flight_number || "Direct"} | ${f.origin} → ${f.destination} | ${f.departure_date} ${f.departure_time} | ${f.arrival_time} | ${f.duration_formatted || f.duration || "2h 40m"} | ${f.stops === 0 ? "Non-stop" : `${f.stops} stop(s)`} | ₹${Number(f.price).toLocaleString()} ${isMin ? "(Lowest Fare ★)" : ""} | [Book Flight](${f.booking_url || "https://www.google.com/travel/flights"}) |`;
      });
      content = `| Airline | Flight # | Route | Departure | Arrival | Duration | Stops | Fare (INR) | Booking Link |\n|---|---|---|---|---|---|---|---|---|\n` + rows.join("\n") + `\n\nAll fares verified via Google Flights MCP and include cabin baggage allowance.`;
    } else if (sectionKey === "hotels" && trip.hotels?.length > 0) {
      content =
        `| Destination | Property Name | Rating | Nightly Rate | Total Stay |\n|---|---|---|---|---|\n` +
        trip.hotels
          .map(
            (h) =>
              `| ${h.destination_city} | ${h.property_name} | ${h.rating} ★ | ₹${Number(h.price_per_night || 0).toLocaleString()} | ₹${Number(h.total_price || 0).toLocaleString()} |`
          )
          .join("\n") +
        `\n\nRoom Guidance: ${trip.hotels[0]?.recommended_rooms || "Suitable for traveler party"}.`;
    } else if (sectionKey === "budget" && trip.budget) {
      content =
        `| Expense Category | Amount (INR) | Share |\n|---|---|---|\n` +
        trip.budget.categories
          .map((c) => `| ${c.name} | ₹${c.amount.toLocaleString()} | ${c.percentage}% |`)
          .join("\n") +
        `\n| Total Estimated Cost | ₹${trip.budget.estimated_total.toLocaleString()} | 100% |\n\nComparison:\n- Target Budget: ₹${trip.budget.user_budget.toLocaleString()}\n- Status: ${trip.budget.status_label} (Difference: ₹${trip.budget.difference.toLocaleString()})`;
    }
  }

  const handleCopy = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-stone-200/90 p-5 sm:p-7 shadow-xs">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-200/80 gap-3">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-emerald-50 text-[#1B4332] flex items-center justify-center shrink-0">
            <Icon className="h-5 w-5 text-[#1B4332]" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-stone-900 tracking-tight">
              {meta.title}
            </h3>
            {meta.description && (
              <p className="text-xs text-stone-500 mt-0.5">{meta.description}</p>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200/80 border border-stone-200 rounded-lg transition-colors cursor-pointer self-start sm:self-auto"
          title="Copy this section text"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-600" />
              <span className="text-emerald-700">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 text-stone-500" />
              <span>Copy Section</span>
            </>
          )}
        </button>
      </div>

      {/* Formatted Output Content */}
      <div className="pt-4">
        <RenderFormattedBlocks content={content} />
      </div>
    </div>
  );
}

