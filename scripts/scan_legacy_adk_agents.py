#!/usr/bin/env python3
"""
Enterprise Legacy ADK Discovery Scanner
Scans codebase repositories to discover legacy ADK dependencies, outdated models,
and usage patterns across distributed microservices.
"""

import os
import re
import json
import sys

DEPENDENCY_PATTERNS = [
    r"google[-_]adk([<>=!~].*)?",
    r"google[-_]cloud[-_]aiplatform([<>=!~].*)?",
    r"langchain([<>=!~].*)?",
    r"pydantic([<>=!~].*)?",
]

def scan_repository(repo_path):
    findings = {
        "repository_path": os.path.abspath(repo_path),
        "manifest_dependencies": [],
        "adk_import_occurrences": []
    }
    
    # 1. Scan requirement manifests
    for req_file in ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]:
        target = os.path.join(repo_path, req_file)
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pat in DEPENDENCY_PATTERNS:
                    matches = re.findall(pat, content)
                    if matches:
                        findings["manifest_dependencies"].append({
                            "file": req_file,
                            "pattern": pat,
                            "matches": matches
                        })
                        
    # 2. Scan source code files for legacy ADK classes
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as src:
                    for line_no, line in enumerate(src, 1):
                        if any(term in line for term in ["from adk", "import adk", "ToolRegistry(", "Agent("]):
                            findings["adk_import_occurrences"].append({
                                "file": os.path.relpath(file_path, repo_path),
                                "line": line_no,
                                "snippet": line.strip()
                            })
    return findings

if __name__ == "__main__":
    scan_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    report = scan_repository(scan_dir)
    print(json.dumps(report, indent=2))
