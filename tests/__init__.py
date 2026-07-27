"""
Tests Package - Automated Testing

This package contains the automated tests that verify the code works correctly.
They run in CI and locally to catch regressions before they reach output.

Running Tests:
    # Run the whole suite (fast, no cache plugin)
    python -m pytest tests -q -p no:cacheprovider

    # Run a specific test file
    python -m pytest tests/test_parser.py -v

Layout:
    The suite spans data, parsing, snapshots, settings, the design render
    context, the Playwright renderer, the application/CLI boundary, and file
    saving. See the individual test_*.py files for what each one covers, and
    conftest.py / fixtures/ for shared setup. Browser tests are marked
    `browser` (see pyproject.toml) because they need the installed Chromium.

Why Write Tests?
    1. Catch bugs early - before you notice them visually.
    2. Safe refactoring - change code confidently.
    3. Documentation - tests show how the code is supposed to work.
"""
