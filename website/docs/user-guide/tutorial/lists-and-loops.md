# 3. Lists and loops

A rack holds many vials. To choose one speed for the whole rack, the program
needs the largest volume in a list.

<!-- tutorial: step -->
```python
class LargestVolume(Function):
    """Find the largest volume in a rack.

    Attributes:
        volumes: Volume of every vial in the rack.
        largest: The largest volume, or 0.0 for an empty rack.
        index: Loop position, reset on every call.
    """

    volumes: Input[list[float]]
    largest: Output[float]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.largest = 0.0
        self.index = 0
        while self.index < len(self.volumes):
            if self.volumes[self.index] > self.largest:
                self.largest = self.volumes[self.index]
            self.index += 1
```

A list field is `list[T]` of one scalar type: `float` here, or `int`, `bool` or
`RotationalSpeed`. Lists are one-dimensional and homogeneous. `len` and indexing
work as in Python; indices are non-negative integers, and a write never extends
a list.

The loop is a `while` with an explicit index, because the runtime language has
no `for`. The index is a `Var`, so it is declared on the class, and it is reset
to zero at the top of the method: without that line the second call would start
where the first one stopped. Every name the method assigns is a declared field;
there are no local variables.

Lists are values. Assigning one list field to another copies it, and a call
passes a copy in and copies results back, so no two fields ever share elements.

<!-- tutorial: checkpoint -->
```python
print(LargestVolume().compile(target=AutoSuiteTarget()).write("largest_volume.asfp").name)
```
```text
largest_volume.asfp
```

Writing the loop the Python way shows how the subset is enforced: the source is
read, and the first statement outside the subset is named.

<!-- tutorial: checkpoint -->
```python
class Iterate(Function):
    volumes: Input[list[float]]
    total: Output[float]

    @runtime
    def run(self) -> None:
        self.total = 0.0
        for volume in self.volumes:
            self.total += volume


try:
    Iterate().compile(target=AutoSuiteTarget())
except Exception as error:
    print(error)
```
```text
$.python.fn:0: Unsupported runtime statement: For. [python_subset]
```

Next: [4. Stirring with an Agitator](agitator.md).
