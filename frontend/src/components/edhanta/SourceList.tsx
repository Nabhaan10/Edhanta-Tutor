import { BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Source } from "@/lib/edhanta-mock";

export function SourceList({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null;
  return (
    <div className="mt-3 flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">Sources</span>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((s, i) => (
          <Badge
            key={i}
            variant="secondary"
            className="gap-1.5 rounded-full px-2.5 py-1 font-normal"
          >
            <BookOpen className="h-3 w-3 shrink-0" />
            <span className="text-xs">
              {s.title} · {s.chapter}
              {s.page ? `, p. ${s.page}` : ""}
            </span>
          </Badge>
        ))}
      </div>
    </div>
  );
}
