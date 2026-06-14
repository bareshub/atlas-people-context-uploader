import { Check, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import type { Document, InferredMetadata } from "../api/client";

interface MetadataFormProps {
  document: Document;
  onSave: (id: string, metadata: InferredMetadata) => Promise<void>;
  onReinfer: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

const toLines = (values: string[]) => values.join(", ");
const fromLines = (value: string) =>
  value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);

export default function MetadataForm({
  document,
  onSave,
  onReinfer,
  onDelete,
}: MetadataFormProps) {
  const [draft, setDraft] = useState<InferredMetadata>(document.metadata);
  const [busy, setBusy] = useState<"save" | "reinfer" | "delete" | null>(null);
  const [saved, setSaved] = useState(false);

  // Reset the form when the underlying document changes (e.g. after re-infer).
  useEffect(() => setDraft(document.metadata), [document.metadata]);

  const dirty = JSON.stringify(draft) !== JSON.stringify(document.metadata);

  function update<K extends keyof InferredMetadata>(key: K, value: InferredMetadata[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  }

  async function run(action: "save" | "reinfer" | "delete") {
    setBusy(action);
    try {
      if (action === "save") {
        await onSave(document.id, draft);
        setSaved(true);
      } else if (action === "reinfer") {
        await onReinfer(document.id);
      } else {
        await onDelete(document.id);
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <Field label="Title">
        <input
          className={inputClass}
          value={draft.title}
          onChange={(e) => update("title", e.target.value)}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Document type">
          <input
            className={inputClass}
            value={draft.document_type}
            onChange={(e) => update("document_type", e.target.value)}
          />
        </Field>
        <Field label="Time period">
          <input
            className={inputClass}
            value={draft.time_period}
            onChange={(e) => update("time_period", e.target.value)}
          />
        </Field>
      </div>

      <Field label="Summary">
        <textarea
          className={`${inputClass} min-h-[72px] resize-y`}
          value={draft.summary}
          onChange={(e) => update("summary", e.target.value)}
        />
      </Field>

      <Field label="Refers to (comma-separated)">
        <input
          className={inputClass}
          value={toLines(draft.refers_to)}
          onChange={(e) => update("refers_to", fromLines(e.target.value))}
        />
      </Field>

      <Field label="Key topics (comma-separated)">
        <input
          className={inputClass}
          value={toLines(draft.key_topics)}
          onChange={(e) => update("key_topics", fromLines(e.target.value))}
        />
      </Field>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          type="button"
          disabled={!dirty || busy !== null}
          onClick={() => run("save")}
          className="inline-flex items-center gap-1.5 rounded-lg bg-atlas-600 px-3 py-2 text-sm font-medium text-white hover:bg-atlas-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Check className="h-4 w-4" />
          {busy === "save" ? "Saving…" : saved && !dirty ? "Saved" : "Save changes"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => run("reinfer")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40"
        >
          <RefreshCw className={`h-4 w-4 ${busy === "reinfer" ? "animate-spin" : ""}`} />
          Re-infer
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => run("delete")}
          className="ml-auto inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-40"
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </button>
      </div>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-atlas-500 focus:outline-none focus:ring-2 focus:ring-atlas-100";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}
