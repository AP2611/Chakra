"""Smriti - Memory Agent that stores and retrieves learning experiences."""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import pymysql
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Smriti:
    """Memory agent for persistent learning using MySQL."""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'chakra_user'),
            'password': os.getenv('DB_PASSWORD', 'chakra_password'),
            'database': os.getenv('DB_NAME', 'chakra_db'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self._init_db()
    
    def _get_connection(self):
        """Get a MySQL database connection."""
        return pymysql.connect(**self.db_config)
    
    def _init_db(self):
        """Initialize the memory database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task_hash VARCHAR(64) UNIQUE NOT NULL,
                    task TEXT NOT NULL,
                    task_embedding TEXT,
                    solution TEXT NOT NULL,
                    quality_score FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    INDEX idx_task_hash (task_hash),
                    INDEX idx_quality_score (quality_score)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            print("Make sure MySQL is running and the database is created.")
            raise
    
    def _hash_task(self, task: str) -> str:
        """Create a hash of the task for deduplication."""
        return hashlib.md5(task.encode()).hexdigest()
    
    def store(
        self,
        task: str,
        solution: str,
        quality_score: float,
        task_embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store a successful solution."""
        task_hash = self._hash_task(task)
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if task already exists
            cursor.execute(
                "SELECT quality_score FROM memories WHERE task_hash = %s",
                (task_hash,)
            )
            existing = cursor.fetchone()
            
            task_embedding_json = json.dumps(task_embedding) if task_embedding else None
            metadata_json = json.dumps(metadata) if metadata else None
            
            if existing:
                # Only update if new score is better
                if quality_score > existing['quality_score']:
                    cursor.execute("""
                        UPDATE memories 
                        SET solution = %s, quality_score = %s, task_embedding = %s, metadata = %s
                        WHERE task_hash = %s
                    """, (
                        solution,
                        quality_score,
                        task_embedding_json,
                        metadata_json,
                        task_hash
                    ))
            else:
                # Insert new memory
                cursor.execute("""
                    INSERT INTO memories (task_hash, task, task_embedding, solution, quality_score, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    task_hash,
                    task,
                    task_embedding_json,
                    solution,
                    quality_score,
                    metadata_json
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error storing memory: {e}")
            raise
    
    def retrieve_similar(
        self,
        task: str,
        limit: int = 3,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Retrieve similar past tasks and their solutions."""
        # Simple text-based similarity (can be enhanced with embeddings)
        task_lower = task.lower()
        task_words = set(task_lower.split())
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task, solution, quality_score, metadata
                FROM memories
                WHERE quality_score >= %s
                ORDER BY quality_score DESC
                LIMIT %s
            """, (min_score, limit * 2))  # Get more, then filter
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Simple similarity scoring
            similar = []
            for row in results:
                stored_task = row['task']
                solution = row['solution']
                score = row['quality_score']
                metadata = row['metadata']
                
                stored_words = set(stored_task.lower().split())
                # Jaccard similarity
                intersection = len(task_words & stored_words)
                union = len(task_words | stored_words)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0.2:  # Threshold for similarity
                    similar.append({
                        "task": stored_task,
                        "solution": solution,
                        "quality_score": score,
                        "similarity": similarity,
                        "metadata": json.loads(metadata) if metadata else {}
                    })
            
            # Sort by similarity and score, return top results
            similar.sort(key=lambda x: (x["similarity"], x["quality_score"]), reverse=True)
            return similar[:limit]
        except Exception as e:
            print(f"Error retrieving similar memories: {e}")
            return []
    
    def get_best_examples(self, limit: int = 5) -> List[str]:
        """Get the best solutions regardless of similarity."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT solution
                FROM memories
                ORDER BY quality_score DESC
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [row['solution'] for row in results]
        except Exception as e:
            print(f"Error retrieving best examples: {e}")
            return []
