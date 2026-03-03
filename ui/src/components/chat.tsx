import { 
  ArrowUp,
  Sparkles,
  Languages,
  Brain,
  Wrench,
  ChevronDown,
  FileText,
  Building2,
  ExternalLink,
  Quote
} from "lucide-react";
import { useChat } from "@/contexts/ChatContext";
import type { AgentActivity, Source, QueryClassification } from "@/contexts/ChatContext";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import remarkGfm from "remark-gfm";
import { API_CONFIG } from "@/lib/api";
import { useUser } from "@/contexts/UserContext";

// Activity badge component
function ActivityBadge({ activity, isLive = false }: { activity: AgentActivity; isLive?: boolean }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div 
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer",
        activity.type === "thinking" 
          ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800" 
          : "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800",
        isLive && "animate-pulse"
      )}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {activity.type === "thinking" ? (
        <Brain size={14} className={cn(isLive && "animate-spin")} />
      ) : (
        <Wrench size={14} className={cn(isLive && "animate-bounce")} />
      )}
      
      <span className="max-w-[200px] truncate">
        {activity.type === "thinking" 
          ? (activity.content || "Thinking...") 
          : `Searching: ${activity.toolName}`
        }
      </span>
      
      {(activity.content || activity.toolParams) && (
        <ChevronDown 
          size={12} 
          className={cn(
            "transition-transform",
            isExpanded && "rotate-180"
          )} 
        />
      )}
      
      {isExpanded && (activity.content || activity.toolParams) && (
        <div 
          className="absolute top-full left-0 mt-2 p-3 bg-white dark:bg-zinc-800 rounded-lg shadow-lg border border-zinc-200 dark:border-zinc-700 text-sm text-left max-w-sm z-20"
          onClick={(e) => e.stopPropagation()}
        >
          {activity.content && (
            <p className="text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap">
              {activity.content}
            </p>
          )}
          {activity.toolParams && (
            <pre className="text-zinc-600 dark:text-zinc-400 text-xs overflow-x-auto">
              {JSON.stringify(activity.toolParams, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

// Classification badge - shows query complexity and retrieval settings
function ClassificationBadge({ classification }: { classification: QueryClassification }) {
  const complexityLabels = {
    specific: "Specific",
    moderate: "Moderate",
    broad: "Broad",
  };

  return (
    <div className="inline-flex items-center gap-1.5 text-xs text-zinc-400 dark:text-zinc-500 font-medium">
      <span>
        {complexityLabels[classification.complexity]}
      </span>
      <span>•</span>
      <span>
        top_k: {classification.top_k}
      </span>
    </div>
  );
}

// Smooth message component for streaming text
function SmoothMessage({ 
  content, 
  isStreaming, 
  sources, 
  onComplete,
  onSourceClick 
}: { 
  content: string, 
  isStreaming: boolean, 
  sources?: Source[], 
  onComplete?: () => void,
  onSourceClick?: (source: Source) => void
}) {
  const [displayedContent, setDisplayedContent] = useState("");
  const indexRef = useRef(0);
  const contentRef = useRef(content);

  // SPEED CONTROL
  // Lower = Faster updates (e.g. 5ms)
  // Higher = Slower updates (e.g. 30ms)
  const UPDATE_INTERVAL = 8;

  // Update ref when content changes
  useEffect(() => {
    contentRef.current = content;
  }, [content]);

  useEffect(() => {
    if (!isStreaming && displayedContent === content) {
      return;
    }

    const interval = setInterval(() => {
      const currentLength = indexRef.current;
      const targetLength = contentRef.current.length;

      if (currentLength < targetLength) {
        // ADAPTIVE SPEED:
        // If we fall behind by > 50 chars, add 5 chars at a time
        // If > 20 chars, add 3
        // Else add 1
        const diff = targetLength - currentLength;
        const chunkSize = diff > 50 ? 5 : diff > 20 ? 2 : 1;

        const nextChunk = contentRef.current.slice(currentLength, currentLength + chunkSize);
        setDisplayedContent(prev => prev + nextChunk);
        indexRef.current += chunkSize;
      } else if (!isStreaming) {
        if (onComplete) onComplete();
        clearInterval(interval);
      }
    }, UPDATE_INTERVAL);

    return () => clearInterval(interval);
  }, [isStreaming, content, displayedContent, onComplete]);

  // If loading historic messages (not live streaming), show instantly
  useEffect(() => {
    if (!isStreaming && indexRef.current === 0 && content.length > 0) {
      setDisplayedContent(content);
      indexRef.current = content.length;
    }
  }, [isStreaming, content]);

  const isVisuallyComplete = !isStreaming && displayedContent === content;

  return (
    <div className="prose dark:prose-invert prose-p:leading-7 prose-pre:p-0 max-w-none prose-zinc prose-base animate-in fade-in duration-500">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({children}) => <p className="mb-4 last:mb-0">{children}</p>,
          a: ({node, className, children, ...props}) => (
            <a
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline cursor-pointer"
              {...props}
            >
              {children}
            </a>
          ),
          ul: ({children}) => <ul className="list-disc pl-4 mb-4 space-y-1">{children}</ul>,
          ol: ({children}) => <ol className="list-decimal pl-4 mb-4 space-y-1">{children}</ol>,
          h1: ({children}) => <h1 className="text-2xl font-bold mb-4 mt-6">{children}</h1>,
          h2: ({children}) => <h2 className="text-xl font-bold mb-3 mt-5">{children}</h2>,
          h3: ({children}) => <h3 className="text-lg font-bold mb-2 mt-4">{children}</h3>,
          table: ({children}) => <div className="overflow-x-auto my-4"><table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-700 border border-zinc-200 dark:border-zinc-700 rounded-lg">{children}</table></div>,
          thead: ({children}) => <thead className="bg-zinc-50 dark:bg-zinc-800">{children}</thead>,
          tbody: ({children}) => <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700 bg-white dark:bg-zinc-900">{children}</tbody>,
          tr: ({children}) => <tr>{children}</tr>,
          th: ({children}) => <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">{children}</th>,
          td: ({children}) => <td className="px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300 whitespace-nowrap">{children}</td>,
          code: ({node, className, children, ...props}) => {
            const match = /language-(\w+)/.exec(className || '')
            return match ? (
              <code className={cn("bg-[#0d0d0d] text-zinc-100 block rounded-md px-4 py-3 my-2 text-sm overflow-x-auto font-mono", className)} {...props}>
                {children}
              </code>
             ) : (
              <code className="bg-transparent text-zinc-900 dark:text-zinc-100 font-semibold font-mono text-[0.9em]" {...props}>
                `{children}`
              </code>
            )
          }
        }}
      >
        {displayedContent}
      </ReactMarkdown>

      {/* Show sources only when visually complete */}
      {isVisuallyComplete && sources && sources.length > 0 && (
        <SourcesCarousel sources={sources} onSourceClick={onSourceClick} />
      )}
    </div>
  );
}

// Sources carousel component
function SourcesCarousel({ sources, onSourceClick }: { sources: Source[], onSourceClick?: (source: Source) => void }) {
  if (!sources || sources.length === 0) return null;
  
  return (
    <div className="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="flex items-center gap-2 mb-3">
        <div className="text-zinc-400">
            <FileText size={14} />
        </div>
        <p className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide">Sources</p>
      </div>
      
      <div className="flex gap-3 overflow-x-auto pb-4 -mx-1 px-1 no-scrollbar mask-gradient">
        {sources.map((source, index) => {
          // If the file_id is a full resource name, use it to construct the link
          // If it's just a short ID, assume backend handles it correctly now
          const docId = source.file_id?.split('/').pop() || source.file_id;
          const uri = source.file_id ? `${API_CONFIG.BASE_URL}/documents/${docId}` : undefined;
          
          const Tag = 'button';
          return (
            <Tag
              key={`${source.file_id || "source"}-${index}`}
              onClick={() => onSourceClick?.(source)}
              className={cn(
                "flex-shrink-0 w-48 p-3 bg-white dark:bg-zinc-800/50 rounded-xl border border-zinc-200 dark:border-zinc-700 flex flex-col justify-between h-24 transition-all group/source text-left hover:border-zinc-300 dark:hover:border-zinc-600 hover:shadow-sm cursor-pointer"
              )}
              title={source.title || source.file_id || "Document"}
            >
              <div className="line-clamp-2 text-xs font-medium text-zinc-800 dark:text-zinc-200 leading-relaxed group-hover/source:text-amber-600 dark:group-hover/source:text-amber-500 transition-colors">
                {source.title || source.file_id || "Untitled Document"}
              </div>
              
              <div className="flex items-center gap-2 mt-2">
                 <div className="w-4 h-4 rounded-full bg-zinc-100 dark:bg-zinc-700 flex items-center justify-center flex-shrink-0 text-[8px] font-bold text-zinc-500 uppercase">
                   {(source.title || "D").charAt(0)}
                 </div>
                 <span className="text-[10px] text-zinc-400 dark:text-zinc-500 truncate">
                   {index + 1} • View Details
                 </span>
              </div>
            </Tag>
          );
        })}
      </div>
    </div>
  );
}


// Profile pill for the header
function ProfilePill() {
  const { profile, chart, logout } = useUser();
  const [isOpen, setIsOpen] = useState(false);

  if (!profile || !chart) return null;

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors text-sm"
      >
        <span className="text-amber-500">☉</span>
        <span className="font-medium text-zinc-700 dark:text-zinc-300">{chart.sun_sign}</span>
        <span className="text-zinc-300 dark:text-zinc-600">·</span>
        <span className="text-blue-400">☽</span>
        <span className="font-medium text-zinc-700 dark:text-zinc-300">{chart.moon_sign}</span>
      </button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title={`${profile.name}'s Chart`}
        description="Your astrological profile"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 bg-zinc-50 dark:bg-zinc-800/50 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
            {[
              { label: "Sun Sign", value: chart.sun_sign, icon: "☉", color: "text-amber-500" },
              { label: "Moon Sign", value: chart.moon_sign, icon: "☽", color: "text-blue-400" },
              { label: "Nakshatra", value: chart.nakshatra, icon: "⭐", color: "text-violet-400" },
              { label: "Birth Number", value: chart.birth_number, icon: "#", color: "text-emerald-500" },
              { label: "Destiny Number", value: chart.destiny_number, icon: "#", color: "text-rose-400" },
            ].map((row) => (
              <div key={row.label} className="space-y-1">
                <p className="text-[10px] uppercase tracking-wider font-semibold text-zinc-400 dark:text-zinc-500">
                  {row.label}
                </p>
                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-200 flex items-center gap-1.5">
                  <span className={row.color}>{row.icon}</span> {row.value}
                </p>
              </div>
            ))}
          </div>

          {/* Planetary Positions */}
          {chart.planetary_positions && Object.keys(chart.planetary_positions).length > 0 && (
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-wider font-semibold text-zinc-400 dark:text-zinc-500">
                Planetary Positions
              </p>
              <div className="grid grid-cols-3 gap-2 bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-lg border border-zinc-100 dark:border-zinc-800">
                {Object.entries(chart.planetary_positions).map(([planet, sign]) => {
                  const planetIcons: Record<string, string> = {
                    Sun: "☉", Moon: "☽", Mars: "♂", Mercury: "☿",
                    Jupiter: "♃", Venus: "♀", Saturn: "♄", Rahu: "☊", Ketu: "☋",
                  };
                  return (
                    <div key={planet} className="flex items-center gap-1.5 text-xs">
                      <span className="text-amber-500">{planetIcons[planet] || "•"}</span>
                      <span className="text-zinc-500 dark:text-zinc-400">{planet}</span>
                      <span className="font-medium text-zinc-900 dark:text-zinc-200">{sign}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Conjunctions */}
          {chart.conjunctions && chart.conjunctions.length > 0 && (
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-wider font-semibold text-zinc-400 dark:text-zinc-500">
                Conjunctions
              </p>
              <div className="flex flex-wrap gap-2">
                {chart.conjunctions.map((conj, i) => (
                  <div
                    key={`conj-${i}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                  >
                    <span className="font-semibold">{conj.planets.join(" + ")}</span>
                    <span className="text-indigo-400 dark:text-indigo-500">in</span>
                    <span>{conj.sign}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <Button
              variant="ghost"
              onClick={() => { logout(); setIsOpen(false); }}
              className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Log out
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}

export function Chat() {
  const { messages, status, sendMessage, isLoading, language, setLanguage, currentActivity } = useChat();
  const { profile } = useUser();
  const [inputValue, setInputValue] = useState("");
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([]);
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastActivityIdRef = useRef<string | null>(null);

  // Track thinking steps from currentActivity
  useEffect(() => {
    if (currentActivity && currentActivity.type === "thinking" && currentActivity.content) {
      // Only add if it's a new activity (different ID)
      if (currentActivity.id !== lastActivityIdRef.current) {
        lastActivityIdRef.current = currentActivity.id;
        setThinkingSteps(prev => [...prev, currentActivity.content!]);
      }
    }
  }, [currentActivity]);



  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, currentActivity]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputValue.trim()) {
        // Clear thinking when user sends new message
        setThinkingSteps([]);
        setIsThinkingExpanded(false);
        lastActivityIdRef.current = null;
        
        sendMessage(inputValue);
        setInputValue("");
      }
    }
  };

  const handleSend = () => {
    if (inputValue.trim()) {
      // Clear thinking when user sends new message
      setThinkingSteps([]);
      setIsThinkingExpanded(false);
      lastActivityIdRef.current = null;
      
      sendMessage(inputValue);
      setInputValue("");
    }
  };

  return (
    <div className="bg-white dark:bg-zinc-900 h-screen w-full flex items-center justify-center font-sans selection:bg-zinc-200 dark:selection:bg-zinc-700">
      <div className="w-full h-full max-w-[1600px] flex relative">

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative h-full">

          {/* Header */}
          <header className="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-4 sm:px-8 z-10 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm">
            <ProfilePill />

            <div className="flex items-center gap-4">


            <div className="flex items-center gap-2">
              <Languages size={18} className="text-zinc-500 dark:text-zinc-400" />
              <div className="flex bg-zinc-100 dark:bg-zinc-800 p-1 rounded-full relative overflow-hidden h-8 w-24">
                {/* Sliding background */}
                <div
                  className={cn(
                    "absolute top-1 bottom-1 w-[calc(50%-4px)] bg-white dark:bg-zinc-600 rounded-full transition-all duration-300 ease-in-out shadow-sm",
                    language === "English" ? "left-1" : "left-[calc(50%+1px)]"
                  )}
                />

                <button
                  onClick={() => setLanguage("English")}
                  className={cn(
                    "relative flex-1 flex items-center justify-center text-[10px] font-bold transition-colors duration-300 z-10 tracking-wider",
                    language === "English" ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
                  )}
                >
                  Eng
                </button>

                <button
                  onClick={() => setLanguage("Hindi")}
                  className={cn(
                    "relative flex-1 flex items-center justify-center text-sm font-bold transition-colors duration-300 z-10",
                    language === "Hindi" ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
                  )}
                >
                  हि
                </button>
              </div>
            </div>

            <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} title={`Status: ${status}`} />
            </div>
          </header>

          {/* Center Content / Chat Area */}
          <div className="flex-1 overflow-y-auto w-full no-scrollbar">
            <div className="w-full max-w-3xl mx-auto px-4 py-20">
              {messages.length > 0 && (
                <div className="space-y-6">
                  {messages.map((msg) => (
                    <div key={msg.id} className="space-y-2 group">

                      <div className={cn(
                        "flex gap-4 w-full",
                        msg.role === "user" ? "justify-end" : "justify-start"
                      )}>
                        {/* Agent Avatar - Top Aligned for ChatGPT style */}
                        {msg.role === 'agent' && (
                            <div className="w-8 h-8 rounded-full border border-zinc-200 dark:border-zinc-700 bg-gradient-to-br from-indigo-50 to-amber-50 dark:from-indigo-900/30 dark:to-amber-900/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                 <Sparkles size={16} className="text-indigo-600 dark:text-indigo-400" />
                            </div>
                        )}

                        {/* Main Bubble */}
                        <div className={cn(
                          "relative px-5 py-3.5 text-base break-words overflow-hidden",
                          "max-w-[85%] sm:max-w-[90%]", 
                          msg.role === "user" 
                            ? "bg-[#f4f4f4] dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-3xl" 
                            : "bg-transparent text-zinc-900 dark:text-zinc-100 px-0 py-0 animate-in fade-in duration-300" 
                        )}>
                          {msg.role === "user" ? (
                            msg.content
                          ) : (
                            <>
                              {/* Show thinking ABOVE the agent response (only for last agent message) */}
                              {thinkingSteps.length > 0 && messages.filter(m => m.role === "agent").slice(-1)[0]?.id === msg.id && (
                                <div className="mb-3">
                                   <button
                                     onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                                     className="flex items-center gap-2 py-1.5 text-left group"
                                   >
                                     <Brain 
                                       size={14} 
                                       className={cn(
                                         "text-zinc-400 dark:text-zinc-500",
                                         currentActivity && "animate-pulse"
                                       )} 
                                     />
                                     <span className="text-sm text-zinc-500 dark:text-zinc-400">
                                       {thinkingSteps[thinkingSteps.length - 1]}
                                     </span>
                                     {currentActivity && (
                                       <span className="text-xs text-zinc-400 animate-pulse">...</span>
                                     )}
                                     <ChevronDown
                                       size={14}
                                       className={cn(
                                         "text-zinc-400 transition-transform duration-200 ml-1",
                                         isThinkingExpanded && "rotate-180"
                                       )}
                                     />
                                   </button>
                                   
                                   {isThinkingExpanded && (
                                     <div className="pl-6 py-2 space-y-1 animate-in fade-in duration-150">
                                       {thinkingSteps.map((step, i) => (
                                         <div key={i} className="flex items-center gap-2">
                                           <div className="w-1.5 h-1.5 rounded-full bg-zinc-300 dark:bg-zinc-600" />
                                           <span className="text-sm text-zinc-500 dark:text-zinc-400">{step}</span>
                                         </div>
                                       ))}
                                     </div>
                                   )}
                                </div>
                              )}
                              <SmoothMessage 
                                content={msg.content} 
                                isStreaming={!!msg.isStreaming}
                                sources={msg.sources}
                                onSourceClick={setSelectedSource}
                              />
                            </>
                          )}
                        </div>
                      </div>
                      
                      {/* Show classification badge after user messages */}
                      {msg.role === "user" && msg.classification && (
                        <div className="flex justify-end mt-1">
                          <ClassificationBadge classification={msg.classification} />
                        </div>
                      )}
                    </div>
                  ))}
                  {/* Show thinking BEFORE agent message exists (waiting for first chunk) */}
                  {thinkingSteps.length > 0 && messages.length > 0 && messages[messages.length - 1]?.role === "user" && (
                    <div className="flex gap-4 w-full justify-start">
                      <div className="w-8 h-8 rounded-full border border-zinc-200 dark:border-zinc-700 bg-gradient-to-br from-indigo-50 to-amber-50 dark:from-indigo-900/30 dark:to-amber-900/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Sparkles size={16} className="text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <div>
                        <button
                          onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                          className="flex items-center gap-2 py-1.5 text-left group"
                        >
                          <Brain size={14} className="text-zinc-400 dark:text-zinc-500 animate-pulse" />
                          <span className="text-sm text-zinc-500 dark:text-zinc-400">
                            {thinkingSteps[thinkingSteps.length - 1]}
                          </span>
                          <span className="text-xs text-zinc-400 animate-pulse">...</span>
                          <ChevronDown
                            size={14}
                            className={cn(
                              "text-zinc-400 transition-transform duration-200 ml-1",
                              isThinkingExpanded && "rotate-180"
                            )}
                          />
                        </button>
                        
                        {isThinkingExpanded && (
                          <div className="pl-6 py-2 space-y-1 animate-in fade-in duration-150">
                            {thinkingSteps.map((step, i) => (
                              <div key={i} className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-zinc-300 dark:bg-zinc-600" />
                                <span className="text-sm text-zinc-500 dark:text-zinc-400">{step}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Loading dots (shown when loading but no current activity and no thinking) */}
                  {isLoading && !currentActivity && thinkingSteps.length === 0 && (
                     <div className="pl-12">
                       <div className="w-2 h-2 bg-zinc-900 dark:bg-zinc-100 rounded-full animate-bounce"></div>
                     </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>
            
            {/* Input Box Area */}
            <div 
              className={cn(
                "w-full px-4 transition-all duration-500 ease-in-out",
                messages.length === 0 
                  ? "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 max-w-2xl flex flex-col items-center justify-center space-y-8" 
                  : "max-w-3xl mx-auto mb-6 sticky bottom-0 bg-white dark:bg-zinc-900 pt-2 pb-6"
              )}
            >
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center animate-in fade-in zoom-in duration-500">
                  <div className={cn(
                    "w-14 h-14 bg-gradient-to-br from-indigo-600 to-violet-700 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-indigo-200 dark:shadow-indigo-900/50",
                    isLoading && "animate-pulse"
                  )}>
                    <Sparkles size={26} className={cn("text-amber-300", isLoading && "animate-spin")} style={isLoading ? { animationDuration: "3s" } : undefined} />
                  </div>
                  <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100 text-center tracking-tight">
                    {profile ? `Welcome, ${profile.name}` : "Ask the stars anything"}
                  </h1>
                  <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-2 text-center max-w-xs">
                    {isLoading
                      ? "Reading your chart and preparing your greeting..."
                      : "Career, love, spirituality — your chart holds the answers."
                    }
                  </p>
                  {isLoading && (
                    <div className="flex items-center gap-1.5 mt-6 animate-in fade-in duration-500">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  )}
                </div>
              )}

            <div className={cn(
              "w-full bg-[#f4f4f4] dark:bg-zinc-800 rounded-[26px] p-2 pl-4 flex items-end relative min-h-[52px]",
              messages.length === 0 && "shadow-sm"
            )}>
              <textarea 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full bg-transparent border-none focus:ring-0 outline-none text-zinc-900 dark:text-zinc-100 placeholder-zinc-500 dark:placeholder-zinc-400 text-base resize-none py-3 max-h-[200px] overflow-y-auto" 
                placeholder="Ask Astro-Agent…"
                style={{ height: 'auto', minHeight: '24px' }}
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
                }}
              ></textarea>
              
              <button 
                onClick={handleSend}
                disabled={!inputValue.trim() || status !== 'connected'}
                className={cn(
                  "p-2 rounded-full mb-1 transition-all flex-shrink-0",
                  inputValue.trim() 
                    ? "bg-black dark:bg-white text-white dark:text-black" 
                    : "bg-[#e5e5e5] dark:bg-zinc-700 text-zinc-400 dark:text-zinc-500 cursor-not-allowed"
                )}
              >
                <ArrowUp size={18} strokeWidth={2.5} />
              </button>
            </div>
            <p className={cn(
              "text-[11px] text-zinc-400 dark:text-zinc-600 mt-2 text-center font-normal transition-opacity duration-300",
              messages.length === 0 ? "opacity-0" : "opacity-100"
            )}>
              Astro-Agent provides guidance, not predictions. Use your own judgement.
            </p>
            </div>

        </main>
      </div>

      {/* Source Details Modal */}
      <Modal
        isOpen={!!selectedSource}
        onClose={() => setSelectedSource(null)}
        title="Source Details"
        className="max-w-2xl"
      >
        {selectedSource && (
          <div className="space-y-6">
            {/* Header / Title */}
            <div>
              <h3 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 leading-snug">
                {selectedSource.title || "Untitled Document"}
              </h3>
              <p className="text-xs text-zinc-500 mt-1 font-mono">
                ID: {selectedSource.file_id?.split('/').pop()}
              </p>
            </div>

            {/* Metadata Grid */}
            {selectedSource.custom_metadata && Object.keys(selectedSource.custom_metadata).length > 0 && (
              <div className="grid grid-cols-2 gap-4 bg-zinc-50 dark:bg-zinc-800/50 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
                {Object.entries(selectedSource.custom_metadata).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <p className="text-[10px] uppercase tracking-wider font-semibold text-zinc-400 dark:text-zinc-500">
                      {key.replace(/_/g, " ")}
                    </p>
                    <p className="text-sm font-medium text-zinc-900 dark:text-zinc-200">
                      {value}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Snippet / Context */}
            {selectedSource.snippet && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
                  <Quote size={14} />
                  <span className="text-xs font-semibold uppercase tracking-wider">Relevant Snippet</span>
                </div>
                <div className="bg-amber-50 dark:bg-amber-900/10 p-4 rounded-lg border border-amber-100 dark:border-amber-900/20 text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed italic relative max-h-[300px] overflow-y-auto">
                  "{selectedSource.snippet}"
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end pt-4 border-t border-zinc-100 dark:border-zinc-800">
              <Button 
                onClick={() => {
                   const docId = selectedSource.file_id?.split('/').pop() || selectedSource.file_id;
                   const uri = `${API_CONFIG.BASE_URL}/documents/${docId}`;
                   window.open(uri, '_blank');
                }}
                className="bg-zinc-900 hover:bg-zinc-800 text-white gap-2"
              >
                <ExternalLink size={14} />
                Open Original Document
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
