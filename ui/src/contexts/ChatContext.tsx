import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { API_CONFIG } from "@/lib/api";
import { useUser } from "@/contexts/UserContext";

export type AgentActivity = {
  id: string;
  type: "thinking" | "tool_call";
  content?: string;
  toolName?: string;
  toolParams?: Record<string, unknown>;
  timestamp: Date;
};

export type Source = {
  title: string | null;
  file_id: string | null;
  uri?: string;
  snippet?: string;
  custom_metadata?: Record<string, string>;
};

export type QueryClassification = {
  complexity: "specific" | "moderate" | "broad";
  intent: string;
  top_k: number;
  confidence: number;
  matched_patterns: string[];
};

export type Message = {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  activities?: AgentActivity[];  // Activities that happened before/during this message
  sources?: Source[];  // Document sources used for this response
  classification?: QueryClassification;  // Query classification (for user messages)
};

type ChatStatus = "disconnected" | "connecting" | "connected" | "error";

type ChatContextType = {
  messages: Message[];
  status: ChatStatus;
  sendMessage: (content: string) => void;
  isLoading: boolean;
  language: string;
  setLanguage: (lang: string) => void;
  currentActivity: AgentActivity | null;  // Current activity being performed
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const { profile, chart } = useUser();
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ChatStatus>("disconnected");
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState("English"); // "English" | "Hindi"
  const [currentActivity, setCurrentActivity] = useState<AgentActivity | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pendingActivitiesRef = useRef<AgentActivity[]>([]);
  const isStreamingRef = useRef<boolean>(false);
  const hasSentProfileRef = useRef<boolean>(false);

  const connect = useCallback(() => {
    // Close any existing connection (handles StrictMode double-mount)
    if (wsRef.current) {
      const { readyState } = wsRef.current;
      if (readyState === WebSocket.OPEN) return; // already connected
      if (readyState === WebSocket.CONNECTING) {
        // Kill the in-flight connection from the previous mount cycle
        wsRef.current.onopen = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
      }
    }

    setStatus("connecting");
    
    // Construct URL with language parameter
    const wsUrl = new URL(API_CONFIG.WS_URL);
    wsUrl.searchParams.set("language", language);
    
    const ws = new WebSocket(wsUrl.toString());

    ws.onopen = () => {
      setStatus("connected");
      console.log(`Connected to Chat WS with language: ${language}`);

      // Send user profile context on first connect so the agent knows who it's talking to
      if (profile && chart && !hasSentProfileRef.current) {
        // Build planetary positions string
        const positionsStr = Object.entries(chart.planetary_positions || {})
          .map(([planet, sign]) => `${planet}=${sign}`)
          .join(", ");
        
        // Build conjunctions string
        const conjStr = (chart.conjunctions || []).length > 0
          ? ` Conjunctions: ${chart.conjunctions.map(c => `${c.planets.join("+")} in ${c.sign}`).join(", ")}.`
          : " No conjunctions detected.";
        
        ws.send(JSON.stringify({
          content: `[SYSTEM CONTEXT] User profile: Name=${profile.name}, Sun=${chart.sun_sign}, Moon=${chart.moon_sign}, Nakshatra=${chart.nakshatra}, Birth Number=${chart.birth_number}, Destiny Number=${chart.destiny_number}. Planetary Positions: ${positionsStr}.${conjStr} Greet the user by name and mention their key signs.`
        }));
        hasSentProfileRef.current = true;
        setIsLoading(true);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      console.log("Disconnected from Chat WS");
      // Optional: Auto-reconnect logic could go here
    };

    ws.onerror = (error) => {
      setStatus("error");
      console.error("Chat WS Error:", error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === "thinking") {
          const currentContent = data.content;
          
          // Create the activity object
          const newActivity: AgentActivity = {
            id: crypto.randomUUID(),
            type: "thinking",
            content: currentContent,
            timestamp: new Date(),
          };
          
          // Update current activity for live indicator
          setCurrentActivity(newActivity);
          
          // Decide where to put the activity based on streaming state
          if (isStreamingRef.current) {
            // Add to the currently streaming message
            setMessages(prev => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === "agent" && lastMsg.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMsg, activities: [...(lastMsg.activities || []), newActivity] }
                ];
              }
              return prev;
            });
          } else {
            // Not streaming yet - add to pending for when message starts
            pendingActivitiesRef.current.push(newActivity);
          }
          
        } else if (data.type === "tool_call") {
             const activity: AgentActivity = {
                id: crypto.randomUUID(),
                type: "tool_call",
                toolName: data.tool_name,
                toolParams: data.tool_params,
                timestamp: new Date(),
              };
              
              setCurrentActivity(activity);
              
              setMessages(prev => {
                 const lastMsg = prev[prev.length - 1];
                 if (lastMsg && lastMsg.role === "agent" && lastMsg.isStreaming) {
                     return [
                       ...prev.slice(0, -1),
                       { ...lastMsg, activities: [...(lastMsg.activities || []), activity] }
                     ];
                 }
                 return prev;
              });
              
              // Only add to pending if NOT streaming
              // Note: This logic is tricky with setState async.
              // Safe bet: Always push to pending, but CLEAR pending when "chunk" starts message.
              // If "chunk" arrives, it consumes pending.
              // If we are ALREADY streaming, "chunk" just appends text.
              // So if we are streaming, we don't look at pending.
              // So pushing to pending is harmless duplicate IF we carefully manage it.
              // However, simpler:
              // If we updated message, don't push to pending.
              // We need to know if we updated message.
              // We can't know in this scope easily.
              
              // Correct fix: Use a ref `isStreamingRef` to toggle behavior.
        } else if (data.type === "chunk") {
          setIsLoading(false);
          setCurrentActivity(null);
          setMessages((prev) => {
            const lastMsg = prev[prev.length - 1];
            
            // If the last message is from the agent and is streaming, append to it
            if (lastMsg && lastMsg.role === "agent" && lastMsg.isStreaming) {
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content }
              ];
            } else {
              // Start a new agent message with any pending activities
              isStreamingRef.current = true; // Mark as streaming
              const newMsg: Message = {
                id: crypto.randomUUID(),
                role: "agent",
                content: data.content,
                timestamp: new Date(),
                isStreaming: true,
                activities: [...pendingActivitiesRef.current],
              };
              pendingActivitiesRef.current = [];
              return [...prev, newMsg];
            }
          });

        } else if (data.type === "done") {
            setIsLoading(false);
            setCurrentActivity(null);
            isStreamingRef.current = false; // Done streaming
            // Attach sources to the last agent message
            const sources: Source[] = data.sources || [];
            setMessages((prev) => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg && lastMsg.role === "agent") {
                    return [
                        ...prev.slice(0, -1),
                        { ...lastMsg, isStreaming: false, sources: sources.length > 0 ? sources : undefined }
                    ];
                }
                return prev;
            });
            pendingActivitiesRef.current = [];
        } else if (data.type === "classification") {
            // Attach classification to the last user message
            const classification: QueryClassification = data.classification;
            setMessages((prev) => {
                const lastUserMsgIndex = [...prev].reverse().findIndex(m => m.role === "user");
                if (lastUserMsgIndex !== -1) {
                    const actualIndex = prev.length - 1 - lastUserMsgIndex;
                    const existingMsg = prev[actualIndex];
                    if (!existingMsg) return prev;
                    const updatedMessages = [...prev];
                    updatedMessages[actualIndex] = {
                        id: existingMsg.id,
                        role: existingMsg.role,
                        content: existingMsg.content,
                        timestamp: existingMsg.timestamp,
                        isStreaming: existingMsg.isStreaming,
                        activities: existingMsg.activities,
                        sources: existingMsg.sources,
                        classification
                    };
                    return updatedMessages;
                }
                return prev;
            });
        } else if (data.type === "error") {
            setIsLoading(false);
            setCurrentActivity(null);
            console.error("Agent Error:", data.content);
            pendingActivitiesRef.current = [];
        }
      } catch (err) {
        console.error("Failed to parse WS message:", err);
      }
    };

    wsRef.current = ws;
  }, [language]);

  useEffect(() => {
    setMessages([]); // Clear chat history when connecting (especially on language change)
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((content: string) => {
    if (!content.trim()) return;
    
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.error("WebSocket is not open");
        return;
    }

    // Add user message immediately
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Send to backend
    wsRef.current.send(JSON.stringify({ content }));
  }, []);

  return (
    <ChatContext.Provider value={{ messages, status, sendMessage, isLoading, language, setLanguage, currentActivity }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
