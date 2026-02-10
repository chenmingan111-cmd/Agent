# ES Query Copilot

Natural Language to Elasticsearch DSL converter with validation, auto-fix, and risk assessment.

## Features
- **Draft**: NL -> DSL generation
- **Validate**: Syntax and field validation with auto-repair
- **Run**: Safe execution with risk scoring and deep paging support
- **Explain**: Readable explanation of queries and results

## Quick Start

1. **Install Dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and set your ES_URL, ES_PASSWORD, and LLM_API_KEY
   ```

3. **Build Field Catalog**
   ```bash
   python scripts/build_field_catalog.py --index "orders-*"
   ```

4. **Run Server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

5. **Run Tests**
   ```bash
   pytest
   ```
