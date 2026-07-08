import { GraduationCap } from "lucide-react";

export function ChatHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-3xl items-center justify-center gap-3 px-4 py-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand text-brand-foreground shadow-sm">
          <GraduationCap className="h-5 w-5" />
        </div>
        <div className="flex flex-col leading-tight">
          <h1 className="text-lg font-semibold tracking-tight">Edhanta Tutor</h1>
          <p className="text-xs text-muted-foreground">Your study companion</p>
        </div>
      </div>
    </header>
  );
}
