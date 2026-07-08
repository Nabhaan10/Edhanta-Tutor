export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-2" aria-label="Edhanta is thinking">
      <span
        className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-typing"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-typing"
        style={{ animationDelay: "150ms" }}
      />
      <span
        className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-typing"
        style={{ animationDelay: "300ms" }}
      />
      <span className="ml-2 text-xs text-muted-foreground">Thinking…</span>
    </div>
  );
}
