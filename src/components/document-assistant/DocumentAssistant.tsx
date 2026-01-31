import { useState, useCallback } from "react";
import { Upload, FileText, Search, ChevronDown, ChevronUp, Quote, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { ProgressBar } from "@/components/shared/ProgressBar";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type ProcessingStatus = "idle" | "uploading" | "processing" | "complete" | "error";

interface SourceSnippet {
  id: number;
  text: string;
  relevance: number;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function DocumentAssistant() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceSnippet[]>([]);
  const [showSources, setShowSources] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<Set<string>>(new Set());

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
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
    handleFiles(files);
  };

  const handleFiles = async (files: File[]) => {
    const filesToUpload = files.filter(file => {
      // Accept text-based files and PDFs
      if (!file.name.match(/\.(txt|md|text|pdf)$/i)) {
        alert(`File ${file.name} is not supported. Please upload .txt, .md, or .pdf files only.`);
        return false;
      }
      return true;
    });

    if (filesToUpload.length === 0) return;

    // Set uploading status for all files
    setUploadingFiles(new Set(filesToUpload.map(f => f.name)));
    setStatus("uploading");

    // Upload files sequentially
    for (const file of filesToUpload) {
      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_URL}/upload-document`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "Failed to upload document");
        }

        // Add to uploaded files list
        setUploadedFiles(prev => [...prev, file]);
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error);
        alert(`Failed to upload ${file.name}: ${error instanceof Error ? error.message : "Unknown error"}`);
      } finally {
        // Remove from uploading set
        setUploadingFiles(prev => {
          const newSet = new Set(prev);
          newSet.delete(file.name);
          return newSet;
        });
      }
    }

    // Reset status after all uploads complete
    setStatus("idle");
  };

  const removeFile = async (index: number) => {
    const file = uploadedFiles[index];
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    
    // Note: In a production system, you'd want to delete from backend too
    // For now, we'll just remove from the list
  };

  const handleAsk = async () => {
    if (!question.trim() || uploadedFiles.length === 0) return;

    setStatus("processing");
    setProgress(0);
    setAnswer(null);
    setSources([]);

    try {
      // Check API health
      const healthCheck = await fetch(`${API_URL}/health`);
      if (!healthCheck.ok) {
        throw new Error("Backend API is not available. Please make sure the backend server is running.");
      }

      setProgress(20);

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

      const response = await fetch(`${API_URL}/query-document`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      setProgress(60);

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `API error (${response.status}): ${errorText || response.statusText}`;
        
        if (response.status === 404) {
          errorMessage = "No relevant content found in uploaded documents. Please upload documents first or try a different question.";
        }
        
        throw new Error(errorMessage);
      }

      setProgress(80);
      const data = await response.json();

      setProgress(90);
      setAnswer(data.answer);
      
      // Format sources
      const formattedSources: SourceSnippet[] = data.sources.map((source: any, index: number) => ({
        id: source.id || index + 1,
        text: source.text,
        relevance: source.relevance || 0.9 - (index * 0.1),
      }));
      setSources(formattedSources);

      setStatus("complete");
      setProgress(100);
    } catch (error) {
      console.error("Error querying document:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to process question";
      
      if (errorMessage.includes("timeout") || errorMessage.includes("AbortError")) {
        alert("Request timed out. The question might be too complex or Ollama is taking too long. Please try a simpler question.");
      } else if (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError")) {
        alert("Cannot connect to the backend API. Please make sure:\n1. Backend server is running on http://localhost:8000\n2. Ollama is running\n3. No firewall is blocking the connection");
      } else {
        alert(`Error: ${errorMessage}`);
      }
      
      setStatus("error");
      setProgress(0);
    }
  };

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-foreground">Document Assistant</h1>
          <p className="text-muted-foreground">
            Upload documents and ask questions to get intelligent answers with source citations. Answers are based ONLY on your uploaded documents.
          </p>
        </div>

        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Documents</CardTitle>
            <CardDescription>Upload text or PDF files (.txt, .md, .pdf) to enable document-based Q&A</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={cn(
                "dropzone p-8 text-center border-2 border-dashed rounded-lg transition-colors",
                isDragging ? "dropzone-active border-primary bg-primary/5" : "border-border hover:border-primary/50"
              )}
            >
                <input
                type="file"
                id="file-upload"
                className="hidden"
                multiple
                accept=".txt,.md,.text,.pdf"
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
                      Text, Markdown, or PDF files (.txt, .md, .pdf)
                    </p>
                  </div>
                </div>
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Uploaded Files */}
        {uploadedFiles.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Uploaded Documents ({uploadedFiles.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
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
                      {uploadingFiles.has(file.name) && (
                        <Badge variant="secondary" className="text-xs">
                          Uploading...
                        </Badge>
                      )}
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-sm text-muted-foreground hover:text-destructive transition-colors p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Question Input */}
        {uploadedFiles.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Ask a Question</CardTitle>
              <CardDescription>Ask questions about your uploaded documents</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about your document..."
                  className="input-large pl-12 w-full"
                  onKeyDown={(e) => e.key === "Enter" && handleAsk()}
                />
              </div>

              <Button
                variant="default"
                size="lg"
                onClick={handleAsk}
                disabled={!question.trim() || uploadedFiles.length === 0 || status === "uploading" || status === "processing"}
                className="w-full sm:w-auto"
              >
                <Search className="w-4 h-4 mr-2" />
                Ask Question
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Progress Section */}
        {status === "uploading" && uploadingFiles.size > 0 && (
          <Card className="animate-fade-in">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <StatusIndicator status="improving" />
                  <span className="text-sm text-muted-foreground">
                    Uploading {uploadingFiles.size} file{uploadingFiles.size > 1 ? 's' : ''}...
                  </span>
                </div>
                <ProgressBar progress={progress} />
                <div className="space-y-1">
                  {Array.from(uploadingFiles).map((filename) => (
                    <p key={filename} className="text-xs text-muted-foreground">
                      • {filename}
                    </p>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {status === "processing" && (
          <Card className="animate-fade-in">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <StatusIndicator status="improving" />
                  <span className="text-sm text-muted-foreground">{progress}%</span>
                </div>
                <ProgressBar progress={progress} />
                <p className="text-sm text-muted-foreground">
                  Processing your question with the agent system...
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Answer Section */}
        {answer && (
          <div className="space-y-4 animate-fade-in">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Answer</CardTitle>
                  <StatusIndicator status="complete" />
                </div>
                <CardDescription>
                  Answer based solely on uploaded documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none text-foreground">
                  {answer.split('\n\n').map((paragraph, i) => (
                    <p key={i} className="mb-4 last:mb-0 leading-relaxed">
                      {paragraph.split('**').map((part, j) => 
                        j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                      )}
                    </p>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Source Citations */}
            {sources.length > 0 && (
              <Card>
                <CardHeader>
                  <button
                    onClick={() => setShowSources(!showSources)}
                    className="w-full flex items-center justify-between text-left"
                  >
                    <div className="flex items-center gap-2">
                      <Quote className="w-4 h-4 text-muted-foreground" />
                      <CardTitle>
                        Source Citations ({sources.length})
                      </CardTitle>
                    </div>
                    {showSources ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                </CardHeader>
                {showSources && (
                  <CardContent>
                    <div className="space-y-3">
                      {sources.map((source) => (
                        <div
                          key={source.id}
                          className="p-4 rounded-lg bg-background border border-border"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-primary bg-accent px-2 py-1 rounded">
                              Source {source.id}
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
                  </CardContent>
                )}
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
