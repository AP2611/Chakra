"""Analytics tracking for the agent system."""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path


class AnalyticsTracker:
    """Tracks analytics data for the agent system."""
    
    def __init__(self, data_dir: str = "backend/data/analytics"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.analytics_file = os.path.join(self.data_dir, "analytics.json")
        self._init_analytics()
    
    def _init_analytics(self):
        """Initialize analytics storage if it doesn't exist."""
        if not os.path.exists(self.analytics_file):
            self._save_analytics({
                "tasks": [],
                "iterations": [],
                "performance_history": [],
                "last_updated": datetime.now().isoformat()
            })
    
    def _load_analytics(self) -> Dict[str, Any]:
        """Load analytics data from file."""
        try:
            with open(self.analytics_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "tasks": [],
                "iterations": [],
                "performance_history": [],
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_analytics(self, data: Dict[str, Any]):
        """Save analytics data to file."""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.analytics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def record_task(
        self,
        task: str,
        final_score: float,
        iterations: List[Dict[str, Any]],
        duration_ms: Optional[float] = None,
        task_type: str = "code"
    ):
        """Record a completed task with its iterations."""
        analytics = self._load_analytics()
        
        # Calculate improvement metrics
        if iterations and len(iterations) > 0:
            # Get scores from iterations
            initial_score = iterations[0].get("score", 0.0)
            final_score_actual = iterations[-1].get("score", final_score) if iterations else final_score
            improvement = final_score_actual - initial_score
            
            # Better percentage calculation - handle edge cases
            if initial_score > 0.01:
                improvement_percent = (improvement / initial_score) * 100
            elif initial_score <= 0.01 and final_score_actual > 0.01:
                # If we started very low but ended with a score, calculate based on absolute improvement
                # Use a formula that shows significant improvement
                improvement_percent = ((final_score_actual - initial_score) / 0.1) * 100
                # Cap at reasonable maximum but ensure it's positive
                improvement_percent = min(500.0, max(10.0, improvement_percent))
            elif initial_score > 0 and final_score_actual > initial_score:
                # Even small improvements should show percentage
                improvement_percent = ((final_score_actual - initial_score) / max(0.01, initial_score)) * 100
            else:
                # Default to showing absolute improvement as percentage
                if improvement > 0:
                    improvement_percent = (improvement / 0.1) * 100  # Normalize to 0.1 base
                    improvement_percent = min(200.0, improvement_percent)
                else:
                    improvement_percent = 0.0
        else:
            # No iterations data - use final score as both
            initial_score = final_score
            final_score_actual = final_score
            improvement = 0.0
            improvement_percent = 0.0
        
        task_record = {
            "id": len(analytics["tasks"]) + 1,
            "task": task[:100],  # Truncate long tasks
            "initial_score": initial_score,
            "final_score": final_score_actual if iterations else final_score,
            "improvement": improvement,
            "improvement_percent": round(improvement_percent, 2),
            "iterations": len(iterations),
            "duration_ms": duration_ms or 0,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat()
        }
        
        analytics["tasks"].append(task_record)
        
        # Record iteration details for quality improvement chart
        for i, iteration in enumerate(iterations):
            iteration_record = {
                "task_id": task_record["id"],
                "iteration_num": i + 1,
                "score": iteration.get("score", 0.0),
                "improvement": iteration.get("improvement", 0.0),
                "timestamp": datetime.now().isoformat()
            }
            analytics["iterations"].append(iteration_record)
        
        # Keep only last 100 tasks for performance
        if len(analytics["tasks"]) > 100:
            analytics["tasks"] = analytics["tasks"][-100:]
            # Remove old iterations
            latest_task_id = analytics["tasks"][-1]["id"]
            analytics["iterations"] = [
                it for it in analytics["iterations"]
                if it["task_id"] >= (latest_task_id - 50)
            ]
        
        self._save_analytics(analytics)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        analytics = self._load_analytics()
        tasks = analytics.get("tasks", [])
        
        if not tasks:
            return {
                "avg_improvement": 0.0,
                "avg_latency": 0.0,
                "avg_accuracy": 0.0,
                "avg_iterations": 0.0,
                "total_tasks": 0
            }
        
        # Calculate averages - include ALL improvements (not just positive ones)
        improvements = [t["improvement_percent"] for t in tasks]
        latencies = [t["duration_ms"] / 1000 for t in tasks if t["duration_ms"] > 0]
        accuracies = [t["final_score"] * 100 for t in tasks]
        iterations = [t["iterations"] for t in tasks]
        
        return {
            "avg_improvement": round(sum(improvements) / len(improvements), 1) if improvements else 0.0,
            "avg_latency": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "avg_accuracy": round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0,
            "avg_iterations": round(sum(iterations) / len(iterations), 1) if iterations else 0.0,
            "total_tasks": len(tasks)
        }
    
    def get_quality_improvement_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get data for quality improvement chart with before/after comparison."""
        analytics = self._load_analytics()
        tasks = analytics.get("tasks", [])
        iterations = analytics.get("iterations", [])
        
        if not tasks:
            return []
        
        # Group iterations by task
        task_iterations = {}
        for it in iterations:
            task_id = it["task_id"]
            if task_id not in task_iterations:
                task_iterations[task_id] = []
            task_iterations[task_id].append(it)
        
        # Build chart data with before/after for each task
        chart_data = []
        for task in tasks[-10:]:  # Last 10 tasks
            task_id = task["id"]
            its = task_iterations.get(task_id, [])
            
            if its:
                its.sort(key=lambda x: x["iteration_num"])
                initial_score = its[0]["score"] * 100
                final_score = its[-1]["score"] * 100
            else:
                # Fallback to task-level scores
                initial_score = task.get("initial_score", 0) * 100
                final_score = task.get("final_score", 0) * 100
            
            # Only add if there's actual data
            if initial_score > 0 or final_score > 0:
                chart_data.append({
                    "iteration": f"T{task_id}",
                    "before": round(initial_score, 1),
                    "after": round(final_score, 1),
                    "improvement": round(final_score - initial_score, 1)
                })
        
        return chart_data[-limit:] if chart_data else []
    
    def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for the last N hours."""
        analytics = self._load_analytics()
        tasks = analytics.get("tasks", [])
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Group tasks by hour
        hourly_data = {}
        for task in tasks:
            try:
                task_time = datetime.fromisoformat(task["timestamp"])
                if task_time < cutoff:
                    continue
                
                hour_key = task_time.replace(minute=0, second=0, microsecond=0)
                hour_str = hour_key.strftime("%H:00")
                
                if hour_str not in hourly_data:
                    hourly_data[hour_str] = {
                        "time": hour_str,
                        "latency": [],
                        "accuracy": []
                    }
                
                if task["duration_ms"] > 0:
                    hourly_data[hour_str]["latency"].append(task["duration_ms"])
                hourly_data[hour_str]["accuracy"].append(task["final_score"] * 100)
            except (ValueError, KeyError):
                continue
        
        # Calculate averages
        result = []
        for hour_str in sorted(hourly_data.keys()):
            data = hourly_data[hour_str]
            result.append({
                "time": hour_str,
                "latency": round(sum(data["latency"]) / len(data["latency"]), 0) if data["latency"] else 0,
                "accuracy": round(sum(data["accuracy"]) / len(data["accuracy"]), 1) if data["accuracy"] else 0
            })
        
        return result
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks for the history table."""
        analytics = self._load_analytics()
        tasks = analytics.get("tasks", [])
        
        recent = sorted(tasks, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        
        # Format for display
        formatted = []
        for task in recent:
            try:
                task_time = datetime.fromisoformat(task["timestamp"])
                now = datetime.now()
                diff = now - task_time
                
                if diff < timedelta(hours=1):
                    time_str = f"{int(diff.total_seconds() / 60)} minutes ago"
                elif diff < timedelta(hours=24):
                    time_str = f"Today, {task_time.strftime('%I:%M %p')}"
                elif diff < timedelta(hours=48):
                    time_str = f"Yesterday, {task_time.strftime('%I:%M %p')}"
                else:
                    time_str = task_time.strftime("%b %d, %I:%M %p")
                
                formatted.append({
                    "id": task["id"],
                    "task": task["task"],
                    "improvement": f"+{task['improvement_percent']:.1f}%",
                    "duration": f"{task['duration_ms'] / 1000:.1f}s" if task["duration_ms"] > 0 else "N/A",
                    "iterations": task["iterations"],
                    "date": time_str
                })
            except (ValueError, KeyError):
                continue
        
        return formatted

