"""Analytics tracking for the agent system using Redis."""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AnalyticsTracker:
    """Tracks analytics data for the agent system using Redis."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection."""
        # Get Redis connection details from environment or use defaults
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,  # Automatically decode responses to strings
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print(f"✓ Connected to Redis at {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            print(f"⚠️ Warning: Could not connect to Redis: {e}")
            print("⚠️ Analytics will not be stored. Make sure Redis is running.")
            self.redis_client = None
        except Exception as e:
            print(f"⚠️ Warning: Redis initialization error: {e}")
            self.redis_client = None
    
    def _is_connected(self) -> bool:
        """Check if Redis is connected."""
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _get_next_task_id(self) -> int:
        """Get the next task ID using Redis INCR."""
        if not self._is_connected():
            return 1
        try:
            return self.redis_client.incr("analytics:task_counter")
        except:
            return 1
    
    def _get_task_ids(self, limit: int = 100) -> List[int]:
        """Get list of recent task IDs."""
        if not self._is_connected():
            return []
        try:
            # Get last N task IDs from sorted set (ordered by timestamp)
            task_ids = self.redis_client.zrevrange("analytics:task_ids", 0, limit - 1)
            return [int(tid) for tid in task_ids]
        except:
            return []
    
    def record_task(
        self,
        task: str,
        final_score: float,
        iterations: List[Dict[str, Any]],
        duration_ms: Optional[float] = None,
        task_type: str = "code"
    ):
        """Record a completed task with its iterations."""
        if not self._is_connected():
            print("⚠️ Redis not connected, skipping analytics recording")
            return
        
        try:
            # Calculate improvement metrics based on Yantra vs Agni scores
            if iterations and len(iterations) > 0:
                # Get Yantra and Agni scores from first iteration
                first_iteration = iterations[0]
                yantra_score = first_iteration.get("yantra_score", 0.0)
                agni_score = first_iteration.get("agni_score", first_iteration.get("score", final_score))
                
                # If yantra_score not explicitly stored, try to get from score or use first score as fallback
                if yantra_score == 0.0 and "yantra_score" not in first_iteration:
                    # Fallback: use first score as yantra_score if not explicitly stored
                    yantra_score = first_iteration.get("score", 0.0)
                
                # If agni_score not explicitly stored, use final score
                if agni_score == 0.0 and "agni_score" not in first_iteration:
                    agni_score = first_iteration.get("score", final_score)
                
                improvement = agni_score - yantra_score
                
                # Calculate improvement percentage: (Agni - Yantra) / Yantra * 100
                if yantra_score > 0.01:
                    improvement_percent = (improvement / yantra_score) * 100
                elif yantra_score <= 0.01 and agni_score > 0.01:
                    improvement_percent = ((agni_score - yantra_score) / 0.1) * 100
                    improvement_percent = min(500.0, max(10.0, improvement_percent))
                elif yantra_score > 0 and agni_score > yantra_score:
                    improvement_percent = ((agni_score - yantra_score) / max(0.01, yantra_score)) * 100
                else:
                    if improvement > 0:
                        improvement_percent = (improvement / 0.1) * 100
                        improvement_percent = min(200.0, improvement_percent)
                    else:
                        improvement_percent = 0.0
                
                # Use yantra_score as initial_score and agni_score as final_score for analytics
                initial_score = yantra_score
                final_score_actual = agni_score
            else:
                initial_score = final_score
                final_score_actual = final_score
                improvement = 0.0
                improvement_percent = 0.0
            
            # Get next task ID
            task_id = self._get_next_task_id()
            timestamp = datetime.now().isoformat()
            
            # Store task data in Redis Hash
            task_record = {
                "id": str(task_id),
                "task": task[:100],  # Truncate long tasks
                "initial_score": str(initial_score),
                "final_score": str(final_score_actual if iterations else final_score),
                "improvement": str(improvement),
                "improvement_percent": str(round(improvement_percent, 2)),
                "iterations": str(len(iterations)),
                "duration_ms": str(duration_ms or 0),
                "task_type": task_type,
                "timestamp": timestamp
            }
            
            # Store task in Redis Hash
            self.redis_client.hset(f"analytics:task:{task_id}", mapping=task_record)
            
            # Add task ID to sorted set (for ordering by timestamp)
            timestamp_float = datetime.now().timestamp()
            self.redis_client.zadd("analytics:task_ids", {str(task_id): timestamp_float})
            
            # Record iteration details
            for i, iteration in enumerate(iterations):
                iteration_record = {
                    "task_id": str(task_id),
                    "iteration_num": str(i + 1),
                    "score": str(iteration.get("score", 0.0)),
                    "improvement": str(iteration.get("improvement", 0.0)),
                    "timestamp": timestamp
                }
                # Store iteration in Redis Hash
                self.redis_client.hset(f"analytics:iteration:{task_id}:{i+1}", mapping=iteration_record)
                # Add to list of iterations for this task
                self.redis_client.sadd(f"analytics:task:{task_id}:iterations", str(i + 1))
            
            # Keep only last 100 tasks (cleanup old tasks)
            task_ids = self._get_task_ids(limit=100)
            if len(task_ids) > 100:
                # Remove oldest tasks
                old_task_ids = task_ids[100:]
                for old_id in old_task_ids:
                    # Remove task hash
                    self.redis_client.delete(f"analytics:task:{old_id}")
                    # Remove task ID from sorted set
                    self.redis_client.zrem("analytics:task_ids", str(old_id))
                    # Remove iterations
                    iteration_keys = self.redis_client.smembers(f"analytics:task:{old_id}:iterations")
                    for iter_num in iteration_keys:
                        self.redis_client.delete(f"analytics:iteration:{old_id}:{iter_num}")
                    self.redis_client.delete(f"analytics:task:{old_id}:iterations")
            
        except Exception as e:
            print(f"⚠️ Error recording task to Redis: {e}")
    
    def _get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        if not self._is_connected():
            return None
        try:
            task_data = self.redis_client.hgetall(f"analytics:task:{task_id}")
            if not task_data:
                return None
            # Convert string values back to appropriate types
            return {
                "id": int(task_data.get("id", 0)),
                "task": task_data.get("task", ""),
                "initial_score": float(task_data.get("initial_score", 0.0)),
                "final_score": float(task_data.get("final_score", 0.0)),
                "improvement": float(task_data.get("improvement", 0.0)),
                "improvement_percent": float(task_data.get("improvement_percent", 0.0)),
                "iterations": int(task_data.get("iterations", 0)),
                "duration_ms": float(task_data.get("duration_ms", 0.0)),
                "task_type": task_data.get("task_type", "code"),
                "timestamp": task_data.get("timestamp", "")
            }
        except Exception as e:
            print(f"⚠️ Error getting task from Redis: {e}")
            return None
    
    def _get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from Redis."""
        if not self._is_connected():
            return []
        try:
            task_ids = self._get_task_ids(limit=100)
            tasks = []
            for task_id in task_ids:
                task = self._get_task(task_id)
                if task:
                    tasks.append(task)
            return tasks
        except Exception as e:
            print(f"⚠️ Error getting all tasks from Redis: {e}")
            return []
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        if not self._is_connected():
            return {
                "avg_improvement": 0.0,
                "avg_latency": 0.0,
                "avg_accuracy": 0.0,
                "avg_iterations": 0.0,
                "total_tasks": 0
            }
        
        try:
            tasks = self._get_all_tasks()
            
            if not tasks:
                return {
                    "avg_improvement": 0.0,
                    "avg_latency": 0.0,
                    "avg_accuracy": 0.0,
                    "avg_iterations": 0.0,
                    "total_tasks": 0
                }
            
            # Calculate averages
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
        except Exception as e:
            print(f"⚠️ Error getting metrics from Redis: {e}")
            return {
                "avg_improvement": 0.0,
                "avg_latency": 0.0,
                "avg_accuracy": 0.0,
                "avg_iterations": 0.0,
                "total_tasks": 0
            }
    
    def get_quality_improvement_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get data for quality improvement chart with before/after comparison."""
        if not self._is_connected():
            return []
        
        try:
            tasks = self._get_all_tasks()
            if not tasks:
                return []
            
            # Get iterations for each task
            task_iterations = {}
            for task in tasks[-10:]:  # Last 10 tasks
                task_id = task["id"]
                iterations = []
                try:
                    iter_nums = self.redis_client.smembers(f"analytics:task:{task_id}:iterations")
                    for iter_num in iter_nums:
                        iter_data = self.redis_client.hgetall(f"analytics:iteration:{task_id}:{iter_num}")
                        if iter_data:
                            iterations.append({
                                "task_id": int(iter_data.get("task_id", 0)),
                                "iteration_num": int(iter_data.get("iteration_num", 0)),
                                "score": float(iter_data.get("score", 0.0)),
                                "improvement": float(iter_data.get("improvement", 0.0)),
                                "timestamp": iter_data.get("timestamp", "")
                            })
                except:
                    pass
                
                if iterations:
                    iterations.sort(key=lambda x: x["iteration_num"])
                    task_iterations[task_id] = iterations
            
            # Build chart data
            chart_data = []
            for task in tasks[-10:]:
                task_id = task["id"]
                its = task_iterations.get(task_id, [])
                
                if its:
                    initial_score = its[0]["score"] * 100
                    final_score = its[-1]["score"] * 100
                else:
                    initial_score = task.get("initial_score", 0) * 100
                    final_score = task.get("final_score", 0) * 100
                
                if initial_score > 0 or final_score > 0:
                    chart_data.append({
                        "iteration": f"T{task_id}",
                        "before": round(initial_score, 1),
                        "after": round(final_score, 1),
                        "improvement": round(final_score - initial_score, 1)
                    })
            
            return chart_data[-limit:] if chart_data else []
        except Exception as e:
            print(f"⚠️ Error getting quality improvement data from Redis: {e}")
            return []
    
    def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for the last N hours."""
        if not self._is_connected():
            return []
        
        try:
            tasks = self._get_all_tasks()
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
        except Exception as e:
            print(f"⚠️ Error getting performance history from Redis: {e}")
            return []
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks for the history table."""
        if not self._is_connected():
            return []
        
        try:
            tasks = self._get_all_tasks()
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
        except Exception as e:
            print(f"⚠️ Error getting recent tasks from Redis: {e}")
            return []
