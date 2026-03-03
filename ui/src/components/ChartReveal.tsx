import { useState, useEffect } from "react";
import { Sparkles, Sun, Moon, Star, Hash, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { BirthChart } from "@/contexts/UserContext";

// ---------------------------------------------------------------------------
// Chart row config
// ---------------------------------------------------------------------------
type ChartRow = {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
};

function getRows(chart: BirthChart): ChartRow[] {
  return [
    {
      icon: <Sun size={18} />,
      label: "Sun Sign",
      value: chart.sun_sign,
      color: "text-amber-500",
    },
    {
      icon: <Moon size={18} />,
      label: "Moon Sign",
      value: chart.moon_sign,
      color: "text-blue-400",
    },
    {
      icon: <Star size={18} />,
      label: "Nakshatra",
      value: chart.nakshatra,
      color: "text-violet-400",
    },
    {
      icon: <Hash size={18} />,
      label: "Birth Number",
      value: chart.birth_number,
      color: "text-emerald-500",
    },
    {
      icon: <Hash size={18} />,
      label: "Destiny Number",
      value: chart.destiny_number,
      color: "text-rose-400",
    },
  ];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function ChartReveal({
  chart,
  userName,
  onComplete,
}: {
  chart: BirthChart;
  userName: string;
  onComplete: () => void;
}) {
  const [revealIndex, setRevealIndex] = useState(-1); // -1 = header animating
  const [showCTA, setShowCTA] = useState(false);
  const rows = getRows(chart);

  const hasPlanets = chart.planetary_positions && Object.keys(chart.planetary_positions).length > 0;
  const hasConjunctions = chart.conjunctions && chart.conjunctions.length > 0;
  
  const totalRevealItems = rows.length + (hasPlanets ? 1 : 0) + (hasConjunctions ? 1 : 0);

  // Sequentially reveal each row
  useEffect(() => {
    // Start with a brief pause for the header
    const headerTimer = setTimeout(() => setRevealIndex(0), 600);
    return () => clearTimeout(headerTimer);
  }, []);

  useEffect(() => {
    if (revealIndex >= 0 && revealIndex < totalRevealItems) {
      const timer = setTimeout(() => setRevealIndex((i) => i + 1), 400);
      return () => clearTimeout(timer);
    }
    if (revealIndex >= totalRevealItems && totalRevealItems > 0) {
      const timer = setTimeout(() => setShowCTA(true), 500);
      return () => clearTimeout(timer);
    }
  }, [revealIndex, totalRevealItems]);

  const planetIcons: Record<string, string> = {
    Sun: "☉", Moon: "☽", Mars: "♂", Mercury: "☿",
    Jupiter: "♃", Venus: "♀", Saturn: "♄", Rahu: "☊", Ketu: "☋",
  };

  return (
    <div className="h-screen w-full flex flex-col items-center justify-center bg-white dark:bg-zinc-900 font-sans px-4 overflow-y-auto py-12">
      <div className="w-full max-w-sm space-y-8 my-auto">

        {/* Header */}
        <div className="text-center space-y-3 animate-in fade-in zoom-in-95 duration-500">
          <div className="w-14 h-14 bg-gradient-to-br from-indigo-600 to-violet-700 rounded-full flex items-center justify-center mx-auto shadow-lg shadow-indigo-200 dark:shadow-indigo-900/50">
            <Sparkles size={26} className="text-amber-300" />
          </div>
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
            Your Celestial Blueprint
          </h2>
          <p className="text-sm text-zinc-400 dark:text-zinc-500">
            {userName}, here's what the stars reveal
          </p>
        </div>

        {/* Chart card */}
        <div className="bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-200 dark:border-zinc-700 p-5 space-y-1">
          {rows.map((row, i) => (
            <div
              key={row.label}
              className={cn(
                "flex items-center justify-between py-3 px-3 rounded-xl transition-all duration-300",
                revealIndex > i
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-2",
                i < rows.length - 1 && "border-b border-zinc-100 dark:border-zinc-700/50"
              )}
            >
              <div className="flex items-center gap-3">
                <div className={cn("flex-shrink-0", row.color)}>
                  {row.icon}
                </div>
                <span className="text-sm text-zinc-500 dark:text-zinc-400">
                  {row.label}
                </span>
              </div>
              <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                {row.value}
              </span>
            </div>
          ))}

          {/* Planetary Positions */}
          {hasPlanets && (
            <div
              className={cn(
                "pt-4 px-3 transition-all duration-500",
                revealIndex > rows.length - 1
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-2 hidden"
              )}
            >
              <div className="space-y-3 pt-3 border-t border-zinc-100 dark:border-zinc-700/50">
                <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Planetary Positions</p>
                <div className="grid grid-cols-2 gap-y-2 gap-x-4">
                  {Object.entries(chart.planetary_positions).map(([planet, sign]) => (
                    <div key={planet} className="flex justify-between items-center text-sm">
                      <div className="flex items-center gap-1.5 text-zinc-500">
                         <span className="text-amber-500/80">{planetIcons[planet] || "•"}</span>
                         <span>{planet}</span>
                      </div>
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">{sign}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Conjunctions */}
          {hasConjunctions && (
            <div
              className={cn(
                "pt-4 px-3 transition-all duration-500",
                revealIndex > rows.length + (hasPlanets ? 0 : -1)
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-2 hidden"
              )}
            >
              <div className="space-y-3 pt-3 border-t border-zinc-100 dark:border-zinc-700/50">
                <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Conjunctions</p>
                <div className="flex flex-col gap-2">
                  {chart.conjunctions.map((conj, i) => (
                    <div
                      key={`conj-${i}`}
                      className="inline-flex items-center justify-between p-2.5 rounded-xl border border-indigo-100 dark:border-indigo-900/50 bg-white dark:bg-zinc-800/50"
                    >
                      <div className="flex items-center gap-2">
                        <Sparkles size={14} className="text-indigo-400" />
                        <span className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                          {conj.planets.join(" + ")}
                        </span>
                      </div>
                      <div className="text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-1 rounded-md">
                        {conj.sign}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* CTA */}
        {showCTA && (
          <div className="flex justify-center pb-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <Button
              onClick={onComplete}
              className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white rounded-full px-8 h-11 gap-2 font-medium shadow-lg shadow-indigo-200 dark:shadow-indigo-900/50 text-base"
            >
              Begin your reading
              <ArrowRight size={18} />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
