# ENTERPRISE OPERATING MANUAL & MIGRATION RUNBOOK
**Document ID:** EOP-AI-2026-v4.2  
**Target Scope:** Migration of 100+ Legacy ADK Agents across 10+ Workflow Applications to Modern Agent Frameworks & Integration into Gemini Enterprise  
**Target Environments:** Vertex AI Agent Engine, Google Cloud Run, Google Kubernetes Engine (GKE), Google App Engine (GAE)

---

## EXECUTIVE SUMMARY & ARCHITECTURE TRANSFORMATION

```mermaid
flowchart TD
    subgraph Legacy Fleet [Legacy Fleet: 100+ ADK Agents across 10+ Apps]
        L1[App Engine: Legacy Task Workers]
        L2[Cloud Run: Micro-Agents]
        L3[GKE: Distributed Long-Running Clusters]
        L4[Legacy Agent Engine: Early ADK Runtimes]
    end

    subgraph Modernization Layer [Phase 1-3: Code & Contract Modernization]
        T1[AST Codemod / Python Upgrade to 3.11+]
        T2[Modern Agent Core: Tools, Memory, State Schemas]
        T3[Standard Open Contract: OpenAPI 3.1 & MCP Servers]
    end

    subgraph Unified Runtime Infrastructure [Phase 4: Unified Runtime Hosting]
        R1[Cloud Run v2: Containerized Event-Driven Agents]
        R2[GKE Enterprise: High-Throughput Heavyweight Agents]
        R3[Vertex AI Agent Engine: Managed Playbooks]
        GW[Apigee / Cloud API Gateway with PSC & Cloud Armor]
    end

    subgraph Gemini Enterprise Surface [Phase 5: Gemini Enterprise Ingestion]
        G_APP[Gemini Enterprise Workspace / Web Assistant]
        V_EXT[Vertex AI Extensions & Tools Directory]
        V_ORCH[Root Supervisor / Dispatcher Agent Engine]
    end

    Legacy Fleet --> Modernization Layer
    Modernization Layer --> Unified Runtime Infrastructure
    Unified Runtime Infrastructure --> GW
    GW --> V_EXT
    V_EXT --> V_ORCH
    V_ORCH --> G_APP
```

---

# MODULE 1: INVENTORY, DISCOVERY & DEPENDENCY AUDIT

### 1.1 Discovery & Taxonomy Matrix
Before changing code, all 100+ agents across the 10+ workflow applications must be categorized into an automated audit registry.

Create an inventory catalog tracking the following schema:
- **Application ID / Name** (e.g., `APP-FIN-01`, `APP-OPS-04`)
- **Agent Name & Role** (e.g., `InvoiceValidatorAgent`, `CustomerOrderRouter`)
- **Source ADK Version** (e.g., `google-adk==0.1.x`, early preview SDKs)
- **Current Runtime** (`Cloud Run`, `GKE`, `Agent Engine`, `App Engine`)
- **State & Memory Store** (`In-Memory`, `Firestore`, `Cloud Memorystore Redis`, `Spanner`)
- **Egress / Integrations** (Third-party APIs, BigQuery, Internal ERP/CRM)
- **Exposure Type** (Tool/Sub-agent, Standalone Endpoint, Async Queue Subscriber)

### 1.2 Automated Discovery Script
Run the following Python script across agent repository roots to generate the audit report:

```python
import os
import re
import json

DEPENDENCY_PATTERNS = [
    r"google[-_]adk([<>=!~].*)?",
    r"google[-_]cloud[-_]aiplatform([<>=!~].*)?",
    r"langchain([<>=!~].*)?",
    r"pydantic([<>=!~].*)?",
]

def scan_repository(repo_path):
    findings = {"path": repo_path, "adk_imports": [], "dependencies": []}
    
    # 1. Scan requirements.txt / pyproject.toml
    for req_file in ["requirements.txt", "pyproject.toml", "Pipfile"]:
        target = os.path.join(repo_path, req_file)
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pat in DEPENDENCY_PATTERNS:
                    matches = re.findall(pat, content)
                    if matches:
                        findings["dependencies"].append((pat, matches))
                        
    # 2. Scan source code for ADK class usage
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as src:
                    for line_no, line in enumerate(src, 1):
                        if "from adk" in line or "import adk" in line or "Agent(" in line:
                            findings["adk_imports"].append({
                                "file": os.path.relpath(file_path, repo_path),
                                "line": line_no,
                                "snippet": line.strip()
                            })
    return findings

if __name__ == "__main__":
    import sys
    scan_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    report = scan_repository(scan_dir)
    print(json.dumps(report, indent=2))
```

