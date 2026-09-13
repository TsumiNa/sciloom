# DSL layering: authoring vocabulary, devices and source analysis

## Authority and status

This is the accepted interface contract for a nine-stage layering refactor of the
Python frontend. It extends the package-layout contract, which records its
own stage status. Every constraint that plan states remains in force, including explicit
context objects, direct functions and the absence of a pass registry, mixin
hierarchy, compatibility facade or generic pass framework. Its stage 4 acceptance
required no *new* import cycles, which this plan does not dispute: the cycles
recorded here predate that stage and were never covered by an executable check.
Stage 2 adds that check, and stages 3 to 5 remove the cycles within the
constraints the earlier plan set.

This plan supersedes one row of the package-layout ownership table when stage 6
lands: `sciloom.dsl` stops owning field declarations and model instances, which
move to `sciloom.flow`, and owns source analysis alone. Nothing else in that
contract changes.

All nine stages are merged: #41 and #42 (4bf4f68, 02cae6e), #43 (d4d13f9), #44
(5363abe), #45 (2db4f3e), #46 (2d90e51), #47 (440aff5), #48 (9ea3a62), #49
(b0f471c) and #50 (083405f). The frontend is acyclic apart from the recorded
facade seam, the package tree matches the architecture diagram, and the layering
test is the executable form of this contract.

One item is deliberately undone, recorded in [stage 9](09-context-scopes.md): the
lowering context is still handed its source record after construction, because
discovering source earlier would reverse which diagnostic an author sees first.

| Stage | Plan | Available after merge |
| --- | --- | --- |
| 1 | [Contract](01-contract.md) | This contract and the organisation rule |
| 2 | [Layering test](02-layering-test.md) | Executable layering ratchet over the frontend |
| 3 | [Device member recognition](03-device-member.md) | `self.<slot>.<member>` recognised by the lowering context |
| 4 | [Branch recursion](04-branch-recursion.md) | All statement recursion in one module |
| 5 | [Composition paths](05-composition-paths.md) | Frontend analysis acyclic except the documented seam |
| 6 | [Flow package](06-flow-package.md) | `flow` / `devices` / `dsl` layout and the written rule |
| 7 | [Declaration diagnostics](07-declaration-diagnostics.md) | One declaration-time error model |
| 8 | [Conventions](08-conventions.md) | Named conventions for adding an analysis module |
| 9 | [Context scopes](09-context-scopes.md) | Program-scoped and function-scoped lowering state |

## Decision and alternatives

A reader of `src/sciloom/dsl/` today cannot tell which module an author writes
against, which one runs at class-definition time and which one runs only inside
`Function.to_ir()`. Eleven modules sit in one flat directory; nine of them form a
single strongly connected component whose only break points are four
function-local imports. `sciloom/devices/` sits beside `core` and `dsl` as though
it were an independent subsystem, when it holds the device half of the same
authoring vocabulary.

The accepted model separates three things that the code already does but never
names:

- **Flow** is the expression container for experiment procedure and control
  conditions. Today that is `Function` and its field declarations. It is the
  place where composing several Functions, adding globals and packaging an
  Application will land; the AutoSuite `.app` file is exactly such a package.
- **Devices** are the things under control, generic or bound to one concrete
  instrument.
- **Source analysis** turns a Python `Function` instance written in those two
  vocabularies into semantic IR, and hands it on.

The target structure is not new. The published architecture page already draws
`Python Function instance` flowing into `DSL source analysis` and on into
`Semantic IR`, and the package ownership table beside it already separates the
authoring vocabulary from the analysis. The diagram has been the intended
structure since the documentation site landed; the code simply never matched it.
This refactor makes the package tree the diagram, and stage 6 labels the first
node with the two vocabularies it has always implied.

Alternatives considered and rejected. Moving `sciloom/devices/` under the DSL
expresses "a device declaration is also DSL" but breaks four published API paths
and makes equipment targets import the authoring frontend, which contradicts the
boundary those targets exist to keep. Keeping one flat `dsl` package and fixing
only the cycles leaves the reading problem unsolved. Introducing a visitor or
pass framework to remove the mutual recursion is forbidden by the package-layout
contract and unjustified with one frontend implementation.

## Organisation rule

> `flow` and `devices` are the two vocabularies an author writes; `dsl` is the
> only layer that reads Python source; `core` imports neither.

Dependencies run `dsl` to `flow` to `devices` to `core`. The single edge in the
other direction is the facade seam recorded below. An equipment target declares
and binds devices, so it may import `sciloom.devices`, as the AutoSuite target
already does; no target imports the flow vocabulary or the source analysis.

| Location | Responsibility |
| --- | --- |
| `sciloom` | Lazy author API |
| `sciloom.units` | Independent physical quantities |
| `sciloom.flow` | Procedure and control vocabulary: Function, runtime fields, device slots, compile-time queries |
| `sciloom.devices` | Controlled things: device families, member declarations, contracts and bindings |
| `sciloom.dsl` | DSL source analysis: one Python Function instance to validated IR |
| `sciloom.core` | IR, validation, compiler pipeline, reference interpreter, diagnostics |
| `sciloom.contrib` | Equipment targets (superseded by the [uv workspace plan](../uv-workspace/00-overview.md): the maintained target is the workspace member `sciloom_autosuite`) |

