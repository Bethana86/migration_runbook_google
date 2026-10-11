"""
Standard Modern Agent Service Template
Compatible with Cloud Run v2, GKE, Vertex AI Reasoning Engines, and OpenAPI 3.1.
"""

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-service")

app = FastAPI(
    title="EnterpriseDomainAgent",
    description="Standardized OpenAPI 3.1 agent backend for Gemini Enterprise consumption",
    version="2.0.0"
)

class AgentInvocationRequest(BaseModel):
    query: str = Field(..., description="Natural language query or instruction for the agent")
    entity_id: Optional[str] = Field(None, description="Optional entity or customer identifier")
    strict_mode: bool = Field(default=True, description="Enforce strict validation and deterministic output")

class AgentStepDetail(BaseModel):
    tool: str
    output: str

class AgentInvocationResponse(BaseModel):
    execution_id: str
    status: str
    result: str
    steps: List[AgentStepDetail] = []

@app.get("/healthz", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "HEALTHY"}

@app.post(
    "/execute",
    response_model=AgentInvocationResponse,
    operation_id="execute_domain_agent",
    summary="Execute specific enterprise domain agent logic"
)
async def execute_agent(
    payload: AgentInvocationRequest,
    authorization: Optional[str] = Header(None, description="OIDC bearer token passed by Vertex AI Extension")
):
    """
    Standard agent execution endpoint.
    Validates payload against Pydantic schema and returns structured response.
    """
    logger.info(f"Received agent invocation request for query: {payload.query[:50]}...")
    
    # Business logic execution
    return AgentInvocationResponse(
        execution_id="exec-" + os.urandom(4).hex(),
        status="SUCCESS",
        result=f"Processed query for entity '{payload.entity_id or 'N/A'}' successfully.",
        steps=[
            AgentStepDetail(tool="knowledge_retrieval", output="Found 1 relevant document"),
            AgentStepDetail(tool="policy_validation", output="Complies with enterprise standards")
        ]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