---

# MODULE 2: CODEBASE & DEPENDENCY UPGRADE BLUEPRINT

### 2.1 Package & Python Runtime Upgrades
1. **Python Baseline**: Move all runtimes from Python 3.8/3.9 to **Python 3.11 or 3.12** for performance and memory improvements.
2. **Core Dependencies Replacement Matrix**:
   - `adk` (Deprecated early preview) $\rightarrow$ `google-cloud-aiplatform>=1.70.0` with `vertexai.preview.reasoning_engines` / modern Agent Engine SDK, or `pydantic-ai` / `langgraph`.
   - `pydantic 1.x` $\rightarrow$ `pydantic 2.x` (Crucial for serialization speed and strict JSON schema generation for OpenAPI 3.1).
   - `google-cloud-storage`, `google-cloud-bigquery` $\rightarrow$ Upgrade to latest stable client libraries to avoid gRPC compatibility conflicts with HTTP/2 proxies.

### 2.2 Refactoring Legacy ADK Patterns to Modern Agent Interfaces

#### Legacy Pattern (Old ADK Pseudocode):
```python
# OLD ADK PATTERN (Deprecated)
from adk import Agent, ToolRegistry

tools = ToolRegistry()

@tools.register
def query_db(account_id: str):
    return {"status": "ok", "balance": 500}

agent = Agent(
    model="gemini-pro-vision-preview",
    tools=tools,
    memory="ephemeral"
)
```

#### Modernized Standard Pattern (OpenAPI/FastAPI + Vertex AI Compatible):
```python
# MODERN STANDARDIZED AGENT (FastAPI + Pydantic v2 + Structured Output)
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field
import vertexai
from vertexai.generative_models import GenerativeModel, Tool

app = FastAPI(
    title="CustomerOperationsAgent",
    version="2.0.0",
    servers=[{"url": "https://agent-cust-ops-xyz.run.app"}]
)

class QueryCustomerRequest(BaseModel):
    customer_id: str = Field(description="Alpha-numeric enterprise customer identifier", pattern=r"^[A-Z0-9_-]{4,32}$")
    include_open_tickets: bool = Field(default=False, description="Whether to include pending support tickets")

class CustomerResponse(BaseModel):
    customer_id: str
    status: str
    risk_score: float
    summary: str

@app.post(
    "/execute", 
    response_model=CustomerResponse,
    operation_id="query_customer_profile",
    summary="Fetch validated customer risk profile and active tickets"
)
async def execute_agent(
    payload: QueryCustomerRequest,
    x_forwarded_authorization: str = Header(None, alias="Authorization")
):
    """
    Primary endpoint surfaced as an OpenAPI Tool in Gemini Enterprise.
    Enforces strict typing, telemetry, and distributed tracing.
    """
    # 1. Input Sanitization & Business Logic
    # 2. Agent Execution / Tool Logic
    return CustomerResponse(
        customer_id=payload.customer_id,
        status="ACTIVE",
        risk_score=0.12,
        summary="Tier-1 Enterprise customer in good standing."
    )
```

---

# MODULE 3: RUNTIME HOSTING CONVERGENCE & INFRASTRUCTURE MODERNIZATION

Legacy deployments across Cloud Run, GKE, Agent Engine, and App Engine must be consolidated and standardized:

### 3.1 App Engine Migration Plan (Retire App Engine)
> [!IMPORTANT]
> App Engine Standard/Flexible imposes restrictive networking for long-running streaming LLM interactions and lacks native gRPC / Cloud Run concurrency scaling controls.
- **Action**: Containerize all App Engine workloads using standard distroless Docker containers and migrate them to **Cloud Run v2**.

### 3.2 Cloud Run Deployment Standard (Lightweight & Event-Driven Agents)
Deploy agents to Cloud Run v2 with:
- **Concurrency**: Set between 8 and 40 (adjust based on CPU vs I/O profile).
- **Execution Environment**: Generation 2 (`--execution-environment=gen2`).
- **Timeout**: Set `--timeout=300s` to accommodate complex multi-step reasoning without connection dropping.
- **VPC Ingress**: Configure `--ingress=internal-and-cloud-load-balancing` to prevent public Internet access.

