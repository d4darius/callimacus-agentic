import React, { useState, useEffect, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Pdf.js worker setup
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface MediaWindowProps {
  onToggleExpand: (isExpanded: boolean) => void;
}

function MediaWindow({ onToggleExpand }: MediaWindowProps) {
  // We store the File object itself instead of a blob URL
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState<boolean>(false);

  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [extractedPages, setExtractedPages] = useState<Record<string, string>>(
    {},
  );
  const [pageInputValue, setPageInputValue] = useState<string>("1");
  const [isInputFocused, setIsInputFocused] = useState<boolean>(false);
  const [timerResetKey, setTimerResetKey] = useState<number>(0);
  const [zoomLevel, setZoomLevel] = useState<number>(1.0); // 1.0 = Default Fit to Page
  const [containerDim, setContainerDim] = useState<{
    width: number;
    height: number;
  } | null>(null);
  const [pageDim, setPageDim] = useState<{
    width: number;
    height: number;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync the input box if the user uses the Next/Prev buttons
  useEffect(() => {
    setPageInputValue(String(currentPage));
  }, [currentPage]);

  // Listen for the document telling us a new paragraph started!
  useEffect(() => {
    const handleReset = () => {
      console.log("🔄 New paragraph detected. Restarting OCR dwell timer.");
      setTimerResetKey((prev) => prev + 1); // Changing this state forces the 5s timer to restart!
    };
    window.addEventListener("resetOcrTimer", handleReset);
    return () => window.removeEventListener("resetOcrTimer", handleReset);
  }, []);

  // 7-Second Dwell Time OCR Injection
  useEffect(() => {
    // Prevent firing if there is no document or if the user is typing in the page input box
    if (
      !totalPages ||
      Object.keys(extractedPages).length === 0 ||
      !extractedPages[String(currentPage)] ||
      isInputFocused
    )
      return;

    // Start a 5-second countdown
    const dwellTimer = setTimeout(() => {
      const formattedOcr = extractedPages[String(currentPage)];
      console.log(
        `⏱️ Dwell time reached! Injecting Page ${currentPage} into OCR Context.`,
      );

      // Fire the event to Document.tsx
      window.dispatchEvent(
        new CustomEvent("injectOcr", { detail: formattedOcr }),
      );
    }, 7000);

    // CLEANUP: If currentPage changes before 5s, this runs and kills the timer!
    return () => clearTimeout(dwellTimer);
  }, [currentPage, extractedPages, totalPages, isInputFocused, timerResetKey]);

  const handleContainerClick = () => {
    if (!isExtracting) fileInputRef.current?.click();
  };

  // Automatically fit the PDF to the container width
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      setContainerDim({
        width: Math.max(10, entries[0].contentRect.width - 40),
        height: Math.max(10, entries[0].contentRect.height - 40),
      });
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, [pdfFile]);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (file && file.type === "application/pdf") {
      setIsExtracting(true);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("http://localhost:8000/api/media/extract", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();

        if (data.status === "completed") {
          setExtractedPages(data.pages);
          setTotalPages(data.total_pages);
          setCurrentPage(1);
          setPdfFile(file);
          onToggleExpand(true);
        }
      } catch (err) {
        console.error("Extraction failed", err);
        alert("Failed to extract PDF text.");
      } finally {
        setIsExtracting(false);
      }
    } else if (file) {
      alert("Please select a valid PDF file.");
    }
  };

  const closePdf = () => {
    setPdfFile(null);
    setExtractedPages({});
    setCurrentPage(1);
    onToggleExpand(false);
  };

  const handlePageChange = (direction: "next" | "prev") => {
    let newPage = currentPage;
    if (direction === "next" && currentPage < totalPages) newPage += 1;
    if (direction === "prev" && currentPage > 1) newPage -= 1;

    if (newPage !== currentPage) {
      setCurrentPage(newPage);
    }
  };

  // Handle the user hitting "Enter" or clicking away from the input
  const handlePageSubmit = () => {
    let newPage = parseInt(pageInputValue, 10);

    // If they typed letters or nonsense, reset it to the current page
    if (isNaN(newPage)) {
      setPageInputValue(String(currentPage));
      return;
    }

    // Constrain the number to the bounds of the PDF
    if (newPage < 1) newPage = 1;
    if (newPage > totalPages) newPage = totalPages;

    setCurrentPage(newPage);
    setPageInputValue(String(newPage));
  };

  let finalScale = zoomLevel;
  if (pageDim && containerDim) {
    const widthRatio = containerDim.width / pageDim.width;
    const heightRatio = containerDim.height / pageDim.height;
    finalScale = Math.max(0.1, Math.min(widthRatio, heightRatio) * zoomLevel);
  }

  if (pdfFile) {
    return (
      <div className="media-pdf-container">
        <button onClick={closePdf} className="media-close-btn">
          ✕ Close PDF
        </button>

        {/* PDF VIEWPORT */}
        <div className="media-pdf-viewport" ref={containerRef}>
          <Document
            file={pdfFile}
            loading={
              <div style={{ color: "#aaa", padding: "20px" }}>
                Loading PDF rendering engine...
              </div>
            }
          >
            <Page
              pageNumber={currentPage}
              scale={finalScale} // 💡 Use our calculated fit-to-page scale!
              onLoadSuccess={(page: any) => {
                // Safely grab the native dimensions of the PDF the moment it loads
                const width =
                  page.originalWidth ||
                  (page.getViewport && page.getViewport({ scale: 1 }).width) ||
                  800;
                const height =
                  page.originalHeight ||
                  (page.getViewport && page.getViewport({ scale: 1 }).height) ||
                  1000;
                setPageDim({ width, height });
              }}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="media-react-page"
            />
          </Document>
        </div>

        {/* CUSTOM PAGINATION BAR */}
        <div className="media-pagination">
          {/* Pagination Controls */}
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button
              onClick={() => handlePageChange("prev")}
              disabled={currentPage === 1}
              className="media-page-btn"
            >
              ◀ Prev
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <input
                type="text"
                value={pageInputValue}
                onFocus={() => setIsInputFocused(true)}
                onChange={(e) => setPageInputValue(e.target.value)}
                onBlur={() => {
                  setIsInputFocused(false);
                  handlePageSubmit();
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setIsInputFocused(false);
                    handlePageSubmit();
                  }
                }}
                style={{
                  width: "40px",
                  textAlign: "center",
                  background: "var(--bg-navbar)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-main)",
                  borderRadius: "4px",
                  padding: "4px",
                }}
              />
              <span
                className="media-page-text"
                style={{ color: "var(--text-muted)", fontSize: "14px" }}
              >
                / {totalPages || "?"}
              </span>
            </div>
            <button
              onClick={() => handlePageChange("next")}
              disabled={currentPage === totalPages}
              className="media-page-btn"
            >
              Next ▶
            </button>
          </div>

          {/* Zoom Controls */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              borderLeft: "1px solid #333",
              paddingLeft: "20px",
              marginLeft: "10px",
            }}
          >
            <button
              onClick={() => setZoomLevel((z) => Math.max(0.4, z - 0.2))}
              className="media-page-btn"
              title="Zoom Out"
            >
              −
            </button>
            <span
              style={{
                color: "var(--text-muted)",
                fontSize: "13px",
                width: "45px",
                textAlign: "center",
                cursor: "pointer",
              }}
              onClick={() => setZoomLevel(1.0)}
              title="Reset Zoom to Fit"
            >
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={() => setZoomLevel((z) => Math.min(4.0, z + 0.2))}
              className="media-page-btn"
              title="Zoom In"
            >
              +
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={handleContainerClick}
      className={`media-empty-state ${isExtracting ? "extracting" : ""}`}
    >
      <input
        type="file"
        accept="application/pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      {isExtracting ? (
        <div className="media-extracting-text">Extracting Text...</div>
      ) : (
        <>
          <div className="media-plus-icon">+</div>
          <button className="media-open-btn">Open file</button>
        </>
      )}
    </div>
  );
}

export default MediaWindow;
