from typing import Dict, Any, List

class RiskAnalyzer:
    def evaluate(self, dsl: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns: {"level": "low/medium/high", "score": int, "reasons": []}
        """
        score = 0
        reasons = []
        
        # 1. Size check
        size = dsl.get("size", 10)
        from_ = dsl.get("from", 0)
        if size > 200:
            score += 20
            reasons.append("Size > 200")
        if size + from_ > 10000:
            # This is hard limit usually, but here we treat as risk if not using search_after
            score += 30
            reasons.append("Deep pagination (from+size > 10000)")

        # 2. Wildcard check
        # Simplified recursive check for "wildcard" or "regexp" keys
        if self._has_key(dsl, "wildcard"):
            score += 40
            reasons.append("Wildcard query used")
        if self._has_key(dsl, "regexp"):
            score += 40
            reasons.append("Regexp query used")
            
        # 3. Script check
        if self._has_key(dsl, "script"):
            score += 40
            reasons.append("Scripting used")
            
        # 4. Aggregation depth (simple check)
        # TODO: checking nested aggs depth
        
        level = "low"
        if score >= 60:
            level = "high"
        elif score >= 30:
            level = "medium"
            
        return {
            "level": level,
            "score": score,
            "reasons": reasons
        }

    def _has_key(self, obj: Any, key: str) -> bool:
        if isinstance(obj, dict):
            if key in obj:
                return True
            return any(self._has_key(v, key) for v in obj.values())
        if isinstance(obj, list):
            return any(self._has_key(v, key) for v in obj)
        return False

risk_analyzer = RiskAnalyzer()
