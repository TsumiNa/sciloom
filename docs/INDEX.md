# Documentation index

The [public handbook](../website/docs/index.md) and its
[local build instructions](../website/docs/developer/documentation.md) describe the current
implementation. The records below retain design history and
implementation context; they are not automatically published with the website.

## Architecture and implementation direction

Use the handbook for implemented behavior. Numbered current-guide files below
are indexes; design proposals and validation records retain their historical context.

- [Project state](00_PROJECT_STATE.md)
- [Target architecture](01_TARGET_ARCHITECTURE.md)
- [Compiler pipeline](02_COMPILER_ARCHITECTURE.md)
- [Representation boundaries](03_REPRESENTATION_LAYER_REDESIGN.md)
- [Restricted Python frontend and staging](04_PYTHON_FRONTEND_AND_STAGING.md)
- [Instance specialization and compile API](05_INSTANCE_SPECIALIZATION_AND_COMPILE_API.md)
- [Error handling](06_ERROR_HANDLING_MODEL.md)
- [xyflow and AI on the shared IR](07_XYFLOW_AI_SHARED_IR.md)
- [Example guide](08_EXAMPLE_CODE_GUIDE.md)
- [Decisions and open questions](09_DESIGN_DECISIONS_AND_OPEN_QUESTIONS.md)
- [Validation status](10_TEST_RESULTS.md)
- [Semantic IR and JSON API](11_SEMANTIC_IR.md)
- [Python Function frontend](12_PYTHON_FRONTEND.md)
- [ASFP compilation](13_ASFP_COMPILER.md)
- [Reference execution contract](14_REFERENCE_EXECUTION.md)
- [Agitation domain semantics](15_AGITATION_SEMANTICS.md)
- [Static typing and contributor contracts](16_TYPING.md)
- [Initial Function implementation sequence](refactor/semantic-ir/00-overview.md)
- [Compiler foundation refactor sequence](refactor/compiler-foundation/00-overview.md)
- [Accepted package layout, native types and list implementation sequence](refactor/package-layout/00-overview.md)
- [Accepted device configuration and lifecycle sequence](refactor/device-abstraction/00-overview.md)
- [Collected device questions for later confirmation](refactor/device-abstraction/qa.md)
- [English documentation and versioned publication plan](refactor/documentation-site/00-overview.md)
- [Standalone website directory contract](refactor/standalone-website/00-overview.md)
- [uv workspace and lockstep versioning](refactor/uv-workspace/00-overview.md)
- [Keeping the AutoSuite corpus out of git](refactor/corpus-privacy/00-overview.md)
- [Renaming the core binding records module](refactor/core-bindings/00-overview.md)
- [Example-led handbooks](refactor/handbook-restructure/00-overview.md)
- [User Guide readability and experimental learning path](refactor/user-guide-readability/00-overview.md)
- [Durable IR and twelve runtime capabilities](refactor/runtime-capabilities/00-overview.md)

## AutoSuite reference

Workflow notes, distilled schema conclusions and reference tools are under
`autosuite/`. The original files and the manual are shared inside the team and
are not in this repository; see [the directory guide](../autosuite/README.md).
Start with the [AutoSuite reference guide](../autosuite/docs/00_REFERENCE_GUIDE.md).
The [capability audit](../autosuite/docs/18_CAPABILITY_GAPS_AND_ZONE_PARAMETERS.md)
compares the current compiler with the received corpus and manual, including
runtime Zone parameters, CSV support and the evidence needed for further work.
