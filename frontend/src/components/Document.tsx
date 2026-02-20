import { useState, useEffect, useRef } from "react";
import { BlockNoteEditor } from "@blocknote/core";
import { BlockNoteView } from "@blocknote/mantine";
import "@blocknote/core/fonts/inter.css";
import "@blocknote/mantine/style.css";

/* INTERFACES AND PROPS */
interface DocumentProps {
  docname: string;
  docId: string;
}

/* HELPER FUNCTIONS */
async function fetchDocContent(docId: string): Promise<string> {
  const res = await fetch(
    `http://localhost:8000/api/docs/${encodeURIComponent(docId)}`,
  );
  if (!res.ok) throw new Error(`404 Failed to load doc: ${docId}`);
  const data: { docId: string; content: string } = await res.json();
  return data.content;
}

async function saveDocContent(
  docId: string,
  content: string,
  signal?: AbortSignal,
) {
  const res = await fetch(
    `http://localhost:8000/api/docs/${encodeURIComponent(docId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
      signal,
    },
  );
  if (!res.ok) throw new Error(`Failed to save doc: ${docId}`);
}

/* PARALLEL PARAGRAPH MEMORY */
type ParagraphStatus = "draft" | "review" | "processed" | "warning";

// Our "Shadow Memory" to track metadata outside of React's render cycle
interface BlockMetadata {
  contentSnapshot: string;
  status: ParagraphStatus;
  timeoutId?: number; // NodeJS.Timeout in pure TS/Node environments
}

function Document({ docname, docId }: DocumentProps) {
  // Store the initialized BlockNote editor instance
  const [editor, setEditor] = useState<BlockNoteEditor | null>(null);
  const [error, setError] = useState<string>("");

  const saveAbortRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<number | null>(null);
  const blockTrackersRef = useRef<Record<string, BlockMetadata>>({});

  // 1) ASYNC INITIALIZATION & LOAD
  useEffect(() => {
    let isMounted = true;

    async function loadInitialData() {
      try {
        setError("");
        const rawData = await fetchDocContent(docId);

        if (!isMounted) return;

        // Safely parse JSON. If the file is empty, initialBlocks stays undefined.
        let initialBlocks = undefined;
        if (rawData) {
          try {
            const parsed = JSON.parse(rawData);
            if (Array.isArray(parsed) && parsed.length > 0) {
              initialBlocks = parsed;
            }
          } catch (err) {
            console.warn("Could not parse document JSON, starting empty.");
          }
        }

        if (!isMounted) return;

        // Initialize the actual editor with the JSON blocks
        const newEditor = BlockNoteEditor.create({
          initialContent: initialBlocks,
        });
        setEditor(newEditor);
      } catch (e) {
        if (e instanceof Error && e.message.includes("404")) {
          const emptyEditor = BlockNoteEditor.create();
          setEditor(emptyEditor);
        } else {
          setError("failed"); // Triggers the logo
        }
      }
    }

    // Reset editor state when switching documents
    setEditor(null);
    loadInitialData();

    return () => {
      isMounted = false;
    };
  }, [docId]);

  // The function that runs when a 20-second timer expires
  const sendBlockToLLM = async (blockId: string) => {
    const tracker = blockTrackersRef.current[blockId];
    if (!tracker || tracker.status !== "draft") return;

    // 1. Update state to review
    tracker.status = "review";
    console.log(`Block ${blockId} sent to review! Triggering LLM...`);

    // 2. TODO: Gather the block text, OCR data, and STT audio for this timeframe
    // 3. TODO: Fetch call to your Python LLM Agent

    // Example: On success, mark as processed
    // tracker.status = "processed";
  };

  // 2) AUTOSAVE WHEN EDITOR CHANGES
  const handleEditorChange = async () => {
    if (!editor) return;

    // --- Block-Level LLM Tracking ---
    editor.document.forEach((block) => {
      const currentContent = JSON.stringify(block.content);
      const tracker = blockTrackersRef.current[block.id];

      // If the block is new, or its text content has changed
      if (!tracker || tracker.contentSnapshot !== currentContent) {
        // If it's already processed, you mentioned user can request modifications.
        // For now, if they edit a processed block, we won't auto-reprocess,
        // so we just update the snapshot and exit.
        if (tracker?.status === "processed") {
          tracker.contentSnapshot = currentContent;
          return;
        }

        // Clear any existing countdown for this specific block
        if (tracker?.timeoutId) {
          window.clearTimeout(tracker.timeoutId);
        }

        // Set up the new tracker and 20-second countdown
        blockTrackersRef.current[block.id] = {
          contentSnapshot: currentContent,
          status: "draft",
          timeoutId: window.setTimeout(() => {
            sendBlockToLLM(block.id);
          }, 20000), // 20 seconds
        };
      }
    });

    // --- Global Document Autosave ---
    // This runs a 1-second timer to save the whole JSON file to your database
    if (debounceTimerRef.current) window.clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = window.setTimeout(async () => {
      saveAbortRef.current?.abort();
      const saveAc = new AbortController();
      saveAbortRef.current = saveAc;

      try {
        // Stringify the entire document array to save it
        const documentJson = JSON.stringify(editor.document);
        await saveDocContent(docId, documentJson, saveAc.signal);
        console.log("Document successfully autosaved to database.");
      } catch (err) {
        console.error("Autosave failed:", err);
      }
    }, 1000); // Saves 1 second after the user stops typing
  };

  if (error)
    return (
      <div className="empty-state-container">
        <img src="src/assets/Logo_d4.png" className="grayscale-logo" />
        <p className="empty-state-text">Document not found</p>
      </div>
    );

  // Render a simple loading state while fetching and parsing
  if (!editor)
    return (
      <div style={{ color: "white", padding: "20px" }}>Loading document...</div>
    );

  return (
    <div className="fileContent">
      <h1>{docname}</h1>

      {/* BlockNoteView handles the entire Notion-like UI.
        theme="dark" matches the CSS palette we created earlier.
      */}
      <BlockNoteView
        editor={editor}
        theme="dark"
        onChange={handleEditorChange}
      />
    </div>
  );
}

export default Document;
