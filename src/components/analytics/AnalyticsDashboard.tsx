import { useState, useEffect } from "react";
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
  BarChart,
  Bar,
  Legend,
} from "recharts";
import { cn } from "@/lib/utils";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
        <span className="text-sm text-muted-foreground">vs last session</span>
      </div>
    </div>
  );
}

interface Metrics {
  avg_improvement: number;
  avg_latency: number;
  avg_accuracy: number;
  avg_iterations: number;
  total_tasks: number;
}

interface QualityData {
  iteration: string;
  before: number;
  after: number;
  improvement: number;
}

interface PerformanceData {
  time: string;
  latency: number;
  accuracy: number;
}

interface RecentTask {
  id: number;
  task: string;
  improvement: string;
  duration: string;
  iterations: number;
  date: string;
}

export function AnalyticsDashboard() {
  const [metrics, setMetrics] = useState<Metrics>({
    avg_improvement: 0,
    avg_latency: 0,
    avg_accuracy: 0,
    avg_iterations: 0,
    total_tasks: 0,
  });
  const [qualityData, setQualityData] = useState<QualityData[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchAnalytics = async () => {
    try {
      // Fetch all analytics data in parallel
      const [metricsRes, qualityRes, performanceRes, tasksRes] = await Promise.all([
        fetch(`${API_URL}/analytics/metrics`),
        fetch(`${API_URL}/analytics/quality-improvement`),
        fetch(`${API_URL}/analytics/performance-history`),
        fetch(`${API_URL}/analytics/recent-tasks`),
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (qualityRes.ok) {
        const qualityDataRes = await qualityRes.json();
        setQualityData(qualityDataRes.data || []);
      }

      if (performanceRes.ok) {
        const performanceDataRes = await performanceRes.json();
        setPerformanceData(performanceDataRes.data || []);
      }

      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        setRecentTasks(tasksData.data || []);
      }

      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error("Error fetching analytics:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchAnalytics();

    // Poll for updates every 3 seconds for real-time updates
    const interval = setInterval(fetchAnalytics, 3000);

    return () => clearInterval(interval);
  }, []);

  // Calculate change indicators (simplified - compare with previous values)
  const getChangeType = (value: number, threshold: number = 0): "positive" | "negative" | "neutral" => {
    if (value > threshold) return "positive";
    if (value < threshold) return "negative";
    return "neutral";
  };

  // Format quality data for chart with before/after
  const formattedQualityData = qualityData.length > 0
    ? qualityData.map((item) => ({
        iteration: item.iteration,
        before: item.before,
        after: item.after,
        improvement: item.improvement,
      }))
    : [];

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold text-foreground">Analytics</h1>
            <p className="text-muted-foreground">
              Real-time metrics and insights for the agent system
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
            {loading && <span className="ml-2 animate-pulse">🔄</span>}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Avg. Improvement"
            value={`${metrics.avg_improvement.toFixed(1)}%`}
            change={`${metrics.avg_improvement > 0 ? '+' : ''}${metrics.avg_improvement.toFixed(1)}%`}
            changeType={metrics.avg_improvement > 0 ? "positive" : "neutral"}
            icon={TrendingUp}
          />
          <MetricCard
            title="Avg. Latency"
            value={`${metrics.avg_latency.toFixed(1)}s`}
            change={metrics.avg_latency > 0 ? `${metrics.avg_latency.toFixed(1)}s` : "N/A"}
            changeType={metrics.avg_latency > 0 && metrics.avg_latency < 5 ? "positive" : "neutral"}
            icon={Clock}
          />
          <MetricCard
            title="Accuracy"
            value={`${metrics.avg_accuracy.toFixed(1)}%`}
            change={`${metrics.avg_accuracy > 0 ? '+' : ''}${metrics.avg_accuracy.toFixed(1)}%`}
            changeType={getChangeType(metrics.avg_accuracy - 80)}
            icon={Target}
          />
          <MetricCard
            title="Total Tasks"
            value={metrics.total_tasks.toString()}
            change={metrics.total_tasks > 0 ? `${metrics.total_tasks} tasks` : "No tasks yet"}
            changeType="neutral"
            icon={Zap}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quality Improvement Chart */}
          <div className="card-elevated p-6">
            <h3 className="section-title mb-1">Quality Improvement Over Iterations</h3>
            <p className="section-subtitle mb-6">Before vs After comparison</p>
            <div className="h-64">
              {formattedQualityData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={formattedQualityData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                    <XAxis 
                      dataKey="iteration" 
                      stroke="hsl(220, 10%, 46%)" 
                      fontSize={11}
                      angle={-45}
                      textAnchor="end"
                      height={70}
                    />
                    <YAxis 
                      stroke="hsl(220, 10%, 46%)" 
                      fontSize={12} 
                      domain={[0, 100]}
                      label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(0, 0%, 100%)",
                        border: "1px solid hsl(220, 13%, 91%)",
                        borderRadius: "8px",
                        boxShadow: "var(--shadow-md)",
                      }}
                      formatter={(value: number, name: string) => {
                        if (name === "improvement") {
                          return [`+${value.toFixed(1)}%`, "Improvement"];
                        }
                        return [`${value.toFixed(1)}%`, name === "before" ? "Before" : "After"];
                      }}
                    />
                    <Legend />
                    <Bar 
                      dataKey="before" 
                      fill="hsl(220, 14%, 70%)" 
                      name="Before"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar 
                      dataKey="after" 
                      fill="hsl(142, 71%, 45%)" 
                      name="After"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  No data yet. Process some tasks to see quality improvements.
                </div>
              )}
            </div>
          </div>

          {/* Performance Chart */}
          <div className="card-elevated p-6">
            <h3 className="section-title mb-1">Performance Metrics</h3>
            <p className="section-subtitle mb-6">Latency and accuracy over time</p>
            <div className="h-64">
              {performanceData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                    <XAxis dataKey="time" stroke="hsl(220, 10%, 46%)" fontSize={12} />
                    <YAxis 
                      yAxisId="left"
                      stroke="hsl(38, 92%, 50%)" 
                      fontSize={12}
                      label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
                    />
                    <YAxis 
                      yAxisId="right"
                      orientation="right"
                      stroke="hsl(152, 60%, 45%)" 
                      fontSize={12}
                      domain={[0, 100]}
                      label={{ value: 'Accuracy (%)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle' } }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(0, 0%, 100%)",
                        border: "1px solid hsl(220, 13%, 91%)",
                        borderRadius: "8px",
                        boxShadow: "var(--shadow-md)",
                      }}
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="latency"
                      stroke="hsl(38, 92%, 50%)"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      name="Latency (ms)"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="accuracy"
                      stroke="hsl(152, 60%, 45%)"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      name="Accuracy (%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  No performance data yet. Process some tasks to see metrics.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Learning History Table */}
        <div className="card-elevated overflow-hidden">
          <div className="p-6 border-b border-border">
            <h3 className="section-title">Learning History</h3>
            <p className="section-subtitle mt-1">Recent task improvements and performance</p>
          </div>
          <div className="overflow-x-auto">
            {recentTasks.length > 0 ? (
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
                  {recentTasks.map((item) => (
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
            ) : (
              <div className="p-12 text-center text-muted-foreground">
                No tasks processed yet. Start using the Code Assistant or Document Assistant to see analytics.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
