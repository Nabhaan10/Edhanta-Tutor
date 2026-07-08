import { useEffect, useRef } from "react";
import { GraduationCap } from "lucide-react";
import type { Message } from "@/lib/edhanta-mock";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

export function MessageList({
  messages,
  isLoading,
}: {
  messages: Message[];
  isLoading: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-40 pt-6">
      <div className="flex flex-col gap-6">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {isLoading && (
          <div className="flex w-full items-start gap-3 animate-fade-in">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand text-brand-foreground">
              <GraduationCap className="h-4 w-4" />
            </div>
            <TypingIndicator />
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
