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

    console.log(`Sending MULTIMODAL payload to Python:`, payloadForPython);
    // TODO: fetch("http://localhost:8000/api/llm/process", { ... })
  };

  // 3) TRACK CHANGES & AUTOSAVE
  const handleEditorChange = async () => {
    if (!editor) return;

    // FIND WHERE THE CURSOR IS
    let activeBlockId: string | null = null;
    try {
      const cursor = editor.getTextCursorPosition();
      activeBlockId = cursor.block.id;
    } catch (e) {
      // Cursor might not be focused, ignore
    }

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

      // UPDATE THE ACTIVE TARGET
      if (activeBlockId && block.id === activeBlockId) {
        activeHeadingRef.current = currentBucket.headingId;
      }
    });
    if (currentBucket.blocks.length > 0) buckets.push(currentBucket);

    // --- STEP B: Update the Register & Manage Timers ---
    buckets.forEach((bucket) => {
      const currentContentStr = JSON.stringify(bucket.blocks);
      const registerEntry = sectionRegister.current[bucket.headingId];

      if (
        !registerEntry ||
        registerEntry.contentSnapshot !== currentContentStr
      ) {
        if (registerEntry?.timeoutId)
          window.clearTimeout(registerEntry.timeoutId);

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

        sectionRegister.current[bucket.headingId] = {
          status: "draft",
          contentSnapshot: currentContentStr,
          blocksPayload: bucket.blocks,
          audioContext: existingAudio,
          ocrContext: existingOcr,
          timeoutId: window.setTimeout(() => {
            sendSectionToLLM(bucket.headingId);
          }, 20000),
        };
      }
    });

    // --- PART C: Global Autosave ---
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
    <div className="fileContent">
      <h1>{docname}</h1>
      <BlockNoteView
        editor={editor}
        theme="dark"
        onChange={handleEditorChange}
      />
    </div>
  );
}

export default Document;