`sciloom.devices` keeps its current import path. Its published paths
(`BaseDevice`, `operation`, `declarations.device_contract`,
`declarations.bind_device`) do not move, and equipment targets continue to reach
device declarations without importing the authoring frontend.

`sciloom.dsl` keeps its name and gains its exact meaning: the source analysis
already drawn as `DSL source analysis` in the architecture diagram. Its
`__init__.py` stays a docstring with no re-exports, so an author import never
loads the analysis modules.

### Final module layout

```text
src/sciloom/
    __init__.py             lazy author API
    units.py
    flow/
        function.py         Function, runtime
        fields.py           Input, Output, Var, RuntimeField, build_schema
        device_slots.py     DeviceReference, DeviceSlot, build_device_schema
        comptime.py         can_write, supports, is_device
    devices/                unchanged
    dsl/
        __init__.py         docstring only
        context.py          LoweringContext
        source.py           locate and parse the single runtime method
        expressions.py      Python expression to IR expression
        statements.py       Python statement to IR statement; all statement recursion
        device_conditions.py  recognise one compile-time device query
        device_operations.py  property writes and declared commands
        driver.py           component paths, lower, function assembly
    core/
    contrib/
```

## Mechanism rule

The package already uses four mechanisms consistently. This contract records the
rule so a newcomer can tell which one a new concern needs.

| Concern | Mechanism | Reason |
| --- | --- | --- |
| Data that survives a JSON round trip | Frozen dataclass in a closed union | Exhaustive, comparable, serializable, no behavior |
| Behavior supplied by a third party that core must not import | Structural `Protocol` | `Target` is the only cross-package extension point; contributors are told not to import it |
| Vocabulary a user extends by subclassing, where ancestry is itself data | Nominal inheritance | `device_contract` derives `base_type_ids` from the MRO; `issubclass(x, BaseDevice)` discriminates a device slot from a host field |
| One transformation over the closed IR with one implementation | Free functions and an explicit context | No second implementation exists; a generic pass framework is a stated non-goal |

Consequences. `Target` stays a `Protocol`: its runtime `isinstance` check
verifies member presence only, and the signature contract is enforced by the
subprocess mypy fixtures. An abstract base class would impose an import and an
inheritance edge, would not check signatures either, and would reject neither of
the two accepted spellings of `target_id`. Device profiles stay nominal because a
Protocol has no MRO to serialize. Lowering passes stay free functions because the
recognisers are ordered: a device assignment must be tried before a general
assignment, a device query before a general `if`, a device command before a
general call, and type-keyed dispatch cannot express that without the registry
this repository excludes.

No new `Protocol`, no abstract base class and no metaclass is introduced by this
refactor.

## Authoritative interface contract

Every stage plan links here rather than restating names. Examples labelled
*target* become runnable after the stage that implements them.

### Device member recognition (target, stage 3)

Recognising `self.<device slot>.<member>` moves onto the lowering context, beside
the existing `host_attribute`, `device_type` and `target` resolvers.

```python
class LoweringContext:
    def device_member(self, node: ast.AST) -> tuple[DeviceReference, str] | None:
        """Recognize `self.<device slot>.<member>`; any other shape returns None."""
```

Callers in `expressions.py`, `statements.py` and `device_operations.py` use
`context.device_member(node)`. The free function of the same name is removed.

### Device queries and branch recursion (target, stage 4)

`device_conditions` recognises a query and reports what the then-branch may
assume. It no longer lowers statements.

```python
@dataclass(frozen=True, kw_only=True)
class DeviceCondition:
    """One recognized compile-time query and the narrowing its then-branch gets."""

    predicate: CanWrite | SupportsOperation | IsDevice
    resource_id: str
    narrowed_type: type[BaseDevice] | None


def device_condition(context: LoweringContext, node: ast.If) -> DeviceCondition | None:
    """Return the device query in `node.test`, or None for an ordinary condition."""
```

Branch narrowing becomes a scope owned by the context, so `narrowed_devices` is
touched only by the context itself.

```python
class LoweringContext:
    @contextmanager
    def narrowing(self, resource_id: str, device_type: type[BaseDevice] | None) -> Iterator[None]:
        """Apply one branch-local device narrowing and restore the enclosing scope."""
```

`statements.py` builds the node, and the order of allocation is part of the
contract: the predicate keeps a lower sequence number than its `DeviceIf`.

```python
elif isinstance(node, ast.If):
    query = device_condition(context, node)
    if query is not None:
        metadata = context.metadata(node)
        with context.narrowing(query.resource_id, query.narrowed_type):
            then_body = statements(context, node.body)
        result.append(
            DeviceIf(
                **metadata,
                condition=query.predicate,
                then_body=then_body,
                else_body=statements(context, node.orelse),
            )
        )
        continue
```

