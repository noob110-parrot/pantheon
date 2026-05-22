# Pantheon Architecture v3

## Core Principles

- Local first
- AppleScript first execution
- Single active model
- Load models on demand
- Dragon themed Textual UI
- Memory capsules
- Knowledge graph retrieval
- Importance → LFU → LRU cache
- Confidence gated execution
- Structured logging
- Memory provenance

## Execution Pipeline

Input
→ Fast Path Detector
→ Parser
→ Router

Router Order:
1. AppleScript
2. Shell
3. OpenClaw
4. LLM

Complex Tasks:
Planner
→ DAG
→ Scheduler
→ Executor

## Memory

Metadata
→ Knowledge Graph
→ Meta Capsules
→ Capsules
→ Vector Search
→ Raw Data

## Cache

L1: 64MB
L2: 256MB
L3: 2GB

Eviction:
Importance
→ LFU
→ LRU

## Model Policy

single_active_model=true
resident_small_model=false
idle_unload_minutes=10

## Safety

Structured logging
Confidence thresholds
Permission system
Memory provenance
