"""Evaluation engine for scoring solutions."""
import re
from typing import Dict, Any, Optional, List


class Evaluator:
    """Evaluates solution quality."""
    
    def __init__(self):
        self.code_patterns = {
            "has_comments": r"#.*|//.*|/\*.*?\*/",
            "has_docstrings": r'""".*?"""|\'\'\'.*?\'\'\'',
            "has_error_handling": r"try:|except:|catch\s*\(",
            "has_type_hints": r"def\s+\w+\s*\([^)]*:\s*\w+",
        }
    
    def evaluate_code(
        self,
        code: str,
        task: str,
        rag_chunks: Optional[List[str]] = None,
        iteration_num: int = 0
    ) -> Dict[str, Any]:
        """Evaluate code solution with stricter scoring."""
        # Start with VERY low base scores - force improvement
        scores = {
            "correctness": 0.1,  # Very low base score
            "quality": 0.05,      # Extremely low base
            "completeness": 0.05,  # Very low base
            "total": 0.07        # Very low total base
        }
        
        task_lower = task.lower()
        
        # Check for code structure - give minimal points
        if "def " in code or "function " in code or "class " in code:
            scores["completeness"] += 0.05
            scores["correctness"] += 0.05
        
        # Check for best practices - require MORE for higher scores
        has_error_handling = bool(re.search(self.code_patterns["has_error_handling"], code, re.DOTALL))
        has_type_hints = bool(re.search(self.code_patterns["has_type_hints"], code, re.DOTALL))
        has_docstrings = bool(re.search(self.code_patterns["has_docstrings"], code, re.DOTALL))
        has_comments = bool(re.search(self.code_patterns["has_comments"], code, re.DOTALL))
        
        # Require multiple best practices for good scores - more points per practice
        best_practices_count = sum([has_error_handling, has_type_hints, has_docstrings, has_comments])
        # Each practice adds significant points - encourages adding them
        scores["quality"] += (best_practices_count * 0.2)  # Max 0.8 from best practices
        
        # Bonus for having ALL best practices
        if best_practices_count == 4:
            scores["quality"] += 0.1
        
        # Check for imports
        if re.search(r"^import\s+|^from\s+", code, re.MULTILINE):
            scores["quality"] += 0.05
        
        # Check for tests - give significant points
        test_count = len(re.findall(r"def test_|@pytest\.|unittest\.|assert\s+", code, re.IGNORECASE))
        if test_count > 0:
            scores["quality"] += 0.15
            scores["completeness"] += 0.15
            # Bonus for multiple tests
            if test_count >= 3:
                scores["quality"] += 0.1
                scores["completeness"] += 0.1
        
        # Check for comprehensive error handling - give more points
        if has_error_handling and re.search(r"ValueError|TypeError|Exception|raise\s+", code):
            scores["correctness"] += 0.2
            scores["quality"] += 0.1
        
        # Check for multiple error types (comprehensive error handling)
        error_types = len(re.findall(r"ValueError|TypeError|KeyError|IndexError|AttributeError|Exception", code))
        if error_types >= 2:
            scores["correctness"] += 0.1
        
        # Check if task requirements are met
        requirements_met = 0
        total_requirements = 0
        
        # Check for common requirements in task
        if "error handling" in task_lower or "handle" in task_lower or "exception" in task_lower:
            total_requirements += 1
            if has_error_handling and re.search(r"try:|except:|if.*error|if.*None|if.*empty", code, re.IGNORECASE):
                requirements_met += 1
                scores["correctness"] += 0.1
                scores["completeness"] += 0.05
        
        if "type" in task_lower and ("hint" in task_lower or "annotation" in task_lower):
            total_requirements += 1
            if has_type_hints:
                requirements_met += 1
                scores["quality"] += 0.1
        
        if "test" in task_lower or "unit" in task_lower:
            total_requirements += 1
            if re.search(r"def test_|@pytest|unittest|assert\s+", code, re.IGNORECASE):
                requirements_met += 1
                scores["completeness"] += 0.1
                scores["quality"] += 0.05
        
        if "optimize" in task_lower or "performance" in task_lower or "efficient" in task_lower:
            total_requirements += 1
            # Check for optimization patterns
            if re.search(r"cache|memoize|@lru_cache|O\(|complexity|optimize", code, re.IGNORECASE):
                requirements_met += 1
                scores["quality"] += 0.1
        
        if "docstring" in task_lower or "documentation" in task_lower or "doc" in task_lower:
            total_requirements += 1
            if has_docstrings:
                requirements_met += 1
                scores["quality"] += 0.08
        
        if "validate" in task_lower or "validation" in task_lower:
            total_requirements += 1
            if re.search(r"if.*is None|if.*not|if.*empty|validate|check", code, re.IGNORECASE):
                requirements_met += 1
                scores["correctness"] += 0.1
        
        # Bonus for meeting all requirements
        if total_requirements > 0:
            requirement_score = requirements_met / total_requirements
            scores["completeness"] += requirement_score * 0.2
        
        # Check for code quality indicators
        if re.search(r"TODO|FIXME|XXX|HACK", code, re.IGNORECASE):
            scores["quality"] -= 0.05  # Penalty for TODOs
        
        # Check for proper structure
        if re.search(r"if __name__|main\(\)", code, re.IGNORECASE):
            scores["completeness"] += 0.05
        
        # Normalize scores
        scores["correctness"] = min(1.0, max(0.0, scores["correctness"]))
        scores["quality"] = min(1.0, max(0.0, scores["quality"]))
        scores["completeness"] = min(1.0, max(0.0, scores["completeness"]))
        
        # Calculate total (weighted average)
        scores["total"] = (
            scores["correctness"] * 0.4 +
            scores["quality"] * 0.4 +      # Increased weight for quality
            scores["completeness"] * 0.2
        )
        
        # Ensure minimum score is very low to force improvement
        scores["total"] = max(0.05, min(1.0, scores["total"]))
        
        # Add iteration-based bonus (encourages multiple iterations)
        # Later iterations get a small bonus for trying to improve
        if iteration_num > 0:
            scores["total"] += min(0.05, iteration_num * 0.01)
            scores["total"] = min(1.0, scores["total"])
        
        return scores
    
    def evaluate_rag_answer(
        self,
        answer: str,
        rag_chunks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate RAG-based answer."""
        scores = {
            "grounding": 0.5,
            "clarity": 0.5,
            "completeness": 0.5,
            "total": 0.5
        }
        
        if not rag_chunks:
            return scores
        
        # Check grounding - simple keyword matching
        answer_lower = answer.lower()
        chunk_text = " ".join(rag_chunks).lower()
        
        answer_words = set(answer_lower.split())
        chunk_words = set(chunk_text.split())
        
        # Calculate overlap
        overlap = len(answer_words & chunk_words)
        total_unique = len(answer_words | chunk_words)
        
        if total_unique > 0:
            grounding_score = overlap / total_unique
            scores["grounding"] = min(1.0, grounding_score * 2)  # Scale up
        
        # Check for citations or references
        if re.search(r"\[.*?\]|\(.*?\)|source|document|according", answer_lower):
            scores["grounding"] += 0.2
        
        # Clarity - check for structure
        if len(answer.split("\n")) > 3:
            scores["clarity"] += 0.2
        
        if re.search(r"\*\*.*?\*\*|#+\s+", answer):  # Markdown formatting
            scores["clarity"] += 0.1
        
        # Normalize
        scores["grounding"] = min(1.0, scores["grounding"])
        scores["clarity"] = min(1.0, scores["clarity"])
        scores["completeness"] = min(1.0, scores["completeness"])
        
        # Total score
        scores["total"] = (
            scores["grounding"] * 0.5 +
            scores["clarity"] * 0.3 +
            scores["completeness"] * 0.2
        )
        
        return scores
    
    def evaluate(
        self,
        solution: str,
        task: str,
        is_code: bool = True,
        rag_chunks: Optional[List[str]] = None,
        iteration_num: int = 0
    ) -> Dict[str, Any]:
        """Main evaluation method."""
        if is_code:
            return self.evaluate_code(solution, task, rag_chunks, iteration_num)
        else:
            return self.evaluate_rag_answer(solution, rag_chunks)

