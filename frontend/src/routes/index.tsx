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
  const [serverStatus, setServerStatus] = useState<"checking" | "starting" | "ready">("checking");
  const [board, setBoard] = useState<Board>("CBSE");

  // ── Health-check: poll /health on mount until backend responds ────────
  useEffect(() => {
    let cancelled = false;
    let timerId: ReturnType<typeof setTimeout>;

    const ping = async () => {
      try {
        const res = await fetch("https://edhanta-tutor.onrender.com/health", {
          signal: AbortSignal.timeout(4000),
        });
        if (!cancelled && res.ok) {
          setServerStatus("ready");
          // Hide banner after 3 s
          timerId = setTimeout(() => setServerStatus((s) => (s === "ready" ? "ready" : s)), 3000);
          return; // stop polling
        }
      } catch {
        // server not yet awake
      }
      if (!cancelled) {
        setServerStatus("starting");
        timerId = setTimeout(ping, 3000); // retry in 3 s
      }
    };

    ping();
    return () => {
      cancelled = true;
      clearTimeout(timerId);
    };
  }, []);

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

      {/* ── Backend status banner ───────────────────────────────────── */}
      {serverStatus !== "ready" && (
        <div
          className={`flex items-center justify-center gap-2 py-1.5 text-xs font-medium ${
            serverStatus === "checking"
              ? "bg-muted text-muted-foreground"
              : "bg-amber-500/15 text-amber-700 dark:text-amber-400"
          }`}
        >
          {serverStatus === "checking" ? (
            <>
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
              Connecting to server…
            </>
          ) : (
            <>
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-amber-500" />
              Server is starting up — first response may take ~30 s
            </>
          )}
        </div>
      )}
      {serverStatus === "ready" && (
        <div className="flex items-center justify-center gap-2 py-1.5 text-xs font-medium bg-green-500/10 text-green-700 dark:text-green-400">
          <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
          Server ready
        </div>
      )}

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
