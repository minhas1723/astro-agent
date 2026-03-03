import { useState } from "react";
import { Brain, ChevronDown, Check, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentActivity } from "@/contexts/ChatContext";

interface ThinkingBlockProps {
  activities?: AgentActivity[];
  isLive?: boolean; // If true, the last activity is considered active
}

export function ThinkingBlock({ activities, isLive = false }: ThinkingBlockProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!activities || activities.length === 0) return null;

  // Determine the status label based on the last activity
  const lastActivity = activities[activities.length - 1];
  if (!lastActivity) return null;

  const isThinking = lastActivity.type === "thinking";
  const label = isThinking 
    ? (lastActivity.content || "Thinking...") 
    : `Used ${lastActivity.toolName}`;

  return (
    <div className="w-full my-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 py-1.5 px-2 text-left group hover:bg-zinc-100 dark:hover:bg-zinc-800/50 rounded-lg transition-colors"
      >
        <div className={cn(
          "relative flex items-center justify-center w-5 h-5",
          isLive && "animate-pulse"
        )}>
           {isLive ? (
             <Brain size={14} className="text-zinc-500 dark:text-zinc-400" />
           ) : (
             <Check size={14} className="text-zinc-500 dark:text-zinc-400" />
           )}
        </div>
        
        <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
          {label}
        </span>

        <ChevronDown
          size={14}
          className={cn(
            "text-zinc-400 dark:text-zinc-500 transition-transform duration-200 ml-1",
            isExpanded ? "rotate-180" : ""
          )}
        />
      </button>

      {isExpanded && (
        <div className="mt-2 pl-2 space-y-4 relative animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="absolute left-[11px] top-2 bottom-2 w-px bg-zinc-200 dark:bg-zinc-800" />
          
          {activities.map((activity, index) => {
            const isLast = index === activities.length - 1;
            const isActive = isLast && isLive;
            
            return (
              <div key={activity.id || index} className="relative pl-6">
                {/* Dot on timeline */}
                <div className={cn(
                  "absolute left-[7px] top-1.5 w-2.5 h-2.5 rounded-full border-2 z-10 box-content bg-white dark:bg-zinc-900",
                  isActive 
                    ? "border-zinc-400 dark:border-zinc-500 animate-pulse" 
                    : "border-zinc-300 dark:border-zinc-700"
                )} />

                <div className="flex flex-col gap-1">
                   <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                        {activity.type === "thinking" ? "Thought" : "Tool Used"}
                      </span>
                      {activity.type === "tool_call" && (
                          <span className="text-[10px] bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-500 font-mono">
                            {activity.toolName}
                          </span>
                      )}
                   </div>
                   
                   {/* Content */}
                   <div className="text-sm text-zinc-600 dark:text-zinc-400">
                      {activity.type === "thinking" ? (
                          <span>{activity.content}</span>
                      ) : (
                          <span className="font-mono text-xs opacity-80">
                            {JSON.stringify(activity.toolParams)}
                          </span>
                      )}
                      
                      {isActive && activity.type === "thinking" && (
                          <span className="inline-block w-1 h-3 ml-1 align-bottom bg-zinc-400 animate-pulse"/>
                      )}
                   </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
