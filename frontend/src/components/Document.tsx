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

function Document({ docname, docId }: DocumentProps) {
  const [editor, setEditor] = useState<BlockNoteEditor<any, any, any> | null>(
    null,
  );
  const [error, setError] = useState<string>("");

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
  // 2) SEND TO LLM (WITH DUMMY DEBUGGER)
  const sendSectionToLLM = async (headingId: string) => {
    const registerEntry = sectionRegister.current[headingId];

    if (!registerEntry || registerEntry.status !== "draft") return;
    registerEntry.status = "review";

    if (editor) {
      editor.updateBlock(headingId, { props: { backgroundColor: "blue" } });
    }

    const typedText = registerEntry.blocksPayload
      .map((block) => {
        if (Array.isArray(block.content)) {
          return block.content.map((c: any) => c.text).join("");
        }
        return "";
      })
      .join("\n");

    const audioText = registerEntry.audioContext.join(" ");
    const ocrText = registerEntry.ocrContext.join(" ");

    const payloadForPython = {
      heading_id: headingId,
      typed_notes: typedText,
      audio_transcript: audioText,
      ocr_data: ocrText,
    };

    console.log(
      `[DUMMY API] Payload prepared for ${headingId}:`,
      payloadForPython,
    );

    // --- DUMMY LLM SIMULATION ---
    setTimeout(() => {
      if (!editor) return;

      // Simulate an 80% chance of success, 20% chance of a warning
      const isSuccess = Math.random() > 0.2;

      if (isSuccess) {
        console.log(`[DUMMY API] Success for ${headingId}`);
        registerEntry.status = "processed";
        editor.updateBlock(headingId, { props: { backgroundColor: "green" } });

        // Fade the green back to default after 2 seconds for a clean UI
        setTimeout(() => {
          const currentBlock = editor.getBlock(headingId);
          if (currentBlock && currentBlock.props.backgroundColor === "green") {
            editor.updateBlock(headingId, {
              props: { backgroundColor: "default" },
            });
          }
        }, 2000);
      } else {
        console.log(`[DUMMY API] Warning generated for ${headingId}`);
        registerEntry.status = "warning";
        editor.updateBlock(headingId, { props: { backgroundColor: "red" } });

        // Insert a mock warning message directly below the heading
        editor.insertBlocks(
          [
            {
              type: "paragraph",
              content:
                "⚠️ DUMMY WARNING: The LLM thinks you missed a detail here.",
            },
          ],
          headingId,
          "after",
        );
      }

      // Clear the multimodal arrays so they don't double-send on the next edit
      registerEntry.audioContext = [];
      registerEntry.ocrContext = [];
    }, 7000); // 3-second fake network delay
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
