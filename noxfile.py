"""Nox sessions for testing and development tasks.

This replaces justfile with a modern Python-based task runner that uses uv.
Run with: uv run nox [session]
"""

import shutil
from pathlib import Path

import nox

# Use uv for all sessions
nox.options.default_venv_backend = "uv"

# Stop on first failure when running multiple sessions
nox.options.stop_on_first_error = True

# Isolate and prevent running system-installed or external venv tooling.
nox.options.error_on_external_run = True

# Default sessions to run (in order) when no session is specified
nox.options.sessions = [
    "format",
    "lint",
    "cov-clean",
    "test",
    "cov-combine",
]

# Python versions to test against
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]

# Tools run only on the latest Python version
TOOLS_PYTHON = PYTHON_VERSIONS[-1]


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run tests with coverage for each Python version."""
    session.install(".", "--group", "test")

    test_args = session.posargs if session.posargs else ["tests"]

    junit_args = []
    if session.python == PYTHON_VERSIONS[-1]:
        junit_args = ["--junit-xml=tests-results.xml"]

    session.run(
        "coverage",
        "run",
        "--parallel-mode",
        "--source",
        "html5tagger",
        "-m",
        "pytest",
        "-qq",
        *junit_args,
        *test_args,
    )


@nox.session(python=TOOLS_PYTHON)
def lint(session):
    """Run linting checks with ruff and type checking with ty."""
    session.install(".", "--group", "test")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
    session.run("ty", "check", "html5tagger")


@nox.session(python=TOOLS_PYTHON)
def format(session):
    """Format code with ruff."""
    session.install("--group", "test")
    session.run("ruff", "check", "--fix", "--unsafe-fixes", ".")
    session.run("ruff", "format", ".")


@nox.session(python=TOOLS_PYTHON, name="cov-clean")
def cov_clean(session):
    """Clean all coverage data and reports."""
    for path in Path(".").glob(".coverage*"):
        if path.is_file():
            path.unlink()

    htmlcov_path = Path("htmlcov")
    if htmlcov_path.exists():
        shutil.rmtree(htmlcov_path)

    coverage_xml = Path("coverage.xml")
    if coverage_xml.exists():
        coverage_xml.unlink()

    tests_results_xml = Path("tests-results.xml")
    if tests_results_xml.exists():
        tests_results_xml.unlink()


@nox.session(python=TOOLS_PYTHON, name="cov-combine")
def cov_combine(session):
    """Generate all coverage reports from previously collected data."""
    session.install("coverage")
    session.run("coverage", "combine", "--keep", success_codes=[0, 1])
    session.run("coverage", "report", "-m")
    session.run("coverage", "html")
    session.run("coverage", "xml")


@nox.session(python=TOOLS_PYTHON)
def clean(session):
    """Clean build artifacts and caches."""
    session.notify("cov-clean")

    patterns = [
        "**/*.pyc",
        "**/*.pyo",
        "**/__pycache__",
        "dist",
        "build",
        "*.egg-info",
        ".pytest_cache",
        ".ruff_cache",
        ".nox",
    ]

    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)


@nox.session(python=TOOLS_PYTHON)
def ty(session):
    """Run type checking with ty."""
    session.install(".", "--group", "test")
    session.run("ty", "check", "html5tagger")


@nox.session(python=False)
def coverage(session):
    """Faster coverage checks. Does not abort on lint or test failures."""
    session.run(
        "uv",
        "run",
        "nox",
        "--no-stop-on-first-error",
        "-s",
        "lint",
        "cov-clean",
        f"test-{TOOLS_PYTHON}",
        "cov-combine",
        external=True,
        success_codes=[0, 1],
    )
