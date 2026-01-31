import { cn } from "@/lib/utils";

type Status = "idle" | "improving" | "reviewing" | "finalizing" | "complete" | "error" | "generating" | "streaming" | "critiquing" | "evaluating";

interface StatusIndicatorProps {
  status: Status;
  className?: string;
}

const statusConfig: Record<Status, { label: string; dotClass: string }> = {
  idle: { label: "Ready", dotClass: "status-dot-idle" },
  generating: { label: "Generating…", dotClass: "status-dot-processing" },
  streaming: { label: "Streaming…", dotClass: "status-dot-processing" },
  critiquing: { label: "Critiquing…", dotClass: "status-dot-processing" },
  improving: { label: "Improving…", dotClass: "status-dot-processing" },
  reviewing: { label: "Reviewing…", dotClass: "status-dot-processing" },
  evaluating: { label: "Evaluating…", dotClass: "status-dot-processing" },
  finalizing: { label: "Finalizing…", dotClass: "status-dot-processing" },
  complete: { label: "Complete", dotClass: "status-dot-active" },
  error: { label: "Error", dotClass: "bg-destructive" },
};

export function StatusIndicator({ status, className }: StatusIndicatorProps) {
  const config = statusConfig[status];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className={cn("status-dot", config.dotClass)} />
      <span className="text-sm text-muted-foreground">{config.label}</span>
    </div>
  );
}
