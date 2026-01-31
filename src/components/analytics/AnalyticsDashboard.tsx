import { TrendingUp, Clock, Target, Zap, ArrowUp, ArrowDown } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { cn } from "@/lib/utils";

const qualityData = [
  { iteration: "1", before: 45, after: 62 },
  { iteration: "2", before: 62, after: 74 },
  { iteration: "3", before: 74, after: 82 },
  { iteration: "4", before: 82, after: 89 },
  { iteration: "5", before: 89, after: 94 },
];

const performanceData = [
  { time: "00:00", latency: 120, accuracy: 85 },
  { time: "04:00", latency: 115, accuracy: 87 },
  { time: "08:00", latency: 180, accuracy: 84 },
  { time: "12:00", latency: 145, accuracy: 89 },
  { time: "16:00", latency: 130, accuracy: 91 },
  { time: "20:00", latency: 125, accuracy: 92 },
];

const learningHistory = [
  { id: 1, task: "React Hook Optimization", improvement: "+18%", duration: "2.3s", iterations: 4, date: "Today, 2:30 PM" },
  { id: 2, task: "API Error Handling", improvement: "+24%", duration: "1.8s", iterations: 3, date: "Today, 11:15 AM" },
  { id: 3, task: "TypeScript Type Definitions", improvement: "+31%", duration: "3.1s", iterations: 5, date: "Yesterday, 4:45 PM" },
  { id: 4, task: "Database Query Optimization", improvement: "+22%", duration: "2.7s", iterations: 4, date: "Yesterday, 10:00 AM" },
  { id: 5, task: "Component State Management", improvement: "+15%", duration: "1.5s", iterations: 2, date: "2 days ago" },
];

const agentWorkflow = [
  { step: "Input Analysis", duration: 150, status: "complete" },
  { step: "Code Generation", duration: 450, status: "complete" },
  { step: "Self-Review", duration: 280, status: "complete" },
  { step: "Improvement Pass 1", duration: 320, status: "complete" },
  { step: "Improvement Pass 2", duration: 290, status: "complete" },
  { step: "Final Validation", duration: 180, status: "complete" },
];

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  changeType: "positive" | "negative" | "neutral";
  icon: React.ElementType;
}

function MetricCard({ title, value, change, changeType, icon: Icon }: MetricCardProps) {
  return (
    <div className="card-elevated p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-3xl font-semibold text-foreground">{value}</p>
        </div>
        <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center">
          <Icon className="w-5 h-5 text-accent-foreground" />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-1">
        {changeType === "positive" ? (
          <ArrowUp className="w-4 h-4 text-success" />
        ) : changeType === "negative" ? (
          <ArrowDown className="w-4 h-4 text-destructive" />
        ) : null}
        <span
          className={cn(
            "text-sm font-medium",
            changeType === "positive" && "text-success",
            changeType === "negative" && "text-destructive",
            changeType === "neutral" && "text-muted-foreground"
          )}
        >
          {change}
        </span>
        <span className="text-sm text-muted-foreground">vs last week</span>
      </div>
    </div>
  );
}

export function AnalyticsDashboard() {
  const totalWorkflowDuration = agentWorkflow.reduce((acc, step) => acc + step.duration, 0);

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-foreground">Analytics</h1>
          <p className="text-muted-foreground">
            Advanced metrics and insights for developers
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Avg. Improvement"
            value="22%"
            change="+4.2%"
            changeType="positive"
            icon={TrendingUp}
          />
          <MetricCard
            title="Avg. Latency"
            value="1.8s"
            change="-0.3s"
            changeType="positive"
            icon={Clock}
          />
          <MetricCard
            title="Accuracy"
            value="94%"
            change="+2.1%"
            changeType="positive"
            icon={Target}
          />
          <MetricCard
            title="Iterations"
            value="3.5"
            change="Same"
            changeType="neutral"
            icon={Zap}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quality Improvement Chart */}
          <div className="card-elevated p-6">
            <h3 className="section-title mb-1">Quality Improvement Over Iterations</h3>
            <p className="section-subtitle mb-6">Before vs after comparison</p>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={qualityData}>
                  <defs>
                    <linearGradient id="beforeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(220, 14%, 70%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(220, 14%, 70%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="afterGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(220, 70%, 50%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(220, 70%, 50%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="iteration" stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(0, 0%, 100%)",
                      border: "1px solid hsl(220, 13%, 91%)",
                      borderRadius: "8px",
                      boxShadow: "var(--shadow-md)",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="before"
                    stroke="hsl(220, 14%, 70%)"
                    fill="url(#beforeGradient)"
                    strokeWidth={2}
                    name="Before"
                  />
                  <Area
                    type="monotone"
                    dataKey="after"
                    stroke="hsl(220, 70%, 50%)"
                    fill="url(#afterGradient)"
                    strokeWidth={2}
                    name="After"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Performance Chart */}
          <div className="card-elevated p-6">
            <h3 className="section-title mb-1">Performance Metrics</h3>
            <p className="section-subtitle mb-6">Latency and accuracy over time</p>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="time" stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 46%)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(0, 0%, 100%)",
                      border: "1px solid hsl(220, 13%, 91%)",
                      borderRadius: "8px",
                      boxShadow: "var(--shadow-md)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="hsl(38, 92%, 50%)"
                    strokeWidth={2}
                    dot={false}
                    name="Latency (ms)"
                  />
                  <Line
                    type="monotone"
                    dataKey="accuracy"
                    stroke="hsl(152, 60%, 45%)"
                    strokeWidth={2}
                    dot={false}
                    name="Accuracy (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Agent Workflow Timeline */}
        <div className="card-elevated p-6">
          <h3 className="section-title mb-1">Agent Workflow Timeline</h3>
          <p className="section-subtitle mb-6">Processing steps breakdown</p>
          <div className="space-y-3">
            {agentWorkflow.map((step, index) => (
              <div key={index} className="flex items-center gap-4">
                <span className="text-sm text-muted-foreground w-36 truncate">
                  {step.step}
                </span>
                <div className="flex-1 h-6 bg-secondary rounded-lg overflow-hidden">
                  <div
                    className="h-full rounded-lg transition-all duration-500"
                    style={{
                      width: `${(step.duration / totalWorkflowDuration) * 100}%`,
                      background: `linear-gradient(90deg, hsl(220, 70%, 50%) 0%, hsl(230, 70%, 55%) 100%)`,
                    }}
                  />
                </div>
                <span className="text-sm text-muted-foreground w-16 text-right">
                  {step.duration}ms
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Learning History Table */}
        <div className="card-elevated overflow-hidden">
          <div className="p-6 border-b border-border">
            <h3 className="section-title">Learning History</h3>
            <p className="section-subtitle mt-1">Recent task improvements and performance</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-secondary/30">
                  <th className="text-left text-sm font-medium text-muted-foreground px-6 py-3">
                    Task
                  </th>
                  <th className="text-left text-sm font-medium text-muted-foreground px-6 py-3">
                    Improvement
                  </th>
                  <th className="text-left text-sm font-medium text-muted-foreground px-6 py-3">
                    Duration
                  </th>
                  <th className="text-left text-sm font-medium text-muted-foreground px-6 py-3">
                    Iterations
                  </th>
                  <th className="text-left text-sm font-medium text-muted-foreground px-6 py-3">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody>
                {learningHistory.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-border last:border-0 hover:bg-secondary/20 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm font-medium text-foreground">
                      {item.task}
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm font-medium text-success">
                        {item.improvement}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {item.duration}
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {item.iterations}
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {item.date}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
