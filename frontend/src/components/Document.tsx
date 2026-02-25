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

interface InterruptData {
  headingId: string;
  question: string;
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

function Document({ docname, docId }: DocumentProps) {
  const [editor, setEditor] = useState<BlockNoteEditor<any, any, any> | null>(
    null,
  );
  const [error, setError] = useState<string>("");
  const [interruptData, setInterruptData] = useState<InterruptData | null>(
    null,
  );
  const [hitlInput, setHitlInput] = useState<string>("");
  const [interruptPos, setInterruptPos] = useState<{
    top: number;
    left: number;
  } | null>(null);

  const saveAbortRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<number | null>(null);

  // THE SECTION REGISTER
  const sectionRegister = useRef<
    Record<
      string,
      {
        status: "draft" | "review" | "processed" | "warning";
        contentSnapshot: string;
        blocksPayload: any[];
        audioContext: string[];
        ocrContext: string[];
        timeoutId?: number;
      }
    >
  >({});

  const activeHeadingRef = useRef<string>("doc-start");

  // 1) ASYNC INITIALIZATION & LOAD
  useEffect(() => {
    let isMounted = true;

    async function loadInitialData() {
      try {
        setError("");
        const rawData = await fetchDocContent(docId);

        if (!isMounted) return;

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

        const newEditor = BlockNoteEditor.create({
          initialContent: initialBlocks,
        });

        // PRE-LOAD THE REGISTER TO PREVENT SPAMMING THE LLM
        if (initialBlocks) {
          let currentBucket = { headingId: "doc-start", blocks: [] as any[] };
          const loadedBuckets: (typeof currentBucket)[] = [];

          initialBlocks.forEach((block: any) => {
            if (block.type === "heading") {
              if (currentBucket.blocks.length > 0)
                loadedBuckets.push(currentBucket);
              currentBucket = { headingId: block.id, blocks: [block] };
            } else {
              currentBucket.blocks.push(block);
            }
          });
          if (currentBucket.blocks.length > 0)
            loadedBuckets.push(currentBucket);

          // Fill the memory so the app knows these are old, finished paragraphs!
          loadedBuckets.forEach((b) => {
            sectionRegister.current[b.headingId] = {
              status: "processed",
              contentSnapshot: JSON.stringify(b.blocks),
              blocksPayload: b.blocks,
              audioContext: [],
              ocrContext: [],
            };
          });
        }

        setEditor(newEditor);
      } catch (e) {
        if (e instanceof Error && e.message.includes("404")) {
          const emptyEditor = BlockNoteEditor.create();
          setEditor(emptyEditor);
        } else {
          setError("failed");
        }
      }
    }

    setEditor(null);
    loadInitialData();

    return () => {
      isMounted = false;
    };
  }, [docId]);

  // HELPER: Reload Editor Sync (Fetches backend AST changes)
  const syncEditorWithBackend = async () => {
    if (!editor) return;
    try {
      const rawData = await fetchDocContent(docId);
      const parsed = JSON.parse(rawData);
      if (Array.isArray(parsed)) {
        // Hot-swap the blocks to reflect the AI's formatting
        editor.replaceBlocks(editor.document, parsed);
      }
    } catch (err) {
      console.error("Failed to sync AST from backend", err);
    }
  };

  // EXTERNAL CONTEXT INJECTOR: Your external audio/ocr components will call this to secretly dump data into the active bucket
  const injectBackgroundContext = (type: "audio" | "ocr", rawText: string) => {
    const activeId = activeHeadingRef.current;
    if (!sectionRegister.current[activeId]) return;

    if (type === "audio") {
      sectionRegister.current[activeId].audioContext.push(rawText);
    } else {
      sectionRegister.current[activeId].ocrContext.push(rawText);
    }
    console.log(`Injected ${type} data into heading: ${activeId}`);
  };

  // 2) SEND TO LLM
  const sendSectionToLLM = async (headingId: string) => {
    const registerEntry = sectionRegister.current[headingId];
    if (!registerEntry || registerEntry.status !== "draft") return;

    registerEntry.status = "review";
    if (editor) {
      editor.updateBlock(headingId, { props: { backgroundColor: "blue" } });
    }

    const typedText = registerEntry.blocksPayload
      .map((block) =>
        Array.isArray(block.content)
          ? block.content.map((c: any) => c.text).join("")
          : "",
      )
      .join("\n\n");

    const payload = {
      doc_id: docname,
      par_id: headingId,
      audio: registerEntry.audioContext.join(" "),
      ocr: registerEntry.ocrContext.join(" "),
      notes: typedText,
    };

    console.log(`[API CALL] Processing payload for ${headingId}...`);

    try {
      const res = await fetch("http://localhost:8000/api/llm/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (data.status === "paused") {
        console.log(`[HITL INTERRUPT] Agent has a question for ${headingId}`);
        registerEntry.status = "warning";
        if (editor)
          editor.updateBlock(headingId, {
            props: { backgroundColor: "orange" },
          });

        // Trigger the UI Modal!
        setInterruptData({
          headingId,
          question:
            typeof data.interrupt === "string"
              ? data.interrupt
              : JSON.stringify(data.interrupt),
        });
      } else if (data.status === "completed") {
        console.log(`[SUCCESS] Agent finished generating for ${headingId}`);
        registerEntry.status = "processed";

        // Pull the fresh AST array from the backend and update the UI
        await syncEditorWithBackend();

        // Flash green briefly to indicate success
        if (editor) {
          editor.updateBlock(headingId, {
            props: { backgroundColor: "green" },
          });
          setTimeout(() => {
            editor.updateBlock(headingId, {
              props: { backgroundColor: "default" },
            });
          }, 2000);
        }
      }

      // Clear multimodal queues
      registerEntry.audioContext = [];
      registerEntry.ocrContext = [];
    } catch (error) {
      console.error("LLM Process Error:", error);
      registerEntry.status = "draft"; // Revert so it can try again later
      if (editor)
        editor.updateBlock(headingId, {
          props: { backgroundColor: "default" },
        });
    }
  };

  // 3) RESUME AGENT AFTER USER ANSWERS
  const handleHitlSubmit = async () => {
    if (!interruptData || !hitlInput.trim()) return;

    const { headingId } = interruptData;
    const answer = hitlInput;

    // Optimistic UI update
    setInterruptData(null);
    setHitlInput("");
    if (editor)
      editor.updateBlock(headingId, { props: { backgroundColor: "blue" } });

    try {
      const res = await fetch("http://localhost:8000/api/llm/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: docname,
          par_id: headingId,
          answer: answer,
        }),
      });
      const data = await res.json();