```bash
gcloud run deploy agent-cust-ops \
    --image=gcr.io/${PROJECT_ID}/agents/cust-ops:v2.0.0 \
    --region=us-central1 \
    --platform=managed \
    --no-allow-unauthenticated \
    --service-account=sa-agent-executor@${PROJECT_ID}.iam.gserviceaccount.com \
    --vpc-connector=agent-vpc-connector \
    --ingress=internal-and-cloud-load-balancing \
    --timeout=300s \
    --concurrency=20 \
    --min-instances=1 \
    --max-instances=50
```

### 3.3 GKE Enterprise Standard (Heavy / GPU / State-Clustered Agents)
For high-throughput workflow engines (e.g., LangGraph multi-node workers, long-running vector search):
1. **Workload Identity**: Bind Kubernetes Service Accounts (KSA) directly to Google Service Accounts (GSA).
2. **Ingress**: Expose via **GKE Gateway API** using Internal Application Load Balancers (ILB) with mutual TLS (mTLS) or OAuth proxy.
3. **Resource Requests/Limits**: Ensure strict memory bounds to prevent OOM kills during multi-turn LLM context buffer expansions.

---

# MODULE 4: INTEGRATION INTO GEMINI ENTERPRISE

Gemini Enterprise consumes external agents through **Vertex AI Extensions & Tools** orchestrated by a central **Supervisor / Dispatcher Agent**.

### 4.1 OpenAPI Schema Publication
Gemini Enterprise requires an OpenAPI 3.0/3.1 JSON or YAML specification that explicitly specifies:
1. `operationId`: Must be semantic and unique across all 100+ agents (e.g., `financial_audit_verify_gl_code`).
2. `description`: Clear semantic explanations for Gemini's prompt planner to decide **when** and **why** to invoke the agent.

Generate and host the OpenAPI manifest in a protected Cloud Storage bucket:
`gs://${PROJECT_ID}-agent-specs/specs/cust-ops-v2.json`

### 4.2 Automated Registration via Vertex AI Extensions API
Register each agent as a reusable Extension in Vertex AI:

```python
from google.cloud import aiplatform_v1beta1 as aiplatform

def register_agent_extension(
    project_id: str,
    location: str,
    extension_name: str,
    spec_gcs_uri: str,
    service_account_email: str
):
    client = aiplatform.ExtensionRegistryServiceClient(
        client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    )
    
    parent = f"projects/{project_id}/locations/{location}"
    
    extension = {
        "display_name": extension_name,
        "description": f"Enterprise extension routing requests to {extension_name} runtime.",
        "manifest": {
            "name": extension_name,
            "description": f"Autonomous tool interface for {extension_name}",
            "api_spec": {
                "open_api_gcs_uri": spec_gcs_uri
            },
            "auth_config": {
                "google_service_account_config": {
                    "service_account": service_account_email
                },
                "auth_type": "GOOGLE_SERVICE_ACCOUNT_AUTH"
            }
        }
    }
    
    response = client.create_extension(parent=parent, extension=extension)
    print(f"Extension registered successfully: {response.name}")
    return response.name
```

### 4.3 Supervisor Routing Architecture (Managing 100+ Agents)
> [!WARNING]
> Exposing 100+ raw tool definitions simultaneously into a single Gemini prompt context degrades tool selection accuracy, causes hallucination, and wastes context tokens.

**Enterprise Architecture Solution: Two-Tier Hierarchical Routing**
1. **Tier 1 (Domain Supervisors in Vertex AI Agent Builder)**:
   - Deploy **4 to 6 Domain Dispatcher Agents** (e.g., *Finance Domain Supervisor*, *Supply Chain Supervisor*, *HR & IT Operations Supervisor*).
2. **Tier 2 (Leaf Agents)**:
   - Each domain supervisor holds only the 10-20 specific agent tools belonging to its operational domain.
3. **Gemini Enterprise Entrypoint**:
   - Routes user queries first to the Domain Supervisor, which then delegates to the exact sub-agent.

---

# MODULE 5: SECURITY, IAM & ZERO TRUST NETWORK TOPOLOGY

### 5.1 Identity & Authentication Chain
- **User $\rightarrow$ Gemini Enterprise**: Handled via Google Workspace / Cloud Identity SSO (OAuth2 OIDC).
- **Gemini Enterprise $\rightarrow$ Vertex AI Extension**: Impersonates a central Dispatcher Service Account (`sa-gemini-orchestrator@...`).
- **Dispatcher $\rightarrow$ Backend Runtimes (Cloud Run / GKE / Agent Engine)**:
  - Carries an authenticated OpenID Connect (OIDC) identity token signed by Google IAM.
  - Target Cloud Run services enforce `roles/run.invoker` granted exclusively to the Dispatcher SA.
  - Target GKE Gateway validates JWT claims via Google Cloud Armor / Ingress Controller.

