# Schematron Rules for DITA Validation

ISO Schematron rules generated from the Red Hat Vale style YAML files. These rules validate DITA XML content during DITA-OT builds, catching style and terminology issues.

## Prerequisites

- DITA-OT 4.3.1+ (`dita --version`)
- Java 17+ (Temurin/OpenJDK)

## Installing the DITA-OT Plugins

Two plugins are required:

```bash
# GraalVM JavaScript engine (required by the Schematron plugin on Java 17+)
dita --install https://github.com/stefan-jung/org.jung.graal/archive/master.zip --force

# Schematron validation plugin
dita --install https://github.com/stefan-jung/org.jung.schematron/archive/master.zip --force
```

### DITA-OT 4.x Store Compatibility Fix

DITA-OT 4.x uses an in-memory store by default. The Schematron plugin's `<ditafileset>` type wraps files in `StoreResource` objects that ph-schematron cannot resolve. To fix this, edit the installed plugin's build file:

**File:** `<DITA-OT>/plugins/org.jung.schematron/build_schematron-validation.xml`

Replace all `<ditafileset>` elements with plain `<fileset>` elements:

```xml
<!-- Before (broken with DITA-OT 4.x in-memory store) -->
<ditafileset format="dita" />

<!-- After -->
<fileset dir="${dita.temp.dir}" includes="**/*.dita" />
```

And for map validation:

```xml
<!-- Before -->
<ditafileset format="ditamap" />

<!-- After -->
<fileset dir="${dita.temp.dir}" includes="**/*.ditamap" />
```

There are 4 occurrences total (2 for maps, 2 for topics) in the `-schematron-validate-maps` and `-schematron-validate-topics` targets.

## Generating the Schematron Rules

```bash
python3 tools/vale-to-schematron.py
```

This reads Vale YAML files from `.vale/styles/RedHat/` and generates:

- Individual `.sch` files in `schematron/output/` (one per Vale rule)
- `RedHat-all.sch` — a combined schema with all patterns inlined

### Validating Generated Rules

```bash
python3 tools/validate-schematron.py
```

### Running Tests

Smoke-test with lxml (no DITA-OT required, XSLT 1.0 only):

```bash
python3 tools/test-schematron.py
```

Full XPath 2.0 validation with DITA-OT (requires DITA-OT + plugins installed):

```bash
./schematron/test.sh              # test all rules
./schematron/test.sh Contractions # test a single rule
./schematron/test.sh -l           # list available rules
```

## Running Schematron Validation with DITA-OT

### Topic validation only

```bash
dita --input your-file.dita \
     --format html5 \
     -Dschematron.topic.validation.files=/path/to/schematron/output/RedHat-all.sch \
     -Dschematron.fail=true \
     -Dschematron.failon.error=true
```

### With map validation

```bash
dita --input your-map.ditamap \
     --format html5 \
     -Dschematron.topic.validation.files=/path/to/schematron/output/RedHat-all.sch \
     -Dschematron.map.validation.files=/path/to/map-validation.sch \
     -Dschematron.fail=true \
     -Dschematron.failon.error=true
```

### Configuration Properties

| Property | Default | Description |
|----------|---------|-------------|
| `schematron.topic.validation.files` | (none) | Comma-separated paths to topic Schematron files |
| `schematron.map.validation.files` | (none) | Comma-separated paths to map Schematron files |
| `schematron.fail` | `false` | Fail the build on Schematron violations |
| `schematron.failon.fatal` | `true` | Treat fatal-level violations as build failures |
| `schematron.failon.error` | `true` | Treat error-level violations as build failures |
| `schematron.failon.warning` | `false` | Treat warning-level violations as build failures |
| `schematron.failon.info` | `false` | Treat info-level violations as build failures |
| `schematron.processing.engine` | `pure` | Processing engine: `pure`, `schematron`, or `xslt` |
| `schematron.svrl.dir` | (none) | Directory to write SVRL output files |

### Suppressing GraalVM Warnings

To suppress the "interpreted mode" warning from GraalVM:

```bash
export ANT_OPTS="-Dpolyglot.engine.WarnInterpreterOnly=false"
```

## Test Fixtures

The `schematron/fixtures/` directory contains per-rule DITA test files:

- `test-{RuleName}.dita` — contains text that triggers the corresponding rule

## Regex Compatibility

The generated Schematron rules use XPath 2.0 `matches()` with XML Schema regular expressions. Key differences from PCRE/Vale regex:

- `\b` (word boundary) is replaced with `(^|\W)` / `(\W|$)`
- Negative lookbehind `(?<!...)` and lookahead `(?!...)` are stripped (not supported in XML Schema regex)
- Backreferences `\1` are not supported; alternative XPath constructs are used

See `tools/vale-to-schematron.py` for the conversion logic.
