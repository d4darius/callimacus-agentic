import { useState, useEffect } from "react";

interface DocItem {
  id: string;
  name: string;
}

interface SidebarProps {
  currentDocId: string;
  onSelectDocument: (id: string) => void;
}

function Sidebar({ currentDocId, onSelectDocument }: SidebarProps) {
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [error, setError] = useState<string>("");

  // New state for renaming
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState<string>("");

  useEffect(() => {
    async function fetchDocList() {
      try {
        const res = await fetch("http://localhost:8000/api/docs");
        if (!res.ok) throw new Error("Failed to load document list");

        const data = await res.json();
        setDocs(data);
      } catch (err) {
        setError("Could not connect to backend.");
      }
    }

    fetchDocList();
  }, []);

  const handleCreateNew = async () => {
    const newId = `untitled-${Date.now()}`;
    const newName = "Untitled Document";

    try {
      // 1. ACTUALLY CREATE THE FILE ON THE BACKEND FIRST
      const res = await fetch(`http://localhost:8000/api/docs/${newId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: "[]" }),
      });

      if (!res.ok) throw new Error("Failed to create file on server");

      // 2. ONLY AFTER it exists on the hard drive, update the visual sidebar
      setDocs((prev) => [...prev, { id: newId, name: newName }]);
      onSelectDocument(newId);
    } catch (err) {
      alert("Error creating new document.");
      console.error(err);
    }
  };

  // Helper to safely format the ID just like the backend does
  const sanitizeId = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9_-]/g, "_");
  };

  const handleRenameSubmit = async (oldId: string) => {
    // If they cleared the input, just cancel the edit
    if (!editName.trim()) {
      setEditingId(null);
      return;
    }

    const newId = sanitizeId(editName);

    // If the name didn't actually change, do nothing
    if (oldId === newId) {
      setEditingId(null);
      return;
    }

    try {
      const res = await fetch(
        `http://localhost:8000/api/docs/${oldId}/rename`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ new_id: newId, new_name: editName }),
        },
      );

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Rename failed");
      }

      // 1. Update the sidebar list with the new name and ID
      setDocs((prev) =>
        prev.map((doc) =>
          doc.id === oldId ? { id: newId, name: editName } : doc,
        ),
      );

      // 2. CRUCIAL: If the user renamed the file they are currently looking at,
      // we MUST tell the App to switch to the new ID, otherwise the editor breaks!
      if (currentDocId === oldId) {
        onSelectDocument(newId);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Rename failed");
    } finally {
      // Close the input field
      setEditingId(null);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="workspace-name">Callimachus Note</span>
        <button className="new-doc-button" onClick={handleCreateNew}>
          + New
        </button>
      </div>

      {error && <div className="sidebar-error">{error}</div>}

      <ul className="doc-list">
        {docs.map((doc) => (
          <li key={doc.id} className="doc-item-wrapper">
            {editingId === doc.id ? (
              <input
                autoFocus
                className="rename-input"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onBlur={() => handleRenameSubmit(doc.id)} // Saves if user clicks away
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRenameSubmit(doc.id); // Saves on Enter
                  if (e.key === "Escape") setEditingId(null); // Cancels on Esc
                }}
              />
            ) : (
              <div
                className={`doc-item-container ${currentDocId === doc.id ? "active" : ""}`}
              >
                <button
                  className="doc-item-button"
                  onClick={() => onSelectDocument(doc.id)}
                >
                  📄 {doc.name}
                </button>
                <button
                  className="rename-trigger-btn"
                  onClick={() => {
                    setEditingId(doc.id);
                    setEditName(doc.name);
                  }}
                  title="Rename"
                >
                  ✎
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Sidebar;
