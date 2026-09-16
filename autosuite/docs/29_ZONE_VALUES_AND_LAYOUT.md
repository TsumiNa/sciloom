# Zone values and read-only layout evidence

Stage 13 implements location data independently of device selection. The public
Zone value is an ordered set of opaque well references; no AutoSuite type ID,
well index or device object enters that value. Dynamic at/candidate compilation
remains stage 16.

## Evidence and mappings

| SciLoom construct | XML/manual evidence | Current implementation | Executor status |
| --- | --- | --- | --- |
| Empty Zone variable | F43/F46: storage type 8, empty value, siunit/unit zone, array 0; manual 3.8.5 p. 113 | Same declaration; no guessed expression literal | Pending |
| Zone parameter | F24 Zone variabletype and non-array input expression binding | Zone inputs/outputs and calls | Pending copy behavior on native calls |
| Named lookup | F48 uses FindZone(TrimText(zone_name_txt)), then ZoneSize(...)=0; manual 3.11.5 | ZoneFind → FindZone | Pending exact name and missing-name behavior |
| Length | F48 and manual 3.11.5 | ZoneLength → ZoneSize | Pending native execution |
| Combine | Manual 3.11.5 defines zone addition with duplicate wells added once | ZoneCombine → parenthesized addition | First-occurrence order/overlaps need Executor |
| Single-well label | F46 WellFullName; manual label example “Rack: Well #6” shape | Reference execution only; target rejects unproven cardinality | Failure propagation and cardinality checks pending |

`Zone.empty()` in an expression allocates private, never-written target storage
with the observed empty initialization. It does not depend on an undocumented
empty Zone expression. Nonempty opaque ZoneLiteral values cannot be emitted;
the target reports unsupported_zone_literal. Static comparisons confirm the
XML shape, not execution or physical behavior.

## Primary APP extraction

`AutoSuiteLayout.from_app(path)` reads gzip XML and extracts only config elements,
their parent relationships, wells and named Zones. It neither writes the APP nor
imports its tasks. The parser currently accepts ordinary SAZone.1 entries with
virtualVial=0, enumerationType=0 and observed enumeration schemes 0/1. External
base applications, virtual Zones and unobserved profiles fail explicitly.

Elements use their normalized UUIDs. A well identity is
`autosuite:well:<element-uuid>:<local-well-id>`; the local ID is not a Zone position.
Zone well references resolve through the tuple (progID, deviceID, local well ID)
to the owning element. Ambiguous tuples are errors. Serialized index values must
be consecutive and match XML order. Duplicate identities/names, missing parents,
cycles, unresolved wells and noncanonical direct layout records are rejected.

In the primary APP, Heater Shaker 23 selects local well 27 of ISynth-2, with
deviceID 1.1 and type Chemspeed.SADeviceISynthBlock2.1. Its actual parent is the
IndividualShaker controller with device ID 23. These are different identifiers;
comparing the Zone name or its enumeration position would not establish hardware
ownership. The parser retains that ancestry for later binding checks.

Display labels follow the manual's `<element name>: Well #<local ID>` shape.
They are for people, not lookup keys. Reference queries use a fixed immutable
LocationDirectory; host files and hardware are not accessed by those queries.

## Verification boundary

Synthetic gzip fixtures always exercise layout validation. The primary-APP test
skips when the team corpus is absent and verifies input bytes are unchanged when
present. The local extraction found 106 elements, 848 wells and 75 Zones; these
counts describe this supplied APP and are not a pinned corpus requirement.

Python, direct IR and JSON tests cover empty values, first-occurrence ordering,
length, unique identities, persistent state, calls, immutable snapshots and
missing-directory/cardinality failures. Existing v4 byte baselines remain fixed.
No Executor or hardware test has run. Runtime-guard-dependent programs stay gated
by [the failure prerequisite](24_RUNTIME_FAILURE_GATE.md).

## Version

Version: none for this evidence note; implementation belongs to stage 13.
