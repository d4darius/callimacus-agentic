import React, { useState, useRef } from "react";
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

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleContainerClick = () => {
    if (!isExtracting) fileInputRef.current?.click();
  };

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

          window.dispatchEvent(
            new CustomEvent("injectOcr", { detail: data.pages["1"] }),
          );
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
      window.dispatchEvent(
        new CustomEvent("injectOcr", {
          detail: extractedPages[String(newPage)],
        }),
      );
    }
  };

  if (pdfFile) {
    return (
      <div className="media-pdf-container">
        {/* PDF VIEWPORT */}
        <div
          className="media-pdf-viewport"
          style={{
            overflowY: "auto",
            display: "flex",
            justifyContent: "center",
            backgroundColor: "#333",
          }}
        >
          <button onClick={closePdf} className="media-close-btn">
            ✕ Close PDF
          </button>

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
              renderTextLayer={true} // Allows user to highlight/copy text
              renderAnnotationLayer={true}
              width={450} // Adjust this base width as needed, or calculate dynamically
              className="media-react-page"
            />
          </Document>
        </div>

        {/* CUSTOM PAGINATION BAR */}
        <div className="media-pagination">
          <button
            onClick={() => handlePageChange("prev")}
            disabled={currentPage === 1}
            className="media-page-btn"
          >
            ◀ Prev
          </button>
          <span className="media-page-text">
            Page <strong>{currentPage}</strong> of {totalPages}
          </span>
          <button
            onClick={() => handlePageChange("next")}
            disabled={currentPage === totalPages}
            className="media-page-btn"
          >
            Next ▶
          </button>
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
