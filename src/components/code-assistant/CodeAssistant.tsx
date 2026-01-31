import { useState } from "react";
import { Sparkles, Upload, ChevronDown, ChevronUp, History, Brain, Eye, Zap, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { ProgressBar } from "@/components/shared/ProgressBar";
import { CodeBlock } from "@/components/shared/CodeBlock";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type ProcessingStatus = "idle" | "generating" | "critiquing" | "improving" | "evaluating" | "complete";

interface Iteration {
  iteration: number;
  yantra_output: string;
  sutra_critique: string;
  agni_output: string;
  score: number;
  improvement?: number;
  score_details?: {
    correctness?: number;
    quality?: number;
    completeness?: number;
    grounding?: number;
    clarity?: number;
    total: number;
  };
}

interface ProcessResult {
  task: string;
  final_solution: string;
  final_score: number;
  iterations: Iteration[];
  total_iterations: number;
  used_rag: boolean;
  rag_chunks?: string[];
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function CodeAssistant() {
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [showIterations, setShowIterations] = useState(false);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [useRAG, setUseRAG] = useState(false);
  const [isCode, setIsCode] = useState(true);

  const handleGenerate = async () => {
    if (!input.trim()) return;

    setStatus("generating");
    setProgress(0);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: input,
          context: uploadedFile ? await uploadedFile.text() : null,
          use_rag: useRAG,
          is_code: isCode,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data: ProcessResult = await response.json();
      setResult(data);
      setStatus("complete");
      setProgress(100);
    } catch (error) {
      console.error("Error processing task:", error);
      alert(`Error: ${error instanceof Error ? error.message : "Failed to process task"}`);
      setStatus("idle");
      setProgress(0);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const getStatusForIteration = (iteration: Iteration, currentIteration: number): ProcessingStatus => {
    if (currentIteration < iteration.iteration) return "complete";
    if (currentIteration === iteration.iteration) {
      // Determine which stage based on what data is available
      if (iteration.agni_output) return "complete";
      if (iteration.sutra_critique) return "improving";
      if (iteration.yantra_output) return "critiquing";
      return "generating";
    }
    return "idle";
  };

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-foreground">Agent System - Code Assistant</h1>
          <p className="text-muted-foreground">
            Describe what you want to build, and watch the agents (Yantra, Sutra, Agni, Smriti) generate and improve your code through recursive learning.
          </p>
        </div>

        {/* Input Section */}
        <Card>
          <CardHeader>
            <CardTitle>Task Input</CardTitle>
            <CardDescription>Enter your task description</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe what you want to build... e.g., 'Create a React hook for managing paginated API data with caching'"
              className="textarea-workspace w-full"
              rows={5}
            />

            {/* Options */}
            <div className="flex items-center gap-4 flex-wrap">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isCode}
                  onChange={(e) => setIsCode(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Code Generation</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useRAG}
                  onChange={(e) => setUseRAG(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Use RAG (Document Context)</span>
              </label>
            </div>

            {/* File Upload */}
            <div className="flex items-center gap-4">
              <label className="cursor-pointer">
                <input
                  type="file"
                  className="hidden"
                  accept=".js,.jsx,.ts,.tsx,.py,.go,.rs,.java,.cpp,.c,.txt,.md"
                  onChange={handleFileUpload}
                />
                <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-secondary/50 hover:bg-secondary transition-colors text-sm text-muted-foreground hover:text-foreground">
                  <Upload className="w-4 h-4" />
                  <span>{uploadedFile ? uploadedFile.name : "Upload context file"}</span>
                </div>
              </label>
              
              {uploadedFile && (
                <button
                  onClick={() => setUploadedFile(null)}
                  className="text-sm text-muted-foreground hover:text-foreground"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Generate Button */}
            <Button
              variant="default"
              size="lg"
              onClick={handleGenerate}
              disabled={!input.trim() || (status !== "idle" && status !== "complete")}
              className="w-full sm:w-auto"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Generate & Improve
            </Button>
          </CardContent>
        </Card>

        {/* Progress Section */}
        {status !== "idle" && status !== "complete" && (
          <Card className="animate-fade-in">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <StatusIndicator status={status} />
                  <span className="text-sm text-muted-foreground">{progress}%</span>
                </div>
                <ProgressBar progress={progress} />
                <p className="text-sm text-muted-foreground">
                  {status === "generating" && "Yantra is generating the initial solution..."}
                  {status === "critiquing" && "Sutra is analyzing and finding issues..."}
                  {status === "improving" && "Agni is improving the solution..."}
                  {status === "evaluating" && "Evaluating solution quality..."}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Section */}
        {result && (
          <div className="space-y-4 animate-fade-in">
            {/* Final Solution */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Final Solution</CardTitle>
                    <CardDescription>Best solution after {result.total_iterations} iteration(s)</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-sm">
                      Score: {(result.final_score * 100).toFixed(1)}%
                    </Badge>
                    <StatusIndicator status="complete" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <CodeBlock code={result.final_solution} language={isCode ? "typescript" : "text"} />
              </CardContent>
            </Card>

            {/* Iterations */}
            {result.iterations.length > 0 && (
              <Card>
                <CardHeader>
                  <button
                    onClick={() => setShowIterations(!showIterations)}
                    className="w-full flex items-center justify-between text-left"
                  >
                    <div className="flex items-center gap-2">
                      <History className="w-4 h-4 text-muted-foreground" />
                      <CardTitle>
                        Iteration History ({result.iterations.length})
                      </CardTitle>
                    </div>
                    {showIterations ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                </CardHeader>
                {showIterations && (
                  <CardContent>
                    <div className="space-y-6">
                      {result.iterations.map((iteration, idx) => (
                        <Card key={idx} className="border-2">
                          <CardHeader>
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-lg">Iteration {iteration.iteration}</CardTitle>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">
                                  Score: {(iteration.score * 100).toFixed(1)}%
                                </Badge>
                                {iteration.improvement !== undefined && iteration.improvement > 0 && (
                                  <Badge variant="default" className="bg-green-600">
                                    <TrendingUp className="w-3 h-3 mr-1" />
                                    +{(iteration.improvement * 100).toFixed(1)}%
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <Tabs defaultValue="yantra" className="w-full">
                              <TabsList className="grid w-full grid-cols-3">
                                <TabsTrigger value="yantra" className="flex items-center gap-2">
                                  <Brain className="w-4 h-4" />
                                  Yantra
                                </TabsTrigger>
                                <TabsTrigger value="sutra" className="flex items-center gap-2">
                                  <Eye className="w-4 h-4" />
                                  Sutra
                                </TabsTrigger>
                                <TabsTrigger value="agni" className="flex items-center gap-2">
                                  <Zap className="w-4 h-4" />
                                  Agni
                                </TabsTrigger>
                              </TabsList>
                              <TabsContent value="yantra" className="space-y-2">
                                <p className="text-sm text-muted-foreground">Initial Generation</p>
                                <CodeBlock code={iteration.yantra_output} language={isCode ? "typescript" : "text"} />
                              </TabsContent>
                              <TabsContent value="sutra" className="space-y-2">
                                <p className="text-sm text-muted-foreground">Critique & Issues Found</p>
                                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                                  <pre className="whitespace-pre-wrap text-sm">{iteration.sutra_critique}</pre>
                                </div>
                              </TabsContent>
                              <TabsContent value="agni" className="space-y-2">
                                <p className="text-sm text-muted-foreground">Improved Solution</p>
                                <CodeBlock code={iteration.agni_output} language={isCode ? "typescript" : "text"} />
                              </TabsContent>
                            </Tabs>
                            {iteration.score_details && (
                              <div className="mt-4 pt-4 border-t border-border">
                                <p className="text-sm font-medium mb-2">Score Breakdown:</p>
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                  {Object.entries(iteration.score_details)
                                    .filter(([key]) => key !== "total")
                                    .map(([key, value]) => (
                                      <div key={key} className="flex justify-between">
                                        <span className="text-muted-foreground capitalize">{key}:</span>
                                        <span className="font-medium">{(value * 100).toFixed(1)}%</span>
                                      </div>
                                    ))}
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>
            )}

            {/* RAG Chunks */}
            {result.used_rag && result.rag_chunks && result.rag_chunks.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Retrieved Document Context</CardTitle>
                  <CardDescription>RAG chunks used for grounding</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.rag_chunks.map((chunk, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-muted/50 border border-border">
                        <p className="text-sm">{chunk}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
