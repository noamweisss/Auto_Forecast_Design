"""
Tests Package - Automated Testing

This package contains unit tests that verify the code works correctly.
Tests are run automatically to catch bugs before they cause problems.

Running Tests:
    # Run all tests
    python -m pytest tests/ -v
    
    # Run a specific test file
    python -m pytest tests/test_parser.py -v
    
    # Run with coverage report
    python -m pytest tests/ --cov=src --cov-report=html

Test Files:
    test_parser.py    - Tests for XML parsing
    test_date_utils.py - Tests for date formatting
    test_rendering.py  - Tests for image generation

Why Write Tests?
    1. Catch bugs early - before you notice them visually
    2. Safe refactoring - change code confidently
    3. Documentation - tests show how code is supposed to work
"""

import pytest
