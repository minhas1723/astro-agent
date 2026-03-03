"""
RAGAgent — LangChain agent for Astro-Agent.

Imports shared state from:
  - src.agent.core  (model, session history, system prompt)
  - src.agent.tools (retrieve tool)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from src.agent.core import SYSTEM_PROMPT, gemini, get_session_history
from src.agent.tools import ASTRO_TOOLS

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


class RAGAgent:
    """
    LangChain agent with:
    - create_agent (standard LangChain 1.x API → LangGraph CompiledStateGraph)
    - 7 scoped astrological retrieval tools
    - Per-session InMemoryChatMessageHistory
    """

    def __init__(self) -> None:
        # Build the agent once — stateless, memory injected per call
        self._agent = create_agent(
            model=gemini,
            tools=ASTRO_TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

    # ------------------------------------------------------------------
    # Private: build the message list for a turn
    # ------------------------------------------------------------------
    def _build_messages(
        self,
        message: str,
        session_id: str,
        *,
        language: str = "English",
        user_context: str = "",
    ) -> list:
        """Assemble prior history + context + new user message."""
        history = get_session_history(session_id)
        prior_messages = list(history.messages)

        # Inject language and optional user profile as a system message
        context_parts: list[str] = [f"Respond in: {language}"]
        if user_context:
            context_parts.append(f"User profile:\n{user_context}")

        prior_messages = [
            SystemMessage(content="\n".join(context_parts)),
            *prior_messages,
        ]

        return [*prior_messages, {"role": "user", "content": message}]

    # ------------------------------------------------------------------
    # Original text-only stream (unchanged)
    # ------------------------------------------------------------------
    async def stream(
        self,
        message: str,
        session_id: str,
        user_context: str = "",
    ) -> AsyncIterator[str]:
        """
        Stream the agent's response token-by-token.

        Args:
            message:      The latest user message.
            session_id:   Unique key for this conversation (for memory).
            user_context: Optional serialised user profile (name, sun sign, etc.)
                          injected as an extra system message.

        Yields:
            Individual text chunks as they stream from the LLM.
        """
        history = get_session_history(session_id)

        # Build the input: history messages + optional profile context + new turn
        prior_messages = list(history.messages)

        # Inject the user's profile as an additional system-level message if provided
        if user_context:
            prior_messages = [
                SystemMessage(content=f"User profile:\n{user_context}"),
                *prior_messages,
            ]

        input_messages = [*prior_messages, {"role": "user", "content": message}]

        full_response = ""

        # astream_events gives fine-grained token-level chunks from create_agent
        async for event in self._agent.astream_events(
            {"messages": input_messages},
            version="v2",
        ):
            # on_chat_model_stream fires for every token the LLM emits
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    if isinstance(chunk.content, str):
                        text = chunk.content
                    elif isinstance(chunk.content, list):
                        # Some LLM providers return [{type: "text", text: "..."}]
                        text = "".join(
                            [
                                c.get("text", "")
                                for c in chunk.content
                                if isinstance(c, dict)
                            ]
                        )
                    else:
                        text = str(chunk.content)

                    if text:
                        full_response += text
                        yield text

        # Persist both sides of the conversation into memory
        if full_response:
            history.add_user_message(message)
            history.add_ai_message(full_response)

    # ------------------------------------------------------------------
    # Rich event stream (for the WebSocket endpoint)
    # ------------------------------------------------------------------
    async def stream_events(
        self,
        message: str,
        session_id: str,
        *,
        language: str = "English",
        user_context: str = "",
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream structured events for the WebSocket protocol.

        Yields dicts matching the frontend expected types:
          {"type": "thinking",  "content": "..."}
          {"type": "tool_call", "tool_name": "...", "tool_params": {...}}
          {"type": "chunk",     "content": "..."}
          {"type": "done",      "sources": [...]}

        The method maps LangGraph's astream_events(v2) to these types:
          on_chat_model_start  →  thinking
          on_tool_start        →  tool_call
          on_tool_end          →  (collect source)
          on_chat_model_stream →  chunk   (text content only)
          end of stream        →  done
        """
        history = get_session_history(session_id)
        input_messages = self._build_messages(
            message,
            session_id,
            language=language,
            user_context=user_context,
        )

        full_response = ""
        tool_sources: list[dict[str, Any]] = []
        model_call_count = 0

        async for event in self._agent.astream_events(
            {"messages": input_messages},
            version="v2",
        ):
            kind = event["event"]

            # ── LLM starts reasoning ──────────────────────────────
            if kind == "on_chat_model_start":
                model_call_count += 1
                if model_call_count == 1:
                    yield {
                        "type": "thinking",
                        "content": "Reasoning about your question...",
                    }
                else:
                    # Model called again after tool execution → composing
                    yield {
                        "type": "thinking",
                        "content": "Composing your reading...",
                    }

            # ── Tool invoked ──────────────────────────────────────
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown_tool")
                tool_input = event.get("data", {}).get("input", {})

                # Descriptive thinking for the tool
                readable = tool_name.replace("get_", "").replace("_", " ").title()
                yield {
                    "type": "thinking",
                    "content": f"Searching {readable}...",
                }

                yield {
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "tool_params": tool_input if isinstance(tool_input, dict) else {},
                }

            # ── Tool finished → collect as a source ───────────────
            elif kind == "on_tool_end":
                tool_name = event.get("name", "")
                output = event.get("data", {}).get("output", "")

                # Handle both str and ToolMessage
                if hasattr(output, "content"):
                    snippet = str(output.content)
                elif isinstance(output, str):
                    snippet = output
                else:
                    snippet = str(output)

                if snippet:
                    tool_sources.append(
                        {
                            "title": tool_name.replace("get_", "")
                            .replace("_", " ")
                            .title(),
                            "file_id": tool_name,
                            "snippet": snippet[:500],
                            "custom_metadata": {
                                "tool": tool_name,
                            },
                        }
                    )

            # ── LLM streams text tokens ───────────────────────────
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk is None:
                    continue

                # Extract text content (skip tool-call-only chunks)
                text = ""
                if isinstance(chunk.content, str):
                    text = chunk.content
                elif isinstance(chunk.content, list):
                    text = "".join(
                        [
                            c.get("text", "")
                            for c in chunk.content
                            if isinstance(c, dict)
                        ]
                    )
                elif chunk.content:
                    text = str(chunk.content)

                if text:
                    full_response += text
                    yield {"type": "chunk", "content": text}

        # ── Stream finished ───────────────────────────────────────
        yield {"type": "done", "sources": tool_sources}

        # Persist both sides of the conversation into memory
        if full_response:
            history.add_user_message(message)
            history.add_ai_message(full_response)


# ---------------------------------------------------------------------------
# Module-level singleton (imported by the chat endpoint)
# ---------------------------------------------------------------------------
rag_agent = RAGAgent()
