import { useState, useEffect, useRef } from "react";
import { BlockNoteEditor } from "@blocknote/core";
import { BlockNoteView } from "@blocknote/mantine";
import {
  FormattingToolbarController,
  FormattingToolbar,
  BasicTextStyleButton,
  BlockTypeSelect,
  CreateLinkButton,
  useBlockNoteEditor,
} from "@blocknote/react";
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

// ==========================================
// CUSTOM TOOLBAR COMPONENTS (STABLE)
// ==========================================

const RewriteToolbarButton = () => {
  const editor = useBlockNoteEditor();

  const handleRewriteClick = () => {
    try {
      const cursor = editor.getTextCursorPosition();
      let currentHeading = "doc-start";

      // Calculate which section the user is currently highlighting
      for (const block of editor.document) {
        if (block.type === "heading") currentHeading = block.id;
        if (block.id === cursor.block.id) break;
      }

      // Fire a custom event to wake up the Document component's modal!
      window.dispatchEvent(
        new CustomEvent("openRewriteModal", { detail: currentHeading }),
      );
    } catch (e) {
      console.warn("Could not find cursor position", e);
    }
  };

  return (
    <button
      onClick={handleRewriteClick}
      style={{
        background: "transparent",
        border: "none",
        color: "#a970ff",
        fontWeight: "bold",
        cursor: "pointer",
        fontSize: "13px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
        padding: "0 8px",
      }}
    >
      Rewrite
    </button>
  );
};

// The stable toolbar definition that BlockNote expects
const CustomFormattingToolbar = (props: any) => (
  <FormattingToolbar {...props}>
    <BlockTypeSelect key={"blockTypeSelect"} />
    <BasicTextStyleButton basicTextStyle={"bold"} key={"boldStyleButton"} />
    <BasicTextStyleButton basicTextStyle={"italic"} key={"italicStyleButton"} />
    <BasicTextStyleButton
      basicTextStyle={"underline"}
      key={"underlineStyleButton"}
    />
    <BasicTextStyleButton basicTextStyle={"strike"} key={"strikeStyleButton"} />
    <CreateLinkButton key={"createLinkButton"} />
    <div
      style={{
        width: "1px",
        height: "24px",
        background: "#555",
        margin: "0 4px",
      }}
    />
    <RewriteToolbarButton key={"rewriteButton"} />
  </FormattingToolbar>
);

// ==========================================
// MAIN DOCUMENT COMPONENT
// ==========================================

