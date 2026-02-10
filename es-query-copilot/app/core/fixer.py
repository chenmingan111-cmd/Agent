from app.services.es_client import es_client
from app.services.llm_client import llm_client
from app.core.prompt import REPAIR_PROMPT
from app.core.config import settings
from typing import Tuple, List, Dict, Any

class DSLFixer:
    async def validate_and_fix(self, index: str, dsl: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str], bool]:
        """
        Returns: (is_valid, final_dsl, error_list, was_fixed)
        """
        current_dsl = dsl
        was_fixed = False
        last_errors = []

        for attempt in range(settings.MAX_VALIDATE_RETRY + 1):
            # 1. Local Validation (TODO: JSON Schema or simple checks)
            # For MVP, rely on ES validate API mainly

            # 2. ES Validate
            validation_result = await es_client.validate_query(index, current_dsl)
            
            if validation_result.get("valid", False):
                return True, current_dsl, [], was_fixed
            
            # Validation failed
            error_msg = validation_result.get("error", "Unknown error")
            last_errors = [error_msg] # In reality might be list
            
            # If we have retries left, try to fix
            if attempt < settings.MAX_VALIDATE_RETRY:
                try:
                    prompt = REPAIR_PROMPT.format(error=error_msg, dsl=str(current_dsl))
                    # Reuse LLM generating JSON, but prompt is different
                    # We might need a separate method if we want just pure JSON back without wrappers
                    # But generate_json handles it fine if LLM adheres to instruction
                    fixed_result = await llm_client.generate_json(
                        system_prompt="You are a JSON fixer.",
                        user_prompt=prompt,
                        temperature=0.0
                    )
                    # Support both direct JSON or wrapped in "dsl" key
                    if "dsl" in fixed_result:
                        current_dsl = fixed_result["dsl"]
                    else:
                        current_dsl = fixed_result
                    
                    was_fixed = True
                except Exception:
                    # If fixing fails (LLM error), abort fixing and return failure
                    break
        
        return False, current_dsl, last_errors, was_fixed

dsl_fixer = DSLFixer()
