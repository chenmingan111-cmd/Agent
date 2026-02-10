import json
import os
from typing import Dict, Any

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "../../data/field_catalog.json")

class FieldCatalog:
    def __init__(self, path: str = DEFAULT_PATH):
        self.catalog = {}
        self.load(path)

    def load(self, path: str):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)
        else:
            # Fallback for dev/first run
            print(f"Warning: Field catalog not found at {path}")

    def get_index_fields(self, index: str) -> Dict[str, Any]:
        # Exact match
        if index in self.catalog:
            return self.catalog[index]
        # Or return first key if only one exists (simple MVP logic)
        if len(self.catalog) == 1:
            return list(self.catalog.values())[0]
        return {}
    
    def validate_field(self, index: str, field: str) -> bool:
        fields = self.get_index_fields(index)
        return field in fields

    def get_field_type(self, index: str, field: str) -> str:
        fields = self.get_index_fields(index)
        if field in fields:
            return fields[field]["type"]
        return None

field_catalog = FieldCatalog()
