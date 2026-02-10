import asyncio
import argparse
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.es_client import ESClient
from app.core.config import settings

async def build_catalog(index_pattern: str, output_path: str):
    print(f"Connecting to ES at {settings.ES_URL}...")
    es = ESClient()
    
    try:
        # 1. Get Mapping
        print(f"Fetching mapping for {index_pattern}...")
        mapping = await es.get_mapping(index=index_pattern)
        if not mapping:
            print("No index found matching pattern.")
            return

        # Flatten mapping to get field types
        # This is a simplified flattening; production might need full recursion
        # Here we rely on field_caps which is more accurate for "searchable/aggregatable"
        
        # 2. Get Field Capabilities
        print(f"Fetching field capabilities...")
        caps = await es.get_field_caps(index=index_pattern, fields="*")
        
        catalog = {}
        for field, info in caps.get("fields", {}).items():
            # Skip metadata fields
            if field.startswith("_"):
                continue
                
            # info is like: {"keyword": {"type": "keyword", "searchable": true, ...}}
            # We explicitly look for the type valid in this index
            
            # Simple heuristic: pick the first type (usually unique in one index)
            field_type_key = list(info.keys())[0]
            details = info[field_type_key]
            
            catalog[field] = {
                "type": details.get("type", "unknown"),
                "searchable": details.get("searchable", False),
                "aggregatable": details.get("aggregatable", False)
            }
            
        final_data = {index_pattern: catalog}
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2)
            
        print(f"Success! Catalog saved to {output_path} with {len(catalog)} fields.")
        
    finally:
        await es.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="orders-*", help="Index pattern to scan")
    parser.add_argument("--out", default="data/field_catalog.json", help="Output path")
    args = parser.parse_args()
    
    asyncio.run(build_catalog(args.index, args.out))
