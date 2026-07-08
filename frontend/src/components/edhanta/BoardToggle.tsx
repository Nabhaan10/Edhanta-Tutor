export type Board = "CBSE" | "MH";

interface BoardToggleProps {
  board: Board;
  onChange: (board: Board) => void;
}

export function BoardToggle({ board, onChange }: BoardToggleProps) {
  const isCBSE = board === "CBSE";

  return (
    <div
      role="group"
      aria-label="Board selector"
      className="relative flex h-8 items-center rounded-full p-[3px]"
      style={{
        background: "oklch(0.929 0.013 255.508)",
        boxShadow: "inset 0 1px 3px oklch(0 0 0 / 0.12)",
      }}
    >
      {/* sliding pill */}
      <span
        aria-hidden
        className="pointer-events-none absolute top-[3px] h-[calc(100%-6px)] rounded-full transition-all duration-300 ease-[cubic-bezier(.4,0,.2,1)]"
        style={{
          width: "calc(50% - 3px)",
          left: isCBSE ? "3px" : "calc(50%)",
          background: isCBSE
            ? "oklch(0.55 0.15 195)"   /* teal — brand colour */
            : "oklch(0.65 0.18 45)",    /* saffron — MH board */
          boxShadow: "0 1px 4px oklch(0 0 0 / 0.25)",
        }}
      />

      {/* CBSE button */}
      <button
        id="board-cbse"
        type="button"
        onClick={() => onChange("CBSE")}
        className="relative z-10 flex-1 rounded-full px-3 py-0.5 text-xs font-semibold transition-colors duration-200"
        style={{
          color: isCBSE
            ? "oklch(0.99 0.005 195)"   /* white on teal */
            : "oklch(0.45 0.03 255)",   /* muted text */
        }}
        aria-pressed={isCBSE}
      >
        CBSE
      </button>

      {/* MH Board button */}
      <button
        id="board-mh"
        type="button"
        onClick={() => onChange("MH")}
        className="relative z-10 flex-1 rounded-full px-3 py-0.5 text-xs font-semibold transition-colors duration-200"
        style={{
          color: !isCBSE
            ? "oklch(0.99 0.005 45)"    /* white on saffron */
            : "oklch(0.45 0.03 255)",   /* muted text */
        }}
        aria-pressed={!isCBSE}
      >
        MH Board
      </button>
    </div>
  );
}
