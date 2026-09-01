import { AlertTriangle, X } from "lucide-react";

export default function DeleteConfirmationDialog({
  title,
  description,
  resourceLabel,
  loading = false,
  onConfirm,
  onCancel,
}) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal delete-confirmation" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
        <header>
          <div><span className="dialog-danger-icon"><AlertTriangle size={18} /></span><h2 id="delete-dialog-title">{title}</h2></div>
          <button type="button" className="icon-button" onClick={onCancel} disabled={loading} aria-label="Close"><X size={16} /></button>
        </header>
        <p>{description}</p>
        <strong className="delete-resource-label">{resourceLabel}</strong>
        <small>This action cannot be undone.</small>
        <footer>
          <button type="button" className="button secondary" onClick={onCancel} disabled={loading}>Cancel</button>
          <button type="button" className="button danger-button" onClick={onConfirm} disabled={loading}>{loading ? "Deleting…" : "Delete"}</button>
        </footer>
      </section>
    </div>
  );
}
