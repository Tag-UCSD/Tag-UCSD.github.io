
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict


app = FastAPI(title="Graph Explorer Demo API", version="0.2.0")

# Allow everything for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParamSummary(BaseModel):
    mean: float
    sd: float
    ci_lower: float
    ci_upper: float


class EvidenceItem(BaseModel):
    id: str
    title: str
    summary: str
    effect_direction: str  # "beneficial", "harmful", "null", "mixed"
    population: str
    design: str
    outcome_measures: List[str]
    doi: Optional[str] = None
    quality: Optional[str] = None  # e.g. "high", "moderate"
    notes: Optional[str] = None


class EdgeDetail(BaseModel):
    id: str
    from_node: str
    to_node: str
    status: str  # "hypothesized" | "supported" | "experimentally_validated"
    param: ParamSummary
    evidence: List[EvidenceItem]


class GraphNode(BaseModel):
    id: str
    label: str
    level: str  # "attribute" | "mediator" | "outcome"
    group: Optional[str] = None
    description: Optional[str] = None


class GraphEdge(BaseModel):
    id: str
    from_node: str
    to_node: str
    status: str
    param: ParamSummary


class GraphPayload(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class PredictRequest(BaseModel):
    # Architectural attributes (scaled 0–1 or approximately so)
    wood_coverage: float
    plant_density: float
    spatial_clutter: float
    glare_index: float


class NodePrediction(BaseModel):
    node_id: str
    label: str
    mean: float
    ci_lower: float
    ci_upper: float


class PredictResponse(BaseModel):
    model_a: List[NodePrediction]
    model_b: List[NodePrediction]


# ---------------------------------------------------------------------
# Demo graph definition
# ---------------------------------------------------------------------

NODES: List[GraphNode] = [
    # Architectural attributes (top band)
    GraphNode(
        id="wood_coverage",
        label="Wood Coverage",
        level="attribute",
        group="materials",
        description="Proportion of visible wall/ceiling area finished in wood (0–1).",
    ),
    GraphNode(
        id="plant_density",
        label="Plant Density",
        level="attribute",
        group="biophilia",
        description="Visible density of indoor plants or green features (0–1).",
    ),
    GraphNode(
        id="spatial_clutter",
        label="Spatial Clutter",
        level="attribute",
        group="layout",
        description="Visual and physical clutter / obstruction in the space.",
    ),
    GraphNode(
        id="glare_index",
        label="Glare Index",
        level="attribute",
        group="lighting",
        description="Subjective glare / harshness of lighting.",
    ),

    # Mediators (middle band)
    GraphNode(
        id="perceived_warmth",
        label="Perceived Warmth",
        level="mediator",
        group="perceptual",
        description="Subjective thermal / visual warmth of the space.",
    ),
    GraphNode(
        id="perceived_naturalness",
        label="Perceived Naturalness",
        level="mediator",
        group="perceptual",
        description="Degree to which the space feels natural / biophilic.",
    ),
    GraphNode(
        id="cognitive_load",
        label="Cognitive Load",
        level="mediator",
        group="cognitive",
        description="Momentary mental effort required to function in the space.",
    ),
    GraphNode(
        id="positive_affect",
        label="Positive Affect",
        level="mediator",
        group="affective",
        description="Momentary positive mood / calmness / pleasure.",
    ),

    # Outcomes (bottom band)
    GraphNode(
        id="state_anxiety",
        label="State Anxiety",
        level="outcome",
        group="affective",
        description="Short-term, situational anxiety level (e.g. STAI-S).",
    ),
    GraphNode(
        id="perceived_stress",
        label="Perceived Stress",
        level="outcome",
        group="affective",
        description="Self-reported stress / tension.",
    ),
    GraphNode(
        id="task_performance",
        label="Task Performance",
        level="outcome",
        group="cognitive",
        description="Performance on a sustained attention / working-memory task.",
    ),
]


# Param helper
def p(mean: float, sd: float, ci_width: float = 1.96) -> ParamSummary:
    return ParamSummary(mean=mean, sd=sd, ci_lower=mean - ci_width * sd, ci_upper=mean + ci_width * sd)


EDGES: Dict[str, EdgeDetail] = {}


def register_edge(
    edge_id: str,
    from_node: str,
    to_node: str,
    mean: float,
    sd: float,
    status: str,
    evidence: Optional[List[EvidenceItem]] = None,
):
    EDGES[edge_id] = EdgeDetail(
        id=edge_id,
        from_node=from_node,
        to_node=to_node,
        status=status,
        param=p(mean, sd),
        evidence=evidence or [],
    )


# Populate demo edges with a few real studies as provenance
register_edge(
    edge_id="wood_coverage->perceived_warmth",
    from_node="wood_coverage",
    to_node="perceived_warmth",
    mean=0.45,
    sd=0.10,
    status="supported",
    evidence=[
        EvidenceItem(
            id="li2021_wood_use",
            title="Effect of the degree of wood use on the visual psychological response of wooden indoor spaces",
            summary=(
                "Medium wood coverage (≈35–65%) in interiors was associated with higher ratings of naturalness, "
                "warmth, relaxation, and desire to use the space compared to low coverage."
            ),
            effect_direction="beneficial",
            population="Adults in controlled visual simulation",
            design="Within-subjects lab experiment",
            outcome_measures=["Perceived warmth", "Perceived relaxation"],
            doi="10.1007/s00226-021-01320-7",
            quality="moderate",
            notes="Inverse V-shaped relationship with very high wood coverage reducing comfort."
        ),
    ],
)

register_edge(
    edge_id="wood_coverage->perceived_naturalness",
    from_node="wood_coverage",
    to_node="perceived_naturalness",
    mean=0.40,
    sd=0.12,
    status="supported",
    evidence=[
        EvidenceItem(
            id="jalilzadehazhari2019_wood_surfaces",
            title="Material properties of wooden surfaces used in interiors and their influence on physiological responses",
            summary=(
                "Visual exposure to indoor wooden surfaces generally increased feelings of comfort and naturalness, "
                "with some evidence of reduced sympathetic activation."
            ),
            effect_direction="beneficial",
            population="University students in interior mock-ups",
            design="Lab-based exposure study",
            outcome_measures=["Perceived naturalness", "Comfort", "Physiological arousal"],
            doi="10.1080/17480272.2019.1575901",
            quality="moderate",
        ),
    ],
)

register_edge(
    edge_id="plant_density->perceived_naturalness",
    from_node="plant_density",
    to_node="perceived_naturalness",
    mean=0.50,
    sd=0.12,
    status="experimentally_validated",
    evidence=[
        EvidenceItem(
            id="yin2020_biophilic_vr",
            title="Effects of biophilic indoor environment on stress and anxiety recovery: A VR experiment",
            summary=(
                "VR offices with biophilic elements (plants, natural materials) produced greater reductions in stress "
                "and anxiety compared to a non-biophilic office."
            ),
            effect_direction="beneficial",
            population="100 adults in virtual office environments",
            design="Between-subjects VR experiment",
            outcome_measures=["State anxiety", "Heart rate variability", "Skin conductance"],
            doi="10.1016/j.envint.2019.105427",
            quality="high",
        ),
        EvidenceItem(
            id="lee2015_indoor_plants",
            title="Interaction with indoor plants may reduce psychological and physiological stress",
            summary=(
                "Active interaction with indoor plants lowered diastolic blood pressure and sympathetic activity "
                "relative to a computer task, and increased feelings of comfort and naturalness."
            ),
            effect_direction="beneficial",
            population="Young adults (mean age ~25 years)",
            design="Randomized crossover experiment",
            outcome_measures=["Heart rate variability", "Blood pressure", "Subjective comfort"],
            doi="10.1186/s40101-015-0060-8",
            quality="high",
        ),
    ],
)

register_edge(
    edge_id="plant_density->positive_affect",
    from_node="plant_density",
    to_node="positive_affect",
    mean=0.35,
    sd=0.10,
    status="supported",
    evidence=[
        EvidenceItem(
            id="yin2020_biophilic_vr_positive",
            title="Effects of biophilic indoor environment on stress and anxiety recovery: A VR experiment",
            summary="Participants in biophilic conditions reported more positive mood after stress induction than those in control offices.",
            effect_direction="beneficial",
            population="Adults in virtual offices",
            design="Between-subjects VR experiment",
            outcome_measures=["State anxiety", "Mood ratings"],
            doi="10.1016/j.envint.2019.105427",
            quality="high",
        ),
    ],
)

register_edge(
    edge_id="spatial_clutter->cognitive_load",
    from_node="spatial_clutter",
    to_node="cognitive_load",
    mean=0.30,
    sd=0.10,
    status="hypothesized",
    evidence=[],
)

register_edge(
    edge_id="glare_index->cognitive_load",
    from_node="glare_index",
    to_node="cognitive_load",
    mean=0.35,
    sd=0.10,
    status="hypothesized",
    evidence=[],
)

register_edge(
    edge_id="perceived_warmth->positive_affect",
    from_node="perceived_warmth",
    to_node="positive_affect",
    mean=0.25,
    sd=0.08,
    status="hypothesized",
    evidence=[],
)

register_edge(
    edge_id="perceived_naturalness->positive_affect",
    from_node="perceived_naturalness",
    to_node="positive_affect",
    mean=0.40,
    sd=0.09,
    status="supported",
    evidence=[
        EvidenceItem(
            id="yin2020_biophilic_vr_mood",
            title="Effects of biophilic indoor environment on stress and anxiety recovery: A VR experiment",
            summary="Biophilic interiors improved stress recovery and reduced anxiety, consistent with higher perceived naturalness and restorative quality.",
            effect_direction="beneficial",
            population="Adults in virtual offices",
            design="Between-subjects VR experiment",
            outcome_measures=["Perceived restorativeness", "State anxiety"],
            doi="10.1016/j.envint.2019.105427",
            quality="high",
        ),
    ],
)

register_edge(
    edge_id="positive_affect->state_anxiety",
    from_node="positive_affect",
    to_node="state_anxiety",
    mean=-0.50,
    sd=0.12,
    status="supported",
    evidence=[],
)

register_edge(
    edge_id="cognitive_load->state_anxiety",
    from_node="cognitive_load",
    to_node="state_anxiety",
    mean=0.30,
    sd=0.11,
    status="hypothesized",
    evidence=[],
)

register_edge(
    edge_id="cognitive_load->task_performance",
    from_node="cognitive_load",
    to_node="task_performance",
    mean=-0.35,
    sd=0.10,
    status="supported",
    evidence=[],
)

register_edge(
    edge_id="state_anxiety->task_performance",
    from_node="state_anxiety",
    to_node="task_performance",
    mean=-0.30,
    sd=0.10,
    status="supported",
    evidence=[],
)

register_edge(
    edge_id="perceived_naturalness->perceived_stress",
    from_node="perceived_naturalness",
    to_node="perceived_stress",
    mean=-0.40,
    sd=0.10,
    status="supported",
    evidence=[],
)

register_edge(
    edge_id="positive_affect->perceived_stress",
    from_node="positive_affect",
    to_node="perceived_stress",
    mean=-0.35,
    sd=0.10,
    status="supported",
    evidence=[],
)


@app.get("/api/v1/graph/v1_demo", response_model=GraphPayload)
def get_demo_graph():
    """
    Return a demo graph. This is intentionally small and static,
    but the shape mirrors what a real evidence graph would return.
    """
    edges_brief: List[GraphEdge] = []
    for ed in EDGES.values():
        edges_brief.append(
            GraphEdge(
                id=ed.id,
                from_node=ed.from_node,
                to_node=ed.to_node,
                status=ed.status,
                param=ed.param,
            )
        )
    return GraphPayload(nodes=NODES, edges=edges_brief)


@app.get("/api/v1/edges/{edge_id}", response_model=EdgeDetail)
def get_edge_detail(edge_id: str):
    """
    Return full statistical and provenance detail for a single edge.
    """
    ed = EDGES.get(edge_id)
    if not ed:
        raise HTTPException(status_code=404, detail="Edge not found")
    return ed


@app.post("/api/v1/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Demo prediction for Model A and Model B.

    Model A: simple linear index of attributes projected onto outcomes.
    Model B: same but includes an interaction between wood_coverage and plant_density.
    """
    w = request.wood_coverage
    plants = request.plant_density
    clutter = request.spatial_clutter
    glare = request.glare_index

    # Simple feature transforms
    # These are NOT fit from data, just reasonable demo numbers.
    perceived_warmth = 0.3 + 0.8 * w - 0.2 * glare
    perceived_naturalness = 0.2 + 0.9 * w + 0.9 * plants - 0.1 * clutter
    cognitive_load = 0.5 + 0.4 * clutter + 0.4 * glare - 0.2 * plants
    positive_affect = 0.3 + 0.6 * perceived_warmth + 0.5 * perceived_naturalness - 0.3 * cognitive_load

    state_anxiety = 0.7 - 0.7 * positive_affect + 0.4 * cognitive_load
    perceived_stress = 0.6 - 0.6 * perceived_naturalness - 0.5 * positive_affect + 0.3 * cognitive_load
    task_performance = 0.5 + 0.6 * positive_affect - 0.5 * cognitive_load - 0.4 * state_anxiety

    def clip01(x: float) -> float:
        return max(0.0, min(1.0, x))

    # Model A: treat these as normalized scores with a fixed ±0.15 CI for demo
    model_a_nodes = [
        ("perceived_warmth", "Perceived Warmth", clip01(perceived_warmth)),
        ("perceived_naturalness", "Perceived Naturalness", clip01(perceived_naturalness)),
        ("cognitive_load", "Cognitive Load", clip01(cognitive_load)),
        ("positive_affect", "Positive Affect", clip01(positive_affect)),
        ("state_anxiety", "State Anxiety", clip01(state_anxiety)),
        ("perceived_stress", "Perceived Stress", clip01(perceived_stress)),
        ("task_performance", "Task Performance", clip01(task_performance)),
    ]

    model_a_preds: List[NodePrediction] = []
    for nid, label, val in model_a_nodes:
        width = 0.15
        model_a_preds.append(
            NodePrediction(
                node_id=nid,
                label=label,
                mean=val,
                ci_lower=max(0.0, val - width),
                ci_upper=min(1.0, val + width),
            )
        )

    # Model B: add interaction term for wood*plants as a simple "biophilia synergy"
    synergy = 0.3 * w * plants
    positive_affect_b = clip01(positive_affect + synergy)
    state_anxiety_b = clip01(0.7 - 0.7 * positive_affect_b + 0.4 * cognitive_load)
    task_performance_b = clip01(0.5 + 0.6 * positive_affect_b - 0.5 * cognitive_load - 0.4 * state_anxiety_b)
    perceived_stress_b = clip01(0.6 - 0.6 * perceived_naturalness - 0.5 * positive_affect_b + 0.3 * cognitive_load)

    model_b_nodes = [
        ("perceived_warmth", "Perceived Warmth", clip01(perceived_warmth)),
        ("perceived_naturalness", "Perceived Naturalness", clip01(perceived_naturalness)),
        ("cognitive_load", "Cognitive Load", clip01(cognitive_load)),
        ("positive_affect", "Positive Affect", positive_affect_b),
        ("state_anxiety", "State Anxiety", state_anxiety_b),
        ("perceived_stress", "Perceived Stress", perceived_stress_b),
        ("task_performance", "Task Performance", task_performance_b),
    ]

    model_b_preds: List[NodePrediction] = []
    for nid, label, val in model_b_nodes:
        width = 0.12
        model_b_preds.append(
            NodePrediction(
                node_id=nid,
                label=label,
                mean=val,
                ci_lower=max(0.0, val - width),
                ci_upper=min(1.0, val + width),
            )
        )

    return PredictResponse(model_a=model_a_preds, model_b=model_b_preds)
