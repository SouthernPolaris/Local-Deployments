# Local Deployments Orchestrator

This repository contains a set of scripts and configurations to orchestrate local deployments of various services and applications. The goal is to simplify the process of setting up and managing local environments for development and testing purposes.

## Features 
* Graph Engine (L2 Orchestrator)
    - Uses NetworkX to validate that a user-submitted network topology is a valid undirected tree (preventing network loops)
    - Algorithmically maps every "edge" in the tree to a unique isolated Linux Bridge (`vmbrX`) on the hypervisor
    - Automatically identifie the main jumpbox and plugs it into the external network bridge (`vmbr0`)

* FastAPI backend
    - Strict Type Safety: All API requests are validated using Pydantic schemas to ensure zero ambiguity reaches the infrastructure layer
    - Async Operations: Implemented `BackgroundTasks` to handle long-running operations without blocking the main event loop

* Persistent Storage
    - Implemented a State Manager that persists range data to `active_ranges.json` to ensure data durability across service restarts
    - Enabled Full Lifecycle Management: Support for `POST`, `GET`, and `DELETE` operations on network ranges, allowing users to create, retrieve, and delete ranges as needed
    - Uses a flat file JSON storage for simplicity, with easy extensibility to more complex databases in the future

* Design Principles
    - Modular Architecture: Separated concerns into distinct modules for better maintainability and scalability
    - Adapter Pattern: Created an abstract interface `ICloudAdapter` to allow easy integration with different cloud providers or hypervisors in the future
    - Linting and Formatting: Project uses `ruff` and `mypy` for linting and type checking

* Mock Adapter
    - System supports a headless dry-run mode using the `MockAdapter`, which simulates an E2E deployment without physical infrastructure
    - Useful for testing

## Current System Architecture
The workflow follows the below pipeline:
1. JSON Request: User submits a graph (Nodes/Links)
2. Validation: The Graph Engine validates the graph structure
3. Planning: Engine assigns Bridge IDs and identifies role-based requirements (e.g., jumpbox external connectivity)
4. Persistence: The cyber range is saved to disk
5. Execution: The `MockAdapter` simulates the process of VM cloning and network attachments

## Next Steps
### Layer 3 & Routing
While the bridges are mapped out, the VMs are currently not communicating as they lack proper IP addressing and routing configurations.

- IP Address Management: Assign subnets to each bridge segment
- Edge Router Config: Automate NAT/Routing configuration on local jumpbox nodes
- Real Proxmox Integration: Replace `MockAdapter` with a actual `proxmoxer` API calls and task polling.

## How to Run Locally
1. Clone the repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2. Install dependencies with uv and pyproject.toml:
    ```bash
    uv -r .
    ```
3. Start the FastAPI server:
    ```bash
    uv run uvicorn app.main:app --reload
    ```
4. Access the API documentation at `http://127.0.0.1:8000/docs`.
5. Execute E2E Test: Use the `POST /range` endpoint with a sample JSON tree.
6. Verify: Check terminal logs for mock cloning and verify `active_ranges.json` for persistence.