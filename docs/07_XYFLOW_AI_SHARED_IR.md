# xyflow, Python and AI on one semantic model

## One model, multiple representations

The agreed design is that all authoring paths converge on the same Typed AutoSuite Semantic IR.

```mermaid
flowchart TB
    Python["Python source / compiler"] --> IR["Typed AutoSuite Semantic IR"]
    GUI["xyflow editor"] <--> IR
    AI["AI Skill / MCP / node-graph tools"] <--> IR
    classDef core fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e;
    class IR core;
```

There is no separate “GUI AST” or “AI pseudo-language”.

## xyflow responsibilities

The GUI should project Semantic IR nodes into a flow representation suitable for visual programming and preview. It may expose:

- control-flow edges;
- data/binding edges;
- task/function nodes;
- variable/state nodes;
- typed ports;
- zone/device references;
- nested scopes/containers;
- validation diagnostics.

GUI-specific state is separate:

```mermaid
classDiagram
    direction LR
    class SemanticNode {
        node_id
        semantic_type
        symbols_and_references
        expressions
        control_and_data_relations
    }
    class ViewNode {
        node_id
        x
        y
        size
        collapsed
        viewport
        group
        annotation
    }
    SemanticNode --> ViewNode : keyed by node_id
```

Moving a box must not create a semantic program change.

## AI responsibilities

AI can interact through either of two equivalent paths:

1. edit/query Semantic IR or its graph projection through Skill/MCP tooling;
2. generate the restricted Python DSL and invoke the same compiler.

The validator is authoritative regardless of how the program was created.

## Python regeneration

A deterministic IR → canonical-Python renderer is useful for:

- code review;
- diffs;
- handoff from GUI user to programmer;
- AI context;
- exporting a visual workflow as maintainable code.

Exact preservation of arbitrary original Python formatting is not required for the initial architecture.

## Why this matters

A scientist can construct the same program visually that an engineer writes in Python and that an AI edits through a graph interface. All three paths receive the same type checking, target validation and XML backend behavior.
