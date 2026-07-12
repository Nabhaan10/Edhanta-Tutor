import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUp, ImagePlus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { BoardToggle, type Board } from "./BoardToggle";

export function ChatComposer({
  onSend,
  onSendImage,
  disabled,
  board,
  onBoardChange,
}: {
  onSend: (text: string) => void;
  onSendImage: (file: File) => void;
  disabled?: boolean;
  board: Board;
  onBoardChange: (board: Board) => void;
}) {
  const [value, setValue] = useState("");
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Text submit ─────────────────────────────────────────────────────────────
  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (disabled) return;

    // Image send takes priority when a file is staged
    if (stagedFile) {
      onSendImage(stagedFile);
      clearStaged();
      return;
    }

    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  // ── Image staging ────────────────────────────────────────────────────────────
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStagedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    // Reset input so the same file can be re-selected if cleared
    e.target.value = "";
  };

  // ── Clipboard paste ───────────────────────────────────────────────────────
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = Array.from(e.clipboardData.items);
    const imageItem = items.find((item) => item.type.startsWith("image/"));
    if (!imageItem) return; // no image — let normal text paste proceed

    const file = imageItem.getAsFile();
    if (!file) return;

    // Prevent the browser from also pasting a data-URI string into the textarea
    e.preventDefault();

    // Re-use the exact same staging flow as the file-picker button
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setStagedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const clearStaged = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setStagedFile(null);
    setPreviewUrl(null);
  };

  const isSendable = !disabled && (!!value.trim() || !!stagedFile);

  return (
    <div className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-background/85 backdrop-blur-md">
      {/* ── Image preview strip ─────────────────────────────────────────────── */}
      {previewUrl && (
        <div className="mx-auto flex w-full max-w-3xl items-center gap-3 px-4 pt-3">
          <div className="relative inline-block">
            <img
              src={previewUrl}
              alt="Question preview"
              className="h-20 w-auto rounded-xl object-contain ring-1 ring-border shadow-sm"
            />
            <button
              type="button"
              onClick={clearStaged}
              aria-label="Remove image"
              className="absolute -right-2 -top-2 grid h-5 w-5 place-items-center rounded-full bg-destructive text-destructive-foreground shadow transition-transform hover:scale-110"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            Press&nbsp;<kbd className="rounded border border-border px-1 py-0.5 font-mono text-[10px]">↑</kbd>&nbsp;to send this image question
          </p>
        </div>
      )}

      <form
        onSubmit={submit}
        className="mx-auto flex w-full max-w-3xl items-end gap-2 px-4 py-3 sm:py-4"
      >
        {/* Board toggle — left of the text area */}
        <div className="shrink-0 self-center">
          <BoardToggle board={board} onChange={onBoardChange} />
        </div>

        <div className="flex-1">
          <Textarea
            id="chat-input"
            name="chat-input"
            autoComplete="off"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            onPaste={handlePaste}
            placeholder={
              stagedFile
                ? "Add a note (optional) or press ↑ to send…"
                : "Ask anything… or paste / upload an image question"
            }
            rows={1}
            className="max-h-40 min-h-[48px] resize-none rounded-2xl border-border bg-card px-4 py-3 text-sm shadow-sm focus-visible:ring-1 focus-visible:ring-brand"
          />
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          id="image-upload-input"
          type="file"
          accept=".jpg,.jpeg,.png"
          className="hidden"
          onChange={handleFileChange}
          aria-label="Upload image question"
        />

        {/* Image upload button */}
        <Button
          type="button"
          size="icon"
          variant="outline"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
          className="h-12 w-12 shrink-0 rounded-2xl border-border text-muted-foreground hover:border-brand hover:text-brand transition-colors"
          aria-label="Upload image question"
          id="image-upload-btn"
        >
          <ImagePlus className="h-5 w-5" />
        </Button>

        {/* Send button */}
        <Button
          type="submit"
          size="icon"
          disabled={!isSendable}
          className="h-12 w-12 shrink-0 rounded-2xl bg-brand text-brand-foreground hover:bg-brand/90"
          aria-label="Send message"
        >
          <ArrowUp className="h-5 w-5" />
        </Button>
      </form>
      <p className="pb-2 text-center text-[10px] text-muted-foreground">
        Edhanta Tutor can make mistakes. Always cross-check with your textbook.
      </p>
    </div>
  );
}