### Composition paths (target, stage 5)

Walking host composition is analysis, not declaration. `component_paths` moves to
the analysis driver and narrows its parameter.

```python
def component_paths(root: Function) -> dict[int, str]:
    """Find stable host composition paths without invoking user descriptors."""
```

It keeps reading `vars(...)` rather than `getattr`, so declared slots never
materialise a reference on a user instance.

### The facade seam (current and target)

One deferred import remains, and only one. `Function.to_ir()` is the author-facing
entry and must reach the analysis layer, while the analysis layer needs the real
`Function` class at runtime for `isinstance` checks.

```python
def to_ir(self) -> Program:
    # Deferred: dsl.driver imports flow.function for composition discovery.
    from sciloom.dsl.driver import lower

    return lower(self)
```

Rejected alternatives: a marker base class carrying `model_fields` and
`device_fields` is a mixin hierarchy and changes MRO traversal and `issubclass`
results for every author class; assigning the method from the analysis layer is a
registry; moving `Function` into the analysis layer breaks the lazy author API.

### Import paths after the move (target, stage 6)

| Before | After |
| --- | --- |
| `sciloom.dsl.model` | `sciloom.flow.function` |
| `sciloom.dsl.schema` | `sciloom.flow.fields` |
| `sciloom.dsl.device_schema` | `sciloom.flow.device_slots` |
| `sciloom.dsl.comptime` | `sciloom.flow.comptime` |
| `sciloom.dsl.lowering` | `sciloom.dsl.driver` |

No published API path changes. `sciloom.Function`, `sciloom.Input`,
`sciloom.Output`, `sciloom.Var`, `sciloom.runtime`, `sciloom.Agitator` and
`sciloom.comptime` keep their spelling and stay lazy.

### Declaration-time diagnostics (target, stage 7)

Declaring a class produces structured diagnostics, never a bare exception. A
Function declaring device slots reuses the runtime field code and path, beside the
existing schema errors:

```python
raise IRValidationError((Diagnostic(code="class_schema", message=..., path=f"$.schema.{name}"),))
```

A device class declaring its own identity, properties or commands reports under
its own code:

```python
raise IRValidationError((Diagnostic(code="device_contract", message=..., path=f"$.device.{subject}"),))
```

This covers `build_device_schema` and `device_contract`, which read a class body,
wherever they are called from. `bind_device` builds a profile's contract and its
ancestors', so a malformed declaration surfaces there as a diagnostic too: it is
a declaration error whoever discovers it. Two boundaries stay `TypeError`, because
neither reports a declaration: host-access guards that reject reading a device
property or calling a runtime method, and `bind_device`'s own checks, which reject
a profile that omits a capability list or names a member it never declared.

### Analysis conventions (target, stage 8)

1. `context` is the first parameter of every analysis function and is always
   named `context`.
2. A recogniser returns `None` for a shape it does not own. Once it has matched,
   it must report through `context.fail`, never return `None`.
3. Names used only inside their own module carry a leading underscore.
4. A function-local import carries a comment naming the cycle it breaks.
5. Adding an analysis module means: recogniser and lowerer, wiring into the
   statement chain at the right position, a colocated `<module>_test.py`, and the
   matching entry in the mypy override list in `pyproject.toml`.

The lowering function named `operation` becomes `device_command`, so `operation`
means only the device declaration decorator.

## Evidence and limits

The cycle inventory, the published-path inventory and the layering claims here
were derived from the tree at `6798354`. The layering test delivered by stage 2
is the executable form of those claims; prose in this file is not the check.

Node identifiers are positional. Any change to the order in which
`context.metadata` is called renumbers a function's nodes and rewrites committed
example artifacts, so every stage compares generated examples against the parent
commit.

## Acceptance and non-goals

Shared acceptance for every stage:

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest src/sciloom examples
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python -m compileall -q examples/proposed_frontend
uv run python examples/function_call.py
uv run python examples/agitation.py
uv run python examples/scale_values.py
uv run python examples/non_zero_array_min.py
uv run python -m examples.developer.agitation_ir
uv run python -m examples.developer.list_ir
uv run python -m examples.developer.demo_device
uv run python -m examples.developer.portable_agitation
git status --porcelain
uv run --group docs python website/tools/site.py build --strict
uv run --group docs pytest website/tools
```

An empty `git status --porcelain` after the example runs is part of acceptance:
the generated companion files are the regression test for node identifiers.

Non-goals. No semantic change, no IR or JSON v4 change, no diagnostic code text
change, no generated artifact change, no pass registry, visitor framework,
plugin discovery, abstract base class or mixin hierarchy, no new `Protocol`, no
move of `sciloom.devices`, no `contrib` dependency on the authoring frontend, and
no change to the agitation lifecycle nodes. Generalising `StartAgitation` and
`StopAgitation` into a contract-driven lifecycle is deferred until a second
device family needs a configure-then-apply sequence; it would require a JSON
version bump and a major release.
