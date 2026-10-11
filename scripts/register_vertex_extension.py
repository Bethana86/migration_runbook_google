#!/usr/bin/env python3
"""
Automated Vertex AI Extension Registrar
Registers an OpenAPI-compliant agent backend into the Vertex AI Extensions Registry
with Google Service Account authentication.
"""

import sys
import argparse
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
    
    print(f"Registering extension '{extension_name}' under {parent}...")
    operation = client.create_extension(parent=parent, extension=extension)
    response = operation.result()
    print(f"Extension successfully registered: {response.name}")
    return response.name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register agent extension in Vertex AI")
    parser.add_argument("--project-id", required=True, help="GCP Project ID")
    parser.add_argument("--location", default="us-central1", help="GCP Region")
    parser.add_argument("--name", required=True, help="Extension Display Name")
    parser.add_argument("--spec-uri", required=True, help="GCS URI to OpenAPI JSON (e.g. gs://bucket/spec.json)")
    parser.add_argument("--service-account", required=True, help="Service Account Email for OIDC Auth")
    
    args = parser.parse_args()
    register_agent_extension(
        project_id=args.project_id,
        location=args.location,
        extension_name=args.name,
        spec_gcs_uri=args.spec_uri,
        service_account_email=args.service_account
    )
