---
layout: default
title: Components
---

# Voyage Framework Components

Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

This page separates the canonical v4.1/v4.2 architecture from historical v4.0 compatibility surfaces that remain in the repository. A legacy export is not a current core capability. This classification also guides v4.3 documentation planning; it does not claim that a v4.3 release exists.

## Canonical v4.1/v4.2 core

| Component | Current responsibility |
|---|---|
| `TaskYamlSpec` / `TaskParser` | Immutable canonical `task.yaml` specification and deterministic validation. |
| `TaskRecord` / `TaskEngine` | Canonical local task state and its only standard lifecycle mutator. |
| `Event` / `EventEngine` | Audit record and append-only audit log; neither independently controls task state. |
| `ContextBuilder` | Context Builder Lite aggregation and comparison for `voyage sync`; generated context is not canonical state. |
| `AgentRegistry` | Static, read-only role registry; it does not start or execute agents. |
| `ModeRegistry` | Static, read-only mode profiles; it does not activate runtime modes. |
| `PromptGenerator` / `PromptPackage` | Deterministic prompt packaging for manual transfer to external AI tools; no model or provider is called. |
| `AdapterContract` / `AdapterProtocol` | Interface and documentation boundary for future external-tool adapters; no adapter runtime or provider integration is implemented. |
| `AgentRequest`, `AgentResponse`, `ValidationResult`, `ApprovalFlow` | Static adapter payload models; `ApprovalFlow` describes approval data and does not execute an approval workflow. |
| Documentation and process artifacts | Guides, static examples, workflow policy, audits, and cleanup plans document safe human-controlled development workflows. |

`TASK.md` and `CONTEXT.json` are generated artifacts, not canonical truth. External AI tools are manual handoff targets and are not Voyage runtime dependencies.

## Legacy and historical v4.0 surfaces

The following names may remain importable or visible for compatibility. They belong to previous architecture and are **not canonical v4.1/v4.2 core**. Their retention here does not promise autonomous agent execution, runtime orchestration, automatic graph execution, or a model/provider execution layer. Voyage is not a LangGraph, CrewAI, or AutoGen replacement.

| Historical surface | Qualification |
|---|---|
| `AgentRuntime` | Legacy v4.0 agent runtime; historical and non-canonical. |
| `LangGraphRuntime` | Legacy v4.0 graph runtime; historical and non-canonical. |
| `VoyageGraphBuilder` | Legacy graph-construction helper; not part of the current core. |
| `MermaidExporter` | Legacy graph-visualization helper; not a current orchestration capability. |
| `AgentState` | Legacy runtime state model retained for compatibility; not canonical task state. |
| `ToolResult` | Legacy tool-execution result model; not evidence of current automatic tool execution. |
| `SecureExecutor` | Legacy command-execution compatibility surface; not a canonical agent runtime. |
| `SecurityPolicy` | Legacy security/runtime support model; not part of the canonical task workflow. |
| `SemanticStore` | Historical semantic-memory surface; not canonical project memory. |
| `CodeSearch` | Historical semantic code-search surface; non-canonical. |
| `ASTParser` | Historical AST tooling surface; non-canonical. |
| `CodeIndexer` | Historical AST/indexing surface; non-canonical. |
| `GoldenDataset` | Historical self-improvement data model; non-canonical. |
| `GoldenSolution` | Historical self-improvement data model; non-canonical. |
| `RuleEngine` | Historical self-improvement rule surface; non-canonical. |
| `Evaluator` | Historical evaluation surface; non-canonical. |
| `FeedbackLoop` | Historical self-improvement surface; non-canonical. |
| `TaskGenerator` | Legacy `TASK.md`/`CONTEXT.json` generator; it does not replace `TaskParser` or create canonical `TaskRecord` state. |
| `ProcessJournal` | Historical Chronicler/process-documentation helper; non-canonical. |
| `ReplayGenerator` | Historical Chronicler replay helper; non-canonical. |
| `DecisionLog` | Historical Chronicler decision helper; non-canonical. |
| `TutorialDraft` | Historical documentation-generation model; non-canonical. |
| `TutorialGenerator` | Historical documentation-generation helper; non-canonical. |
| `DocsBuilder` | Historical documentation-generation helper; non-canonical. |
| `ProjectContext` | Legacy context model; it is not canonical task or runtime state. |

These surfaces are preserved as historical and compatibility evidence only. Their future disposition requires a separately approved cleanup or compatibility phase; this page does not deprecate, remove, execute, or otherwise change them.