### 5.2 Network Isolation & Private Service Connect (PSC)
- Prevent public internet routing.
- Use **Serverless VPC Access connectors** for Cloud Run.
- Configure **Private Service Connect (PSC)** between Vertex AI and internal GKE Load Balancers.
- Apply **Cloud Armor WAF** rules to block malformed payloads and prompt injection patterns at the API perimeter.

---

# MODULE 6: COMPREHENSIVE CUTOVER RUNBOOK & SOP

### 6.1 Phase-by-Phase Execution Schedule

| Phase | Duration | Scope | Deliverables |
|---|---|---|---|
| **Phase 1: Pilot Modernization** | Weeks 1–2 | 1 Application (5–10 Agents) | Standard template, automated CI/CD pipeline, OpenAPI schema generator |
| **Phase 2: App Engine Deprecation** | Weeks 3–4 | App Engine services migrated to Cloud Run v2 | Container images, Terraform configs, VPC bindings |
| **Phase 3: Batch Migration** | Weeks 5–8 | Remaining 90+ agents across GKE & Cloud Run | Pydantic v2 code upgrade, testing suite validation, unit/e2e tests |
| **Phase 4: Vertex AI & Gemini Surfacing** | Weeks 9–10 | Extension registration & Hierarchical Supervisor setup | Manifests uploaded, Domain Supervisors tested in Gemini Studio |
| **Phase 5: Canary Cutover & Production** | Weeks 11–12 | Traffic shadowing (10% $\rightarrow$ 50% $\rightarrow$ 100%) | Full cutover, legacy shutdown, metric baseline sign-off |

### 6.2 Canary & Traffic Migration Procedure
For each application:
1. **Stage 1: Shadow Traffic (Read-Only)**
   - Replay 10% of historical production requests through the modernized endpoint using Cloud Tasks or Envoy mirroring.
   - Verify output parity, response times, and error rates.
2. **Stage 2: Pilot Canary in Gemini Enterprise (Internal Testers)**
   - Enable the new extension only for an internal testing security group in Gemini Enterprise.
   - Collect user interaction logs, trace tool-call fidelity, and check for schema hallucination.
3. **Stage 3: 100% General Availability Cutover**
   - Promote extension to organization-wide Gemini Enterprise availability.
   - Drain old ADK instances and decommission legacy infrastructure.

---

# MODULE 7: OBSERVABILITY, AUDITING & SRE RUNBOOKS

### 7.1 Unified Distributed Tracing
Ensure every agent propagates the W3C `traceparent` header.
- Gemini Enterprise passes `x-cloud-trace-context` or `traceparent`.
- Capture span IDs within Cloud Run, GKE, and Agent Engine.
- Correlate user prompts with downstream database queries in **Cloud Trace**.

### 7.2 Golden Signals Alerting Matrix

| Metric | Warning Threshold | Critical Threshold | Automated Action |
|---|---|---|---|
| **P95 Latency** | > 8.0s | > 15.0s | Cloud Run auto-scaling step-up / Alert SRE on call |
| **Tool Execution Error Rate (5xx)** | > 2% | > 5% | Vertex AI Circuit Breaker flags tool as degraded |
| **Schema Mismatch (422 Unprocessable)** | > 0.5% | > 2% | Auto-disable extension; fallback to deterministic fallback prompt |
| **Token Budget Consumption** | > 80% monthly quota | > 95% quota | Rate-limit high-frequency agents; notify billing owner |

### 7.3 SRE Incident Runbook: Degraded Agent Diagnostic Tree
If Gemini Enterprise reports failure to trigger or execute an agent:

1. **Verify IAM Token Exchange**:
   ```bash
   gcloud auth print-identity-token --audiences="https://agent-cust-ops-xyz.run.app"
   curl -H "Authorization: Bearer $(gcloud auth print-identity-token --audiences=...)" https://agent-cust-ops-xyz.run.app/docs
   ```
2. **Inspect Cloud Run / GKE Application Logs**:
   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" AND severity>=ERROR' --limit 20 --format json
   ```
3. **Inspect Vertex AI Extension Execution Logs**:
   - Query log name: `projects/{PROJECT_ID}/logs/aiplatform.googleapis.com%2Fextension_execution`
   - Filter by `jsonPayload.status != "OK"` to view rejected schema validations.
4. **Emergency Rollback**:
   - Revert Gemini Extension manifest back to the previous stable OpenAPI revision via the Vertex AI Extension Registry API or Terraform.
