# Known AutoSuite semantic traps relevant to a compiler

1. **Macro variables are stateful unless reset behavior is enabled.** Re-entering a Macro Task does not necessarily reinitialize locals. This must be represented explicitly rather than assuming Python local-variable semantics.
2. **Sequential fragment variable is not the ordinary `loop` variable.** Project debugging found that code using `loop` to recover a well index failed; the active fragment counter must be used.
3. **IF/ELSE serialization is structural.** Branch bodies belong under `SATaskCondition/components`; a visually similar flat sibling sequence is not the same schema.
4. **Function-call argument IDs matter.** Binding nodes reuse parameter IDs from the callee definition.
5. **Arrays are zero-based.** AutoSuite Manual and project code both rely on this.
6. **Array autofill has expression limitations.** Do not assume an arbitrary expression involving an indexed array will be expanded per table row.
7. **Units are dangerous.** AutoSuite expressions are evaluated in SI context; unit literals or typed variables should be used instead of naked constants where physical types are intended.
8. **Writable zone variables can begin empty.** Using them before assignment can fail at runtime.
9. **Do not conflate current error-latch code with the target language error model.** The production program uses `g_error_latched`, `Throw Error`, and repeated guards, while AutoSuite separately has an application-level OnError event. The new frontend may provide structured `try/except ... raise` syntax that lowers to target fault semantics, but fatal faults must not silently continue.
10. **`.app` is compressed.** Treat it as gzip XML; comparing raw bytes is meaningless.
