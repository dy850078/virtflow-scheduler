# Mock data for BareMetalNode
from typing import List

from fastapi import FastAPI
from app.models.schemas import BareMetalNode

app = FastAPI()

mock_nodes = [
    BareMetalNode(
        name="bm01",
        cpu=16,
        memory=32768,
        storage=1000,
        usage_cpu=0.3,
        usage_mem=0.4,
        pool="default",
        dedicated=False,
        model="HPE ProLiant DL360 Gen10",
        max_vms=20,
        current_vms=5
    ),
    BareMetalNode(
        name="bm02",
        cpu=32,
        memory=65536,
        storage=2000,
        usage_cpu=0.7,
        usage_mem=0.6,
        pool="high-performance",
        dedicated=True,
        model="Dell PowerEdge R740",
        max_vms=15,
        current_vms=10
    )
]


# Mock API endpoint to get BareMetalNode
@app.get("/nodes", response_model=List[BareMetalNode])
async def get_nodes():
    return mock_nodes