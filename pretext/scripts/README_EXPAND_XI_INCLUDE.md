# Xi:Include Preprocessor with set-xml-id Support

A Python tool that expands `<xi:include>` elements in PreTeXt XML files, with support for the `set-xml-id` attribute to rename element IDs at inclusion points.

## Problem This Solves

PreTeXt's native `set-xml-id` attribute on `<xi:include>` elements is not processed by the PreTeXt build system - it's a conceptual feature that doesn't actually work. This tool preprocesses XML files to:

1. **Expand all xi:include elements** by replacing them with the actual content from the referenced files
2. **Apply ID renaming** when `set-xml-id` attributes are present, allowing the same element to be included multiple times with different IDs

## Use Case: Problem Sets with Multiple Sections

When you have problem sets used by different lecture sections (MW and TR) but want to maintain a single source of truth for exercises:

```xml
<!-- ps01-mw.ptx: Original IDs -->
<xi:include href="problems.ptx" xpointer="xpointer(//exercise[@xml:id='p-2'])" />

<!-- ps01-tr.ptx: Same exercises, but with -tr suffix -->
<xi:include href="problems.ptx" xpointer="xpointer(//exercise[@xml:id='p-2'])" set-xml-id="p-2-tr" />
```

After preprocessing, the expanded file will contain:
```xml
<!-- MW version: original ID -->
<exercise xml:id="p-2">...</exercise>

<!-- TR version: renamed ID -->
<exercise xml:id="p-2-tr">...</exercise>
```

This eliminates duplicate `@xml:id` conflicts while maintaining a single canonical problem source.

## Installation

Requires Python 3 with `lxml`:

```bash
pip install lxml
```

## Usage

```bash
python3 expand_xi_include_with_id.py <input_file> <output_file> [--base-dir <dir>]
```

### Arguments

- `input_file`: Path to the PreTeXt XML file to process
- `output_file`: Path where the expanded XML will be written
- `--base-dir`: Base directory for resolving relative paths in `href` attributes (defaults to the input file's directory)

### Example

```bash
# Expand psets.ptx, with relative paths resolved from source/psets/
python3 expand_xi_include_with_id.py source/psets/psets.ptx /tmp/psets-expanded.ptx --base-dir source/psets

# Then use the expanded file for building
pretext build psets-web
```

## How It Works

1. **Iterative expansion**: Processes xi:include elements in multiple passes to handle nested includes
2. **File loading**: Loads referenced files and evaluates XPath expressions in `xpointer` attributes
3. **Element cloning**: Deep-copies matched elements to avoid reference issues
4. **ID renaming**: When `set-xml-id` is present, updates the `@xml:id` attribute on the cloned element
5. **Insertion**: Replaces the xi:include element with the processed cloned element

## Supported XPointer Expressions

Currently supports basic XPath-style expressions:

- `xpointer(//exercise[@xml:id='exercise-id'])` - Find exercise by ID
- `xpointer(//section[1])` - Find first section
- `xpointer(//section[1]/introduction)` - Find specific descendant elements

## Limitations

- Does not validate PreTeXt-specific constraints
- May not handle all complex XPath expressions (contributions welcome!)
- Circular includes are detected but continue processing (with warnings)
- Maximum iteration limit of 100 to prevent infinite loops

## Integration with PreTeXt Build

Use this as a preprocessing step in your build workflow:

```bash
# Preprocess the source
python3 scripts/expand_xi_include_with_id.py source/psets/psets.ptx source/psets/psets-expanded.ptx --base-dir source/psets

# Build from the expanded file (manually copy/replace if needed)
cp source/psets/psets-expanded.ptx source/psets/psets.ptx
pretext build psets-web

# Restore the original if needed
git checkout source/psets/psets.ptx
```

Or create a wrapper script for your build system.

## Example: Consolidating Exercises

**Original structure:**
- `ps01-mw.ptx` - Contains 5 inline exercises with IDs: `p-1`, `p-2`, etc.
- `ps01-tr.ptx` - Same exercises inline (duplicated)
- `ps02-mw.ptx` - Contains 6 different inline exercises

**Refactored structure:**
- `problems.ptx` - Master file with all 11 exercises (canonical source)
- `ps01-mw.ptx` - Includes from `problems.ptx` with original IDs
- `ps01-tr.ptx` - Includes from `problems.ptx` with `set-xml-id` suffixes (`-tr`)
- `ps02-mw.ptx` - Includes from `problems.ptx` with original IDs
- `ps02-tr.ptx` - Includes from `problems.ptx` with `set-xml-id` suffixes (`-tr`)

**After preprocessing:** All exercises are expanded inline with appropriate IDs, ready for PreTeXt to build without conflicts.

## Verification

Check the preprocessed output for expected elements:

```bash
# Count expanded exercises
grep -c "<exercise" psets-expanded.ptx

# Verify ID variants exist
grep 'xml:id="p-2"' psets-expanded.ptx         # Should find original
grep 'xml:id="p-2-tr"' psets-expanded.ptx     # Should find TR variant

# Check for remaining xi:include (should be minimal)
grep -c "xi:include" psets-expanded.ptx
```

## Future Enhancements

- Add command-line option to validate result against PreTeXt schema
- Support for more complex XPath expressions
- Optional output to preserve or remove namespace declarations
- Integration with PreTeXt CLI as a plugin/extension
