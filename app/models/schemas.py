from pydantic import BaseModel
from typing import List

class BareMetalNode(BaseModel):
    name: str
    cpu: int = 0
    memory: int = 0
    storage: int = 0
    usage_cpu: float = 0.0
    usage_mem: float = 0.0
    pool: str
    dedicated: bool
    model: str
    max_vms: int = 1
    current_vms: int = 0

class SchedulingRequest(BaseModel):
    requested_cpu: int
    requested_memory: int
    requested_pool: str
    dedicated: bool