function Document({ docname, docId }: DocumentProps) {
  const [editor, setEditor] = useState<BlockNoteEditor<any, any, any> | null>(
    null,
  );
  const [error, setError] = useState<string>("");
  const [pendingQuestions, setPendingQuestions] = useState<
    Record<string, string>
  >({}); // Dictionary to store pending questions by headingId
  // HITL State popup
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null); // Active/Inactive
  const [indicatorPositions, setIndicatorPositions] = useState<
    Record<string, { top: number; left: number }>
  >({}); // Store positions for each question
  const [hitlInput, setHitlInput] = useState<string>("");
  const [rewriteHeadingId, setRewriteHeadingId] = useState<string | null>(null);
  const [rewriteInput, setRewriteInput] = useState<string>("");

  const saveAbortRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null); // Reference to the main container so we can calculate relative coordinates for the yellow dots

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

  // HELPER: Calculate coordinates for the yellow indicator dots
  useEffect(() => {
    const updatePositions = () => {
      if (!containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newPositions: Record<string, { top: number; left: number }> = {};

      Object.keys(pendingQuestions).forEach((headingId) => {
        const blockEl = document.querySelector(`[data-id="${headingId}"]`);
        if (blockEl) {
          const blockRect = blockEl.getBoundingClientRect();
          newPositions[headingId] = {
            // Calculate position relative to our wrapper div
            top: blockRect.top - containerRect.top + blockRect.height / 2 - 11, // Center vertically, adjust for dot size
            left: blockRect.left - containerRect.left - 35, // Push it 35px into the left margin
          };
        }
      });
      setIndicatorPositions(newPositions);
    };

    // Run calculation
    updatePositions();

    // Recalculate if the window resizes
    window.addEventListener("resize", updatePositions);
    return () => window.removeEventListener("resize", updatePositions);
  }, [pendingQuestions, editor?.document]);

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

  // HELPER: Safely extract the question from the LangGraph interrupt payload
  const parseInterruptQuestion = (interruptData: any): string => {
    if (!interruptData) return "Clarification needed.";
    try {
      const parsed =
        typeof interruptData === "string"
          ? JSON.parse(interruptData)
          : interruptData;
      return parsed.question || JSON.stringify(parsed);
    } catch (e) {
      return String(interruptData);
    }
  };

  // HELPER: Listen for the custom Rewrite Button event
  useEffect(() => {
    const handleOpenRewrite = (e: any) => {
      setRewriteHeadingId(e.detail);
    };
    window.addEventListener("openRewriteModal", handleOpenRewrite);
    return () =>
      window.removeEventListener("openRewriteModal", handleOpenRewrite);
  }, []);

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

        // Add to the pending questions dictionary to show the yellow dot and store the question
        const questionText = parseInterruptQuestion(data.interrupt);
        setPendingQuestions((prev) => ({ ...prev, [headingId]: questionText }));
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
        setPendingQuestions((prev) => {
          const updated = { ...prev };
          delete updated[headingId];
          return updated;
        });
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
    if (!activeQuestionId || !hitlInput.trim()) return;

    const headingId = activeQuestionId;
    const answer = hitlInput;

    // Optimistic UI update: Close popover, clear input, remove from queue
    setActiveQuestionId(null);
    setHitlInput("");
    setPendingQuestions((prev) => {
      const updated = { ...prev };
      delete updated[headingId];
      return updated;
    });
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
        setPendingQuestions((prev) => ({
          ...prev,
          [headingId]: parseInterruptQuestion(data.interrupt),
        }));
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

  // 4) SEND REWRITE REQUEST TO AGENT
  const handleRewriteSubmit = async () => {
    if (!rewriteHeadingId || !rewriteInput.trim()) return;

    const headingId = rewriteHeadingId;
    const instruction = rewriteInput;

    // Optimistic UI: Close input and show processing color
    setRewriteHeadingId(null);
    setRewriteInput("");
    if (editor)
      editor.updateBlock(headingId, { props: { backgroundColor: "blue" } });

    try {
      const res = await fetch("http://localhost:8000/api/llm/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: docname,
          par_id: headingId,
          instruction: instruction,
        }),
      });
      const data = await res.json();

      if (data.status === "completed") {
        console.log(`[SUCCESS] Paragraph ${headingId} rewritten.`);
        // Update status, pull new AST, and flash green
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
      console.error("LLM Rewrite Error:", error);
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
        // Protect "processed" paragraphs: If the AI already finished this section, the user is just doing manual touch-ups.
        if (registerEntry && registerEntry.status === "processed") {
          sectionRegister.current[bucket.headingId].contentSnapshot =
            currentContentStr;
          sectionRegister.current[bucket.headingId].blocksPayload =
            bucket.blocks;
          return; // Skip the rest of the loop so it doesn't become a draft!
        }

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

  if (error || docname === "")
    return (
      <div className="empty-state-container">
        <img src="src/assets/Logo_d4.png" className="grayscale-logo" />
        <p className="empty-state-text">Please open a notebook</p>
      </div>
    );

  if (!editor)
    return (
      <div style={{ color: "white", padding: "20px" }}>Loading document...</div>
    );

  return (
    <div
      className="fileContent"
      style={{ position: "relative" }}
      ref={containerRef}
    >
      <h1>{docname}</h1>
      <BlockNoteView
        editor={editor}
        theme="dark"
        onChange={handleEditorChange}
        onSelectionChange={manageTimers}
        formattingToolbar={false}
      >
        <FormattingToolbarController
          formattingToolbar={CustomFormattingToolbar}
        />
      </BlockNoteView>
      {/* REWRITE INSTRUCTION POPOVER */}
      {rewriteHeadingId && (
        <div
          style={{
            position: "fixed",
            top: "20%", // Keep it high on the screen, out of the way of the text
            left: "50%",
            transform: "translateX(-50%)",
            background: "#2a2a2a",
            padding: "16px",
            borderRadius: "8px",
            borderTop: "4px solid #a970ff", // Purple accent for the AI Compiler
            boxShadow: "0 10px 40px rgba(0,0,0,0.6)",
            zIndex: 10000,
            width: "400px",
          }}
        >
          <h4
            style={{
              margin: "0 0 12px 0",
              color: "#a970ff",
              fontSize: "14px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            How should I rewrite this?
          </h4>

          <input
            type="text"
            value={rewriteInput}
            onChange={(e) => setRewriteInput(e.target.value)}
            placeholder="e.g., Make it bullet points, summarize it, fix the math..."
            autoFocus
            className="hitl-input" // Re-using our clean CSS class from earlier!
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRewriteSubmit();
            }}
          />

          <div
            style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}
          >
            <button
              onClick={() => setRewriteHeadingId(null)}
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
              onClick={handleRewriteSubmit}
              style={{
                padding: "6px 12px",
                fontSize: "12px",
                background: "#a970ff",
                border: "none",
                color: "white",
                fontWeight: "bold",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Regenerate
            </button>
          </div>
        </div>
      )}

      {/* RENDER THE YELLOW INDICATOR DOTS FOR EACH PENDING QUESTION */}
      {Object.keys(pendingQuestions).map((headingId) => {
        const pos = indicatorPositions[headingId];
        if (!pos) return null;

        const isActive = activeQuestionId === headingId;

        return (
          <div
            key={headingId}
            onClick={() => {
              // Toggle the popover on/off when clicking the dot
              setActiveQuestionId(isActive ? null : headingId);
              if (!isActive) setHitlInput(""); // Clear input when opening a new one
            }}
            style={{
              position: "absolute",
              top: `${pos.top}px`,
              left: `${pos.left}px`,
              width: "22px",
              height: "22px",
              backgroundColor: isActive ? "#ff922b" : "#fcc419", // Darker orange if open
              borderRadius: "50%",
              cursor: "pointer",
              boxShadow: isActive
                ? "0 0 10px rgba(255,146,43,0.5)"
                : "0 2px 6px rgba(0,0,0,0.4)",
              zIndex: 100,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#222",
              fontWeight: "bold",
              fontSize: "14px",
              transition: "transform 0.1s ease-in-out",
              transform: isActive ? "scale(1.1)" : "scale(1)",
            }}
            title="Clarification Needed"
          >
            ?
          </div>
        );
      })}

      {/* RENDER THE POPOVER FOR THE ACTIVELY SELECTED QUESTION */}
      {activeQuestionId && indicatorPositions[activeQuestionId] && (
        <div
          style={{
            position: "absolute",
            top: `${indicatorPositions[activeQuestionId].top + 30}px`, // Place right below the dot
            left: `${indicatorPositions[activeQuestionId].left}px`,
            background: "#2a2a2a",
            padding: "16px",
            borderRadius: "8px",
            borderLeft: "4px solid #ff922b",
            boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
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
            {pendingQuestions[activeQuestionId]}
          </p>

          <input
            type="text"
            value={hitlInput}
            onChange={(e) => setHitlInput(e.target.value)}
            placeholder="Type your answer..."
            autoFocus
            className="hitl-input"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleHitlSubmit();
            }}
          />

          <div
            style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}
          >
            <button
              onClick={() => setActiveQuestionId(null)}
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
              Close
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
              Submit
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
              "[MOCK AUDIO: 'So as I was saying, GDP stands for General Data Protection'] ",
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
            injectBackgroundContext(
              "ocr",
              "[MOCK OCR: 'Slide 4: GDP Growth, the GDP is the Gross Domestic Product (GDP)'] ",
            )
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
