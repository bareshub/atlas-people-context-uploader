import { Loader2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

const ACCEPTED = [".txt", ".md", ".markdown"];

interface DropzoneProps {
  onFile: (file: File) => void;
  uploading: boolean;
}

function isAccepted(file: File): boolean {
  return ACCEPTED.some((ext) => file.name.toLowerCase().endsWith(ext));
}

export default function Dropzone({ onFile, uploading }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    if (!isAccepted(file)) {
      setError("Please choose a .txt or .md file.");
      return;
    }
    setError(null);
    onFile(file);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !uploading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!uploading) handleFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition ${
          dragging
            ? "border-atlas-500 bg-atlas-50"
            : "border-slate-300 bg-white hover:border-atlas-500 hover:bg-atlas-50"
        } ${uploading ? "pointer-events-none opacity-70" : ""}`}
      >
        {uploading ? (
          <Loader2 className="mb-3 h-10 w-10 animate-spin text-atlas-500" />
        ) : (
          <UploadCloud className="mb-3 h-10 w-10 text-atlas-500" />
        )}
        <p className="font-medium text-slate-700">
          {uploading ? "Uploading & analysing…" : "Drop a document here, or click to browse"}
        </p>
        <p className="mt-1 text-sm text-slate-400">Plain text or Markdown (.txt, .md)</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => {
            handleFiles(e.target.files);
            // Reset so selecting the same file again still fires onChange.
            e.target.value = "";
          }}
        />
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
