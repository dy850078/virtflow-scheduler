import uuid
from app.models.schemas import SchedulingRequest, BareMetalNode
from typing import List, Optional
from app.services.algorithm import select_best_node


def run_scheduler(nodes: List[BareMetalNode], request: SchedulingRequest) -> Optional[str]:
    selected = select_best_node(request, nodes)
    return selected.name if selected else None