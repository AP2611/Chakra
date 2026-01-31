import { useState, useRef, useCallback } from "react";
import { MessageCircle, Send, Sparkles, ChevronDown, ChevronUp, History, Brain, Eye, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { ProgressBar } from "@/components/shared/ProgressBar";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

type ProcessingStatus = "idle" | "generating" | "streaming" | "critiquing" | "improving" | "evaluating" | "complete";

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

export function ChatBot() {
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [showIterations, setShowIterations] = useState(false);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [useRAG, setUseRAG] = useState(false);
  
  // Refs for token streaming (prevent flicker)
  const accumulatedTokensRef = useRef<string>("");
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const tokenCountRef = useRef<number>(0);
  
  // Batched update function to prevent flicker
  const updateResultWithTokens = useCallback((token: string) => {
    accumulatedTokensRef.current += token;
    tokenCountRef.current += 1;
    
    // Clear existing timeout
    if (updateTimeoutRef.current) {
      clearTimeout(updateTimeoutRef.current);
      updateTimeoutRef.current = null;
    }
    
    // Update function
    const updateState = () => {
      const currentText = accumulatedTokensRef.current;
      setResult(prev => {
        if (!prev) {
          return {
            task: input,
            final_solution: currentText,
            final_score: 0,
            iterations: [{
              iteration: 1,
              yantra_output: currentText,
              sutra_critique: "",
              agni_output: currentText,
              score: 0,
              improvement: 0
            }],
            total_iterations: 1,
            used_rag: useRAG
          };
        }
        return {
          ...prev,
          final_solution: currentText,
          iterations: prev.iterations.map((it, idx) => 
            idx === 0 ? { ...it, yantra_output: currentText, agni_output: currentText } : it
          )
        };
      });
    };
    
    // Batch updates: update every 5 tokens or every 100ms (whichever comes first)
    if (tokenCountRef.current % 5 === 0) {
      // Update immediately for every 5th token
      updateState();
    } else {
      // Schedule update after 100ms (debounced)
      updateTimeoutRef.current = setTimeout(() => {
        updateState();
        updateTimeoutRef.current = null;
      }, 100);
    }
  }, [input, useRAG]);

  const handleGenerate = async () => {
    if (!input.trim()) return;

    setStatus("generating");
    setProgress(10);
    setResult(null);
    
    // Reset token accumulation
    accumulatedTokensRef.current = "";
    tokenCountRef.current = 0;
    if (updateTimeoutRef.current) {
      clearTimeout(updateTimeoutRef.current);
      updateTimeoutRef.current = null;
    }

    try {
      // Check API health first
      const healthCheck = await fetch(`${API_URL}/health`);
      if (!healthCheck.ok) {
        throw new Error("Backend API is not available. Please make sure the backend server is running.");
      }

      setProgress(20);
      
      // Use streaming endpoint for fast first response
      const response = await fetch(`${API_URL}/process-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: input,
          context: null,
          use_rag: useRAG,
          is_code: false, // This is for theory/general questions, not code
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
      }

      // Handle streaming response with token-by-token updates
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let firstResponseReceived = false;
      let finalResult: ProcessResult | null = null;
      const iterations: Iteration[] = [];
      
      // Reset token accumulation
      accumulatedTokensRef.current = "";

      if (!reader) {
        throw new Error("Failed to get response reader");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === "token") {
                // Handle token-by-token streaming (prevent flicker with batching)
                if (!firstResponseReceived) {
                  firstResponseReceived = true;
                  setStatus("streaming");
                  setProgress(30);
                }
                
                // Update with batched tokens (prevents flicker)
                updateResultWithTokens(data.token);
                
              } else if (data.type === "first_response" || data.type === "first_response_complete") {
                // Show first response immediately (fallback for non-streaming or streaming complete)
                firstResponseReceived = true;
                setStatus("complete"); // First response is complete, waiting for improvements
                setProgress(50);
                
                // Clear any pending timeout and finalize
                if (updateTimeoutRef.current) {
                  clearTimeout(updateTimeoutRef.current);
                  updateTimeoutRef.current = null;
                }
                
                // Use accumulated tokens if available (from streaming), otherwise use solution
                const solutionText = accumulatedTokensRef.current || data.solution;
                if (accumulatedTokensRef.current && !data.solution) {
                  // We were streaming, use accumulated tokens
                  accumulatedTokensRef.current = solutionText;
                } else if (data.solution) {
                  // Non-streaming response, use provided solution
                  accumulatedTokensRef.current = data.solution;
                }
                
                // Create/update result with first response
                const finalText = accumulatedTokensRef.current || solutionText;
                setResult(prev => {
                  const result: ProcessResult = {
                    task: input,
                    final_solution: finalText,
                    final_score: 0,
                    iterations: [{
                      iteration: 1,
                      yantra_output: finalText,
                      sutra_critique: "",
                      agni_output: finalText,
                      score: 0,
                      improvement: 0
                    }],
                    total_iterations: 1,
                    used_rag: useRAG
                  };
                  return result;
                });
                
              } else if (data.type === "improving_started") {
                // Background improvements have started
                setStatus("improving");
                setProgress(60);
                
              } else if (data.type === "improved") {
                setProgress(70);
                setStatus("improving");
                // Update with improved solution immediately
                setResult(prev => {
                  if (!prev) return null;
                  const iterationNum = data.iteration || 1;
                  return {
                    ...prev,
                    final_solution: data.solution,
                    iterations: prev.iterations.map((it, idx) => 
                      (it.iteration === iterationNum || idx === iterationNum - 1) 
                        ? { ...it, agni_output: data.solution } 
                        : it
                    )
                  };
                });
              } else if (data.type === "iteration_complete") {
                setProgress(80);
                // Update with improved iteration
                const existingIteration = iterations.find(it => it.iteration === data.iteration);
                if (existingIteration) {
                  existingIteration.agni_output = data.solution;
                  existingIteration.score = data.score || 0;
                  existingIteration.improvement = data.improvement || 0;
                } else {
                  iterations.push({
                    iteration: data.iteration,
                    yantra_output: data.solution,
                    sutra_critique: "",
                    agni_output: data.solution,
                    score: data.score || 0,
                    improvement: data.improvement || 0
                  });
                }
                
                setResult(prev => {
                  if (!prev) return null;
                  return {
                    ...prev,
                    final_solution: data.solution,
                    final_score: data.score || 0,
                    iterations: iterations,
                    total_iterations: data.iteration
                  };
                });
              } else if (data.type === "final") {
                // Clear any pending timeout
                if (updateTimeoutRef.current) {
                  clearTimeout(updateTimeoutRef.current);
                  updateTimeoutRef.current = null;
                }
                
                setProgress(100);
                setStatus("complete");
                finalResult = {
                  task: input,
                  final_solution: data.solution,
                  final_score: data.score,
                  iterations: iterations,
                  total_iterations: data.iterations,
                  used_rag: useRAG
                };
                setResult(finalResult);
              } else if (data.type === "error") {
                throw new Error(data.error || "Unknown error");
              }
            } catch (e) {
              console.error("Error parsing stream data:", e);
            }
          }
        }
      }

      // Clear any pending timeout
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
        updateTimeoutRef.current = null;
      }

      if (!firstResponseReceived && !finalResult) {
        throw new Error("No response received from server");
      }

      if (finalResult) {
        setResult(finalResult);
      }
      
      setStatus("complete");
      setProgress(100);
    } catch (error) {
      console.error("Error processing task:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to process task";
      
      // More user-friendly error messages
      if (errorMessage.includes("timeout") || errorMessage.includes("AbortError")) {
        alert("Request timed out. The question might be too complex or Ollama is taking too long. Please try a simpler question or check if Ollama is running.");
      } else if (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError")) {
        alert("Cannot connect to the backend API. Please make sure:\n1. Backend server is running on http://localhost:8000\n2. Ollama is running\n3. No firewall is blocking the connection");
      } else {
        alert(`Error: ${errorMessage}`);
      }
      
      setStatus("idle");
      setProgress(0);
      
      // Cleanup: clear any pending timeouts
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
        updateTimeoutRef.current = null;
      }
      accumulatedTokensRef.current = "";
      tokenCountRef.current = 0;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-8">
            <img 
              src="/chakra-logo.png" 
              alt="Chakra AI Logo" 
              className="w-48 h-48 object-contain"
            />
            <div>
              <h1 className="text-4xl font-semibold text-foreground">ChatBot</h1>
              <p className="text-muted-foreground text-lg">
                Ask theory questions, get explanations, and have conversations - with recursive improvement
              </p>
            </div>
          </div>
        </div>

        {/* Input Card */}
        <Card>
          <CardHeader>
            <CardTitle>Ask a Question</CardTitle>
            <CardDescription>
              Ask any theory question, get explanations, or have a general conversation. 
              The agents will improve the response through iterations.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Textarea
                placeholder="E.g., Explain quantum computing, What is machine learning?, How does photosynthesis work?"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                className="min-h-[120px] resize-none"
                disabled={status !== "idle" && status !== "complete"}
              />
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Press Enter to send, Shift+Enter for new line</span>
                <span>{input.length} characters</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useRAG}
                  onChange={(e) => setUseRAG(e.target.checked)}
                  className="rounded border-border"
                  disabled={status !== "idle" && status !== "complete"}
                />
                <span className="text-sm text-muted-foreground">Use RAG (document context)</span>
              </label>
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
              Ask & Improve
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
                      {status === "generating" && "Yantra is generating the initial response..."}
                      {status === "streaming" && "Streaming response as it's generated..."}
                      {status === "critiquing" && "Sutra is analyzing and finding areas to improve..."}
                      {status === "improving" && "First response complete. Improving in background..."}
                      {status === "evaluating" && "Evaluating response quality..."}
                      {status === "complete" && result && result.final_score === 0 && "First response ready. Improvements coming..."}
                      {status === "complete" && result && result.final_score > 0 && "Improved version ready!"}
                    </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Section */}
        {result && (
          <div className="space-y-4 animate-fade-in">
            {/* Final Response */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Final Response</CardTitle>
                    <CardDescription>Best response after {result.total_iterations} iteration(s)</CardDescription>
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
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-foreground leading-relaxed">
                    {result.final_solution}
                  </div>
                </div>
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
                    <Tabs defaultValue="0" className="space-y-4">
                      <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4">
                        {result.iterations.map((iteration, idx) => (
                          <TabsTrigger key={idx} value={idx.toString()}>
                            Iteration {iteration.iteration}
                            {iteration.improvement !== undefined && iteration.improvement > 0 && (
                              <Badge variant="outline" className="ml-2 text-green-600 border-green-600">
                                +{(iteration.improvement * 100).toFixed(1)}%
                              </Badge>
                            )}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                      {result.iterations.map((iteration, idx) => (
                        <TabsContent key={idx} value={idx.toString()} className="space-y-4">
                          {/* Yantra Output */}
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Brain className="w-4 h-4 text-blue-500" />
                              <h3 className="font-semibold text-sm">Initial Response (Yantra)</h3>
                            </div>
                            <div className="p-4 rounded-lg bg-muted/50 border border-border">
                              <div className="whitespace-pre-wrap text-sm text-foreground">
                                {iteration.yantra_output}
                              </div>
                            </div>
                          </div>

                          {/* Sutra Critique */}
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Eye className="w-4 h-4 text-orange-500" />
                              <h3 className="font-semibold text-sm">Critique (Sutra)</h3>
                            </div>
                            <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
                              <div className="whitespace-pre-wrap text-sm text-foreground">
                                {iteration.sutra_critique}
                              </div>
                            </div>
                          </div>

                          {/* Agni Output */}
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Zap className="w-4 h-4 text-green-500" />
                              <h3 className="font-semibold text-sm">Improved Response (Agni)</h3>
                            </div>
                            <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                              <div className="whitespace-pre-wrap text-sm text-foreground">
                                {iteration.agni_output}
                              </div>
                            </div>
                          </div>

                          {/* Score */}
                          <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
                            <div>
                              <span className="text-sm font-medium">Score: </span>
                              <span className="text-sm font-semibold">
                                {(iteration.score * 100).toFixed(1)}%
                              </span>
                            </div>
                            {iteration.improvement !== undefined && (
                              <div>
                                <span className="text-sm font-medium">Improvement: </span>
                                <span
                                  className={cn(
                                    "text-sm font-semibold",
                                    iteration.improvement > 0
                                      ? "text-green-600"
                                      : iteration.improvement < 0
                                      ? "text-red-600"
                                      : "text-muted-foreground"
                                  )}
                                >
                                  {iteration.improvement > 0 ? "+" : ""}
                                  {(iteration.improvement * 100).toFixed(1)}%
                                </span>
                              </div>
                            )}
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
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

