from app.core.config import logger 
from app.models.schemas import BareMetalNode, SchedulingRequest


def pre_filter(request: SchedulingRequest, nodes: list[BareMetalNode]):
    return [
        node for node in nodes
        if node.pool == request.requested_pool
        and (not request.dedicated or node.dedicated)
        and node.current_vms < node.max_vms
    ]

# Filter nodes based on resource requirements 
def filter_nodes(request: SchedulingRequest, nodes: list[BareMetalNode]):
    return [
        node for node in nodes
        if node.cpu >= request.requested_cpu
        and node.memory >= request.requested_memory
    ]

# Score nodes based on CPU, memory, and VM usage
def score_nodes(nodes: list[BareMetalNode], cpu_weight=1.0, mem_weight=1.0, vm_weight=1.0):
    nodes.sort(key=lambda node: (1 - node.usage_cpu) * cpu_weight +
                                (1 - node.usage_mem) * mem_weight -
                                (node.current_vms / node.max_vms) * vm_weight)
    return nodes

# Select the best node based on pre-filtering, filtering, and scoring
def select_best_node(request: SchedulingRequest, nodes: list[BareMetalNode]):
    nodes = pre_filter(request, nodes)
    logger.info(f"[Pre-filtered] {[node.name for node in nodes]}")

    nodes = filter_nodes(request, nodes)
    logger.info(f"[Filtered] {[node.name for node in nodes]}")

    candidates = score_nodes(nodes)
    logger.info(f"[Scored] {[node.name for node in candidates]}")
    if candidates:
        logger.info(f"[Selected] {candidates[0].name}")
        return candidates[0]
    return None