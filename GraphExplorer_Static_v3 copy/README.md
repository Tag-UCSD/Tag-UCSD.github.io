
# GraphExplorer Static v3

This is a self-contained demo of the Evidence Graph Explorer with:

- A FastAPI backend exposing a small static causal graph (attributes → mediators → outcomes).
- A static HTML/JS frontend (no React/Vite) using Cytoscape.js to render the graph.
- Edge detail view with real literature examples (DOIs open in a new tab).
- Attribute node view listing incoming/outgoing edges ordered by effect size.
- A demo Model A / Model B prediction endpoint (`/api/v1/predict`).

## 1. Backend

### Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API root will be at: http://127.0.0.1:8000  
Swagger UI: http://127.0.0.1:8000/docs

### Key endpoints

- `GET /api/v1/graph/v1_demo`  
  Returns the static demo graph:

  ```jsonc
  {
    "nodes": [
      { "id": "wood_coverage", "label": "Wood Coverage", "level": "attribute", ... },
      { "id": "perceived_warmth", "label": "Perceived Warmth", "level": "mediator", ... },
      { "id": "state_anxiety", "label": "State Anxiety", "level": "outcome", ... }
    ],
    "edges": [
      {
        "id": "wood_coverage->perceived_warmth",
        "from_node": "wood_coverage",
        "to_node": "perceived_warmth",
        "status": "supported",
        "param": { "mean": 0.45, "sd": 0.10, "ci_lower": 0.25, "ci_upper": 0.65 }
      },
      ...
    ]
  }
  ```

- `GET /api/v1/edges/{edge_id}`  
  Returns full detail for a single edge, including literature evidence and DOIs.  
  The frontend calls this when you click an edge.

- `POST /api/v1/predict`  
  Demo Model A / B predictions based on architectural attributes:

  ```jsonc
  {
    "wood_coverage": 0.5,
    "plant_density": 0.3,
    "spatial_clutter": 0.4,
    "glare_index": 0.2
  }
  ```

  Response:

  ```jsonc
  {
    "model_a": [
      { "node_id": "perceived_warmth", "mean": 0.6, "ci_lower": 0.45, "ci_upper": 0.75 },
      ...
    ],
    "model_b": [
      { "node_id": "perceived_warmth", "mean": 0.62, "ci_lower": 0.5, "ci_upper": 0.74 },
      ...
    ]
  }
  ```

This endpoint is intentionally lightweight (simple deterministic mapping) so you can later replace it with a full Bayesian engine without changing the frontend.

## 2. Static Frontend

The static frontend lives in `static-frontend/index.html` and talks directly to the backend at `http://127.0.0.1:8000/api/v1`.

### Run

With the backend running:

- On macOS:

  ```bash
  cd static-frontend
  open index.html
  ```

- On Windows:

  ```bash
  cd static-frontend
  start index.html
  ```

If your browser blocks CORS, ensure the backend is running on `127.0.0.1:8000` (CORS is fully open in `main.py`).

### Interactions

- **Pan / zoom** the graph with mouse drag / wheel.
- **Click a node**:
  - Attribute nodes (`level="attribute"`) show incoming/outgoing edges in the side panel,
    sorted by absolute effect size (|β|).
  - Mediators and outcomes show a simple description and hint to click edges.
- **Click an edge**:
  - Side panel shows:
    - Status badge (hypothesized / supported / experimentally validated).
    - Posterior demo statistics (mean, sd, 95% CI).
    - Evidence cards:
      - Title, short summary, direction of effect, population, design, outcomes, and quality.
      - If a DOI is present, the entire card is clickable and opens the DOI in a new tab.
- **Click the background**:
  - Clears selection, removes fading, and resets the side panel instructions.

### Visual semantics

- **Vertical bands**:
  - Top: architectural attributes (wood coverage, plant density, clutter, glare).
  - Middle: perceptual/cognitive mediators (perceived warmth, naturalness, cognitive load, positive affect).
  - Bottom: outcomes (state anxiety, perceived stress, task performance).

- **Arrows**:
  - All edges have small arrowheads indicating causal direction (`from_node → to_node`).

- **Selection / focus**:
  - The clicked node or edge (and its immediate neighbors) get a purple highlight.
  - All other nodes and edges are partially faded to de-emphasize them.

## 3. Next steps

This demo is intentionally minimal and deterministic. To move to a full production system, you would:

1. Replace the in-memory `NODES` / `EDGES` definitions with a database-backed evidence graph.
2. Extend `EvidenceItem` to link into your main literature database / knowledge graph.
3. Swap the simple `/predict` logic with a proper Bayesian engine that:
   - learns posterior edge weights from meta-analytic data,
   - propagates uncertainty through the mediator structure,
   - returns model diagnostics alongside predictions.
4. Add authentication and project-specific graph filtering in the API.
5. Integrate this frontend into your broader experimenter dashboard.

But you can already use this bundle as a working UI prototype for:
- graph navigation,
- evidence inspection with DOIs,
- and basic Model A / B comparison.
