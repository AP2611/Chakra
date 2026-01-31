import { useState, useCallback } from "react";
import { Upload, FileText, Search, ChevronDown, ChevronUp, Quote } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { ProgressBar } from "@/components/shared/ProgressBar";
import { cn } from "@/lib/utils";

type ProcessingStatus = "idle" | "improving" | "reviewing" | "finalizing" | "complete";

interface SourceSnippet {
  id: number;
  text: string;
  page: number;
  relevance: number;
}

const mockAnswer = `Based on the document, the key performance metrics for Q3 2024 show significant improvement across all departments:

**Revenue Growth**: The company achieved a 23% year-over-year revenue increase, surpassing the projected 18% target. This was primarily driven by the expansion into the APAC market and the successful launch of the enterprise product tier.

**Customer Retention**: The retention rate improved from 87% to 92%, attributed to the new customer success initiatives implemented in Q2. The NPS score also increased from 45 to 58.

**Operational Efficiency**: Operating costs were reduced by 12% through automation of manual processes and optimization of cloud infrastructure spending.

The document recommends continuing investment in the APAC region and prioritizing the development of additional enterprise features for the next quarter.`;

const mockSources: SourceSnippet[] = [
  {
    id: 1,
    text: "Q3 2024 revenue growth reached 23% YoY, exceeding our 18% target by 5 percentage points...",
    page: 12,
    relevance: 0.95,
  },
  {
    id: 2,
    text: "Customer retention metrics improved significantly, with the retention rate climbing from 87% to 92% following the implementation of new success programs...",
    page: 24,
    relevance: 0.89,
  },
  {
    id: 3,
    text: "Operational efficiency gains of 12% were achieved through strategic automation and cloud optimization initiatives...",
    page: 31,
    relevance: 0.82,
  },
];

export function DocumentAssistant() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceSnippet[]>([]);
  const [showSources, setShowSources] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    setUploadedFiles(prev => [...prev, ...files]);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleAsk = async () => {
    if (!question.trim() || uploadedFiles.length === 0) return;

    setStatus("improving");
    setProgress(0);
    setAnswer(null);
    setSources([]);

    const stages: ProcessingStatus[] = ["improving", "reviewing", "finalizing", "complete"];
    
    for (let i = 0; i < stages.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 700));
      setStatus(stages[i]);
      setProgress((i + 1) * 25);
    }

    setAnswer(mockAnswer);
    setSources(mockSources);
    setProgress(100);
  };

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-foreground">Document Assistant</h1>
          <p className="text-muted-foreground">
            Upload documents and ask questions to get intelligent answers with source citations.
          </p>
        </div>

        {/* Upload Section */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={cn(
            "dropzone p-8 text-center",
            isDragging && "dropzone-active"
          )}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            multiple
            accept=".pdf,.doc,.docx,.txt,.md"
            onChange={handleFileSelect}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-full bg-accent flex items-center justify-center mx-auto">
                <Upload className="w-6 h-6 text-accent-foreground" />
              </div>
              <div>
                <p className="text-foreground font-medium">
                  Drop files here or click to upload
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  PDF, Word, Text, or Markdown files
                </p>
              </div>
            </div>
          </label>
        </div>

        {/* Uploaded Files */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2 animate-fade-in">
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 border border-border"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-primary" />
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-sm text-muted-foreground hover:text-destructive transition-colors"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Question Input */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-4 animate-fade-in">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your document..."
                className="input-large pl-12"
                onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              />
            </div>

            <Button
              variant="primary"
              size="lg"
              onClick={handleAsk}
              disabled={!question.trim() || (status !== "idle" && status !== "complete")}
            >
              <Search className="w-4 h-4" />
              Ask Question
            </Button>
          </div>
        )}

        {/* Progress Section */}
        {status !== "idle" && status !== "complete" && (
          <div className="card-elevated p-6 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
              <StatusIndicator status={status} />
              <span className="text-sm text-muted-foreground">{progress}%</span>
            </div>
            <ProgressBar progress={progress} />
          </div>
        )}

        {/* Answer Section */}
        {answer && (
          <div className="space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
              <h2 className="section-title">Answer</h2>
              <StatusIndicator status="complete" />
            </div>

            <div className="card-elevated p-6">
              <div className="prose prose-sm max-w-none text-foreground">
                {answer.split('\n\n').map((paragraph, i) => (
                  <p key={i} className="mb-4 last:mb-0 leading-relaxed">
                    {paragraph.split('**').map((part, j) => 
                      j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                    )}
                  </p>
                ))}
              </div>
            </div>

            {/* Source Citations */}
            {sources.length > 0 && (
              <div className="card-subtle">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="w-full flex items-center justify-between p-4 text-left hover:bg-secondary/50 transition-colors rounded-xl"
                >
                  <div className="flex items-center gap-2">
                    <Quote className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">
                      Source Citations ({sources.length})
                    </span>
                  </div>
                  {showSources ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>

                {showSources && (
                  <div className="px-4 pb-4 space-y-3 animate-fade-in">
                    {sources.map((source) => (
                      <div
                        key={source.id}
                        className="p-4 rounded-lg bg-background border border-border"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-primary bg-accent px-2 py-1 rounded">
                            Page {source.page}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {Math.round(source.relevance * 100)}% relevant
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground italic">
                          "{source.text}"
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
