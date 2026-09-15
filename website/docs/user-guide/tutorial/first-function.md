# 1. Start a shaker

The first procedure has two steps: save a speed of 300 rpm, then start the
shaker. Inside the program they look like this:

```python
self.shaker.speed = 300 * rpm
self.shaker.start()
```

Saving a speed does not start the device. `start()` applies the saved setting
and enables agitation.

## Put the steps in a Function

A Python class groups a procedure's declarations and methods. Our class is
called `StirRack`; `(Function)` gives it SciLoom's compilation methods.
The field `shaker: Agitator` says the procedure needs a shaker.

`self` refers to the current procedure instance, so `self.shaker` means its
shaker. `@runtime` marks the method whose steps SciLoom will compile. The
method accepts only `self`; later lessons use fields for its inputs.

Here is the complete file:

```python
--8<-- "examples/tutorial/start_shaker.py"
```

`StirRack()` creates an instance of the class. Calling its `.compile()`
generates the AutoSuite function package. The `run` method is not executed
during this process; ordinary Python, such as the code below the class, is.
Keep the source in a normal `.py` file so SciLoom can read the method.

## Match the shaker to your configuration

The dictionary key `"shaker"` matches the declared field name. The values
`zone="Heater Shaker 23"` and `device_id="23"` identify equipment in an
example AutoSuite configuration. For your setup, use the zone name and
individual shaker ID in your own configuration. A shaker ID is not a vial number.

`300 * rpm` expresses a rotational speed. You can change the number here and
compile again. These settings are programming examples, not a recommendation
for your samples.

## Generate the package

From the repository root:

```bash
uv run python examples/tutorial/start_shaker.py
```

```text
start_shaker.asfp
```

The file is written beside the Python source. The `Path(__file__)` expression
selects that location, even when you run the command from another directory.

The package has no runtime inputs. When AutoSuite calls its function, it uses
the fixed speed in this source. Compilation does not connect to equipment;
validate the package with AutoSuite Executor on the deployment computer before
equipment use. See [validation limits](../../introduction/status.md#what-compilation-establishes).

[Python source](../../_generated/examples/tutorial/start_shaker.py) ·
[Generated package](../../_generated/examples/tutorial/start_shaker.asfp)

Next: [2. Supply a speed and switch](inputs-and-units.md).
