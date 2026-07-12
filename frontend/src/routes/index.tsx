import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ChatHeader } from "@/components/edhanta/ChatHeader";
import { MessageList } from "@/components/edhanta/MessageList";
import { ChatComposer } from "@/components/edhanta/ChatComposer";
import { uid, type Message } from "@/lib/edhanta-mock";
import { type Board } from "@/components/edhanta/BoardToggle";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Edhanta Tutor — Your Study Companion" },
      {
        name: "description",
        content:
          "Edhanta Tutor is a friendly educational chatbot that answers your questions with clear explanations and textbook sources.",
      },
      { property: "og:title", content: "Edhanta Tutor — Your Study Companion" },
      {
        property: "og:description",
        content:
          "Ask anything from your textbooks. Edhanta Tutor explains concepts and cites the source so you can keep learning.",
      },
    ],
  }),
  component: Index,
});

function Index() {

  const [sessionId, setSessionId] = useState("");

  useEffect(() => {
    let id = localStorage.getItem("session_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("session_id", id);
    }
    setSessionId(id);
  }, []);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: uid(),
      role: "assistant",
      content:
        "Hi! I'm Edhanta Tutor. Ask me anything from your textbooks — concepts, definitions, worked examples, or quick revision. I'll do my best to explain it clearly.",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isWarmingUp, setIsWarmingUp] = useState(false);
  const [board, setBoard] = useState<Board>("CBSE");

  // ── Text question handler ──────────────────────────────────────────────────
  const handleSend = async (text: string) => {
    if (!sessionId) return;
    const userMsg: Message = {
      id: uid(),
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Show "warming up" hint after 5 s (Render free-tier cold start)
    const warmTimer = setTimeout(() => setIsWarmingUp(true), 5000);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000);

    try {
      const response = await fetch("https://edhanta-tutor.onrender.com/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, session_id: sessionId, board }),
        signal: controller.signal,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Server error");

      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: data.answer,
          sources: (data.sources ?? []).map((source: string) => ({
            title: source,
            chapter: "",
          })),
        },
      ]);
    } catch (error) {
      const isTimeout = error instanceof DOMException && error.name === "AbortError";
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: isTimeout
            ? "The server took too long to respond. It may be waking up — please try again in a moment."
            : "Sorry, something went wrong while contacting the server.",
        },
      ]);
    } finally {
      clearTimeout(warmTimer);
      clearTimeout(timeoutId);
      setIsLoading(false);
      setIsWarmingUp(false);
    }
  };

  // ── Image question handler ─────────────────────────────────────────────────
  const handleSendImage = async (file: File) => {
    if (!sessionId) return;
    const imageUrl = URL.createObjectURL(file);
    const userMsg: Message = { id: uid(), role: "user", imageUrl };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    const warmTimer = setTimeout(() => setIsWarmingUp(true), 5000);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000);

    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("session_id", sessionId);
      formData.append("board", board);
      formData.append("language", "English");

      const response = await fetch("https://edhanta-tutor.onrender.com/ask-image", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Server error");

      const ext = data.extracted ?? {};
      const metaParts: string[] = [];
      if (ext.subject) metaParts.push(`**Subject:** ${ext.subject}`);
      if (ext.topic) metaParts.push(`**Topic:** ${ext.topic}`);
      if (ext.marks) metaParts.push(`**Marks:** ${ext.marks}`);
      if (ext.question_type) metaParts.push(`**Type:** ${ext.question_type}`);

      const metaBlock =
        metaParts.length > 0
          ? `\n\n---\n*Detected: ${metaParts.join(" · ")}*`
          : "";

      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: data.answer + metaBlock,
          sources: (data.sources ?? []).map((source: string) => ({
            title: source,
            chapter: "",
          })),
        },
      ]);
    } catch (error) {
      const isTimeout = error instanceof DOMException && error.name === "AbortError";
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: isTimeout
            ? "The server took too long to respond. It may be waking up — please try again in a moment."
            : `Sorry, I couldn't process that image. ${error instanceof Error ? error.message : "Unknown error"}`,
        },
      ]);
    } finally {
      clearTimeout(warmTimer);
      clearTimeout(timeoutId);
      setIsLoading(false);
      setIsWarmingUp(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <ChatHeader />
      <main className="flex-1">
        <MessageList messages={messages} isLoading={isLoading} />
        {isWarmingUp && (
          <p className="pb-32 text-center text-xs text-muted-foreground animate-pulse">
            ⏳ Server is waking up, this may take up to 30 seconds…
          </p>
        )}
      </main>
      <ChatComposer
        onSend={handleSend}
        onSendImage={handleSendImage}
        disabled={isLoading}
        board={board}
        onBoardChange={setBoard}
      />
    </div>
  );
}
