import { GraduationCap, User } from "lucide-react";
import type { Message } from "@/lib/edhanta-mock";
import { SourceList } from "./SourceList";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

/**
 * remark-math v6 only understands $...$ and $$...$$ delimiters.
 * The LLM outputs \(...\) for inline and \[...\] for display math.
 * This preprocessor converts them so KaTeX renders correctly.
 */
function preprocessMath(content: string): string {
  return content
    // Display math: \[ ... \]  →  $$ ... $$
    .replace(/\\\[([\s\S]*?)\\\]/g, (_m, inner) => `$$${inner}$$`)
    // Inline math:  \( ... \)  →  $ ... $
    .replace(/\\\(([\s\S]*?)\\\)/g, (_m, inner) => `$${inner}$`);
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex w-full justify-end animate-fade-in">
        <div className="flex max-w-[85%] items-start gap-2 sm:max-w-[75%]">
          <div className="rounded-2xl rounded-tr-md bg-chat-user px-4 py-2.5 text-chat-user-foreground shadow-sm">
            {/* Image thumbnail — shown when the user uploaded a photo */}
            {message.imageUrl && (
              <div className="mb-2">
                <img
                  src={message.imageUrl}
                  alt="Uploaded question"
                  className="max-h-48 w-auto rounded-xl object-contain ring-1 ring-white/20"
                />
              </div>
            )}
            <div className="prose prose-sm dark:prose-invert max-w-none text-foreground">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {preprocessMath(message.content ?? "")}
              </ReactMarkdown>
            </div>
          </div>
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground">
            <User className="h-4 w-4" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full animate-fade-in">
      <div className="flex w-full items-start gap-3">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand text-brand-foreground">
          <GraduationCap className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1 pt-1">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {preprocessMath(message.content ?? "")}
            </ReactMarkdown>
          </div>
          {message.sources && <SourceList sources={message.sources} />}
        </div>
      </div>
    </div>
  );
}