      if (data.status === "paused") {
        // Asked a follow up question
        if (editor)
          editor.updateBlock(headingId, {
            props: { backgroundColor: "orange" },
          });
        setInterruptData({ headingId, question: data.interrupt });
      } else if (data.status === "completed") {
        sectionRegister.current[headingId].status = "processed";
        await syncEditorWithBackend();

        if (editor) {
          editor.updateBlock(headingId, {
            props: { backgroundColor: "green" },
          });
          setTimeout(
            () =>
              editor.updateBlock(headingId, {
                props: { backgroundColor: "default" },
              }),
            2000,
          );
        }
      }
    } catch (error) {
      console.error("LLM Resume Error:", error);
      if (editor)
        editor.updateBlock(headingId, { props: { backgroundColor: "red" } });
    }
  };

  // Helper: Finds out which bucket the cursor is currently inside
  const getActiveHeadingId = () => {
    if (!editor) return "doc-start";
    try {
      const cursor = editor.getTextCursorPosition();
      let currentHeading = "doc-start";

      // Read top to bottom, remember the last heading we saw
      for (const block of editor.document) {
        if (block.type === "heading") currentHeading = block.id;
        if (block.id === cursor.block.id) return currentHeading;
      }
    } catch (e) {
      // If the user clicks completely outside the editor (like the sidebar)
      // it loses focus. We return null so all timers can start!
      return null;
    }
    return "doc-start";
  };

  // Manages the start/stop of timers based on cursor focus
  const manageTimers = () => {
    const activeId = getActiveHeadingId();

    // Update our funnel target for the Audio/OCR streams
    if (activeId) activeHeadingRef.current = activeId;

    // Evaluate every bucket in our register
    Object.keys(sectionRegister.current).forEach((headingId) => {
      const entry = sectionRegister.current[headingId];

      if (entry.status === "draft") {
        if (headingId === activeId) {
          // The user is currently inside this draft!
          // PAUSE/CLEAR the timer. They are actively thinking/working here.
          if (entry.timeoutId) {
            window.clearTimeout(entry.timeoutId);
            entry.timeoutId = undefined;
          }
        } else {
          // The user LEFT this draft!
          // START the 20-second countdown if it isn't already ticking.
          if (!entry.timeoutId) {
            entry.timeoutId = window.setTimeout(() => {
              sendSectionToLLM(headingId);
            }, 20000);
          }
        }
      }
    });
  };

  // 3) TRACK TYPING & AUTOSAVE
  const handleEditorChange = async () => {
    if (!editor) return;

    // --- STEP A: Build the Buckets ---
    const buckets: { headingId: string; blocks: any[] }[] = [];
    let currentBucket = { headingId: "doc-start", blocks: [] as any[] };

    editor.document.forEach((block) => {
      if (block.type === "heading") {
        if (currentBucket.blocks.length > 0) buckets.push(currentBucket);
        currentBucket = { headingId: block.id, blocks: [block] };
      } else {
        currentBucket.blocks.push(block);
      }
    });
    if (currentBucket.blocks.length > 0) buckets.push(currentBucket);

    // --- STEP B: Update the Register for Changes ---
    buckets.forEach((bucket) => {
      const currentContentStr = JSON.stringify(bucket.blocks);
      const registerEntry = sectionRegister.current[bucket.headingId];

      if (
        !registerEntry ||
        registerEntry.contentSnapshot !== currentContentStr
      ) {
        // Reset visual background if they edit a processed/warning block
        const headingBlock = editor.getBlock(bucket.headingId);
        if (
          headingBlock &&
          headingBlock.type === "heading" &&
          headingBlock.props.backgroundColor !== "default"
        ) {
          editor.updateBlock(bucket.headingId, {
            props: { backgroundColor: "default" },
          });
        }

        const existingAudio = registerEntry?.audioContext || [];
        const existingOcr = registerEntry?.ocrContext || [];

        // Update memory: Mark as draft, save new text, KEEP existing timer state
        sectionRegister.current[bucket.headingId] = {
          status: "draft",
          contentSnapshot: currentContentStr,
          blocksPayload: bucket.blocks,
          audioContext: existingAudio,
          ocrContext: existingOcr,
          timeoutId: registerEntry?.timeoutId, // Keep it, manageTimers will handle it!
        };
      }
    });

    // --- STEP C: Re-evaluate Timers ---
    manageTimers();

    // --- PART D: Global Autosave ---
    if (debounceTimerRef.current) window.clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = window.setTimeout(async () => {
      saveAbortRef.current?.abort();
      const saveAc = new AbortController();
      saveAbortRef.current = saveAc;
      try {
        await saveDocContent(
          docId,
          JSON.stringify(editor.document),
          saveAc.signal,
        );
      } catch (err) {
        console.error("Autosave failed:", err);
      }
    }, 1000);
  };

  // HELPER: Auto-position the HITL popup next to the active block
  useEffect(() => {
    if (interruptData) {
      // Find the specific BlockNote DOM element
      const blockEl = document.querySelector(
        `[data-id="${interruptData.headingId}"]`,
      );
      if (blockEl) {
        const rect = blockEl.getBoundingClientRect();
        // Position it right below the heading block, slightly indented
        setInterruptPos({
          top: rect.bottom + window.scrollY + 10,
          left: rect.left + window.scrollX + 20,
        });
      }
    } else {
      setInterruptPos(null);
    }
  }, [interruptData]);

  if (error)
    return (
      <div className="empty-state-container">
        <img src="src/assets/Logo_d4.png" className="grayscale-logo" />
        <p className="empty-state-text">Document not found</p>
      </div>
    );

  if (!editor)
    return (
      <div style={{ color: "white", padding: "20px" }}>Loading document...</div>
    );

  return (
    <div className="fileContent" style={{ position: "relative" }}>
      <h1>{docname}</h1>
      <BlockNoteView
        editor={editor}
        theme="dark"
        onChange={handleEditorChange}
        onSelectionChange={manageTimers}
      />

      {/* NEW: CONTEXTUAL HITL QUESTION POPOVER */}
      {interruptData && (
        <div
          style={{
            position: "absolute",
            // Use calculated position, or fallback to center if DOM node wasn't found
            top: interruptPos ? `${interruptPos.top}px` : "50%",
            left: interruptPos ? `${interruptPos.left}px` : "50%",
            transform: interruptPos ? "none" : "translate(-50%, -50%)",
            background: "#2a2a2a",
            padding: "16px",
            borderRadius: "8px",
            borderLeft: "4px solid #ff922b", // Cleaner, less intrusive border
            boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            zIndex: 10000,
            width: "350px",
            color: "#e0e0e0",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginBottom: "8px",
            }}
          >
            <span style={{ fontSize: "16px" }}>🤖</span>
            <h4 style={{ margin: 0, color: "#ff922b", fontSize: "14px" }}>
              Clarification Needed
            </h4>
          </div>

          <p
            style={{
              margin: "0 0 12px 0",
              fontSize: "13px",
              lineHeight: "1.4",
            }}
          >
            {interruptData.question}
          </p>

          <input
            type="text"
            value={hitlInput}
            onChange={(e) => setHitlInput(e.target.value)}
            placeholder="Type your answer..."
            autoFocus // Automatically focuses the input so you can just type!
            style={{
              width: "100%",
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid #444",
              background: "#1e1e1e",
              color: "white",
              marginBottom: "12px",
              boxSizing: "border-box",
              fontSize: "13px",
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleHitlSubmit();
            }}
          />

          <div
            style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}
          >
            <button
              onClick={() => setInterruptData(null)}
              style={{
                padding: "6px 12px",
                fontSize: "12px",
                background: "transparent",
                border: "1px solid #555",
                color: "#aaa",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleHitlSubmit}
              style={{
                padding: "6px 12px",
                fontSize: "12px",
                background: "#ff922b",
                border: "none",
                color: "#111",
                fontWeight: "bold",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Resume
            </button>
          </div>
        </div>
      )}

      {/* FLOATING DEBUGGER PANEL */}
      <div
        style={{
          position: "fixed",
          bottom: 20,
          right: 20,
          background: "#222",
          padding: "10px",
          borderRadius: "8px",
          border: "1px solid #444",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          zIndex: 9999,
        }}
      >
        <span
          style={{
            color: "#aaa",
            fontSize: "12px",
            textAlign: "center",
            fontWeight: "bold",
          }}
        >
          LLM Debugger
        </span>
        <button
          onClick={() =>
            injectBackgroundContext(
              "audio",
              "[MOCK AUDIO: 'The professor mentioned 1945'] ",
            )
          }
          style={{
            background: "#4dabf7",
            color: "white",
            border: "none",
            padding: "6px 12px",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          🎤 Inject Audio
        </button>
        <button
          onClick={() =>
            injectBackgroundContext("ocr", "[MOCK OCR: 'Slide 4: GDP Growth'] ")
          }
          style={{
            background: "#20c997",
            color: "white",
            border: "none",
            padding: "6px 12px",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          📷 Inject OCR
        </button>
      </div>
    </div>
  );
}

export default Document;
