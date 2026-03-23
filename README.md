# AGRODATA

A full-stack, data-driven platform designed to **ingest, standardize, query, and visualize heterogeneous environmental station data** through a unified, secure, and scalable architecture.

The project focuses on solving real-world challenges related to **data heterogeneity, performance, secure access, and reproducible deployment** in distributed environments.

---

## 🌐 Live Demo

👉 https://environmentalstationsdata.pages.dev/

> ⚠️ **Note:** The website may occasionally be unstable or partially broken as new features and updates are actively being deployed.

---

## Overview

Environmental monitoring stations often expose data through **heterogeneous schemas, vendor-specific APIs, and inconsistent naming conventions**, making cross-station analysis and querying difficult and error-prone.

This platform addresses those challenges by:
- Standardizing station data ingestion through a centralized domain model
- Enabling **semantic, vendor-agnostic querying** across stations
- Providing a **type-safe API layer** between backend and frontend
- Delivering high-performance geospatial visualization
- Ensuring secure access and automated, repeatable deployments

The system is designed to be **production-grade**, not a demo application.

---

## Key Features

- **Semantic RAG-based query resolution** to unify queries across heterogeneous station schemas  
- Centralized data model with automated ETL pipelines for continuous synchronization with vendor APIs  
- Type-safe FastAPI ↔ React communication with consistent domain object serialization  
- High-performance data access through caching, query optimization, and concurrency  
- Distributed worker architecture using **Redis-backed background workers**  
- OAuth-based authentication with role-aware authorization  
- Secure remote database access over encrypted VPN tunnels  
- Fully containerized architecture with automated CI/CD pipelines  
- Centralized logging and reproducible server deployments  

---

## System Architecture

### High-Level Flow

1. **Data ingestion**
   - Station data fetched from heterogeneous vendor APIs
   - ETL pipelines normalize and map data to a centralized schema

2. **Semantic query resolution**
   - User queries resolved via a semantic RAG-based layer
   - Environmental parameters mapped to station-specific sensor names and aggregation types

3. **Backend processing**
   - FastAPI serves structured, typed endpoints
   - Background workers handle heavy or concurrent workloads

4. **Frontend consumption**
   - React + TypeScript consumes strictly typed API responses
   - Optimized data feeds power high-performance map visualizations

5. **Secure access**
   - OAuth authentication and role-based authorization enforced at the API layer

---

## Tech Stack

### Frontend
- React
- TypeScript

### Backend
- Python
- FastAPI
- Pydantic

### Data & Caching
- PostgreSQL
- Redis

### Infrastructure & DevOps
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)
- SSH
- Tailscale VPN

### Authentication & Security
- Clerk (OAuth)
- Role-based authorization middleware

---

## Authentication & Authorization

Authentication is handled using **OAuth via Clerk**.

Authorization is enforced server-side using **role-based middleware**:
- Users authenticate via Clerk
- User roles are resolved and attached to requests
- API endpoints enforce access rules based on role (e.g. admin vs user)

This approach ensures secure access and strict privilege separation without relying on client-side enforcement.

---

## Data Model & Processing

- Centralized station data model abstracts vendor-specific schemas
- Automated ETL pipelines synchronize data from external services
- Semantic resolution maps logical parameters to:
  - Station-specific sensor names
  - Appropriate aggregation strategies
- Aggregated and derived data is cached to optimize read performance

---

## Worker Architecture

To reduce backend load and keep API responses fast, the platform uses a **Redis-backed worker setup**.

- **Redis** is used as a task broker (and can also be leveraged as shared caching when needed).
- **Background workers** currently focus on running the **semantic RAG query resolution** asynchronously.
- This keeps the FastAPI app responsive by offloading compute-heavy model execution away from the main API request path.
- The architecture is designed to scale later to additional workloads (e.g., ETL or cache warm-up) if needed.

---

## Performance Optimizations

The platform achieves a **~55% reduction in data fetching time** by combining:
- Intelligent caching strategies
- Optimized database queries
- Concurrent worker execution
- Reduced over-fetching in API responses

These optimizations directly enable smooth, high-performance map visualization.

---

## Deployment & Infrastructure

### Containerization
- Full-stack application containerized using **Docker Compose**
- Supports local development, testing, and production environments
- Dedicated dev/test environments for safe experimentation

### Secure Remote Database Access
- PostgreSQL hosted on a Windows Server
- Access secured via **encrypted Tailscale VPN tunnels**
- Controlled port-forwarding safely bypasses firewall limitations
- Ensures consistent database availability without exposing public ports

### CI/CD & Automation
- Docker images automatically built and pushed to **GHCR** via GitHub Actions
- Remote deployments orchestrated using:
  - SSH connections tunneled through Tailscale
  - Automated container startup and updates
- Centralized logging for observability and debugging

---

## Setup & Local Development

This project relies on **private infrastructure components** (VPN access, secrets, and third-party authentication) that are **not publicly exposed**.

To run the full stack locally, you must have:
- Access to the private **Tailscale VPN** used for secure server and database communication
- Required **secret files and environment variables** (e.g. database credentials, Clerk configuration)
- Docker and Docker Compose installed

### Local Setup

```bash
git clone https://github.com/YassineSahli04/EnvironmentalStationsData.git
cd EnvironmentalStationsData
docker compose -f docker-compose.override.yml up
