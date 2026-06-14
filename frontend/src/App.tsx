import { FileText, Layers } from "lucide-react";
import { useEffect, useState } from "react";

import {
  Document,
  InferredMetadata,
  deleteDocument,
  listDocuments,
  reinferMetadata,
  updateMetadata,
  uploadDocument,
} from "./api/client";
import Dropzone from "./components/Dropzone";
import MetadataForm from "./components/MetadataForm";

export default function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function replaceDoc(updated: Document) {
    setDocuments((docs) => docs.map((d) => (d.id === updated.id ? updated : d)));
  }

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    try {
      const created = await uploadDocument(file);
      setDocuments((docs) => [created, ...docs]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function handleSave(id: string, metadata: InferredMetadata) {
    replaceDoc(await updateMetadata(id, metadata));
  }

  async function handleReinfer(id: string) {
    replaceDoc(await reinferMetadata(id));
  }

  async function handleDelete(id: string) {
    await deleteDocument(id);
    setDocuments((docs) => docs.filter((d) => d.id !== id));
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8 flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-atlas-600 text-white">
          <Layers className="h-6 w-6" />
        </span>
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Context Uploader</h1>
          <p className="text-sm text-slate-500">
            Upload a document — metadata is inferred automatically. Review and correct anything below.
          </p>
        </div>
      </header>

      <Dropzone onFile={handleUpload} uploading={uploading} />

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="mt-10">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Documents{documents.length > 0 && ` (${documents.length})`}
        </h2>

        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : documents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 px-6 py-12 text-center text-sm text-slate-400">
            No documents yet. Upload one above to get started.
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <article
                key={doc.id}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="mb-4 flex items-center gap-2 border-b border-slate-100 pb-3 text-slate-500">
                  <FileText className="h-4 w-4 shrink-0" />
                  <span className="truncate text-sm font-medium text-slate-700">
                    {doc.filename}
                  </span>
                  <span className="ml-auto shrink-0 text-xs text-slate-400">
                    {(doc.size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
                <MetadataForm
                  document={doc}
                  onSave={handleSave}
                  onReinfer={handleReinfer}
                  onDelete={handleDelete}
                />
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
