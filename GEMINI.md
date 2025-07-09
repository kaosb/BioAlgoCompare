# BioAlgoCompare - Gemini Agent Guidelines

This document outlines key information and directives for the Gemini agent operating within the `BioAlgoCompare` repository. Adhering to these guidelines will ensure efficient and consistent development.

## 1. Project Overview

`BioAlgoCompare` is a framework designed for implementing and comparing bio-inspired optimization algorithms, primarily focused on Vehicle Routing Problems (VRP). The current development phase emphasizes achieving scientific rigor, reproducibility, and a clean, well-documented codebase.

## 2. Core Directives & Goals

*   **Scientific Rigor & Reproducibility**: All changes must contribute to the project's goal of high scientific rigor and reproducibility, essential for academic publication.
*   **V2 Architecture**: Prioritize and adhere to the `v2` architecture. All algorithms have been migrated to `v2`.
*   **Codebase Cleanliness**: Maintain a clean, well-documented, and idiomatic Python codebase. Remove unnecessary files and consolidate redundant scripts.

## 3. Technical Stack & Tools

*   **Language**: Python
*   **Testing**: `pytest` (with `pytest-cov` for coverage).
*   **Linting**: `ruff` (ensure all code adheres to `ruff` standards).
*   **Dependency Management**: `pyproject.toml` and `requirements.txt`.

## 4. Project Structure & Conventions

*   **Main CLI Entry Point**: `bioalgocompare.py` is the primary command-line interface.
*   **Algorithms**: Located in `algorithms/`. All are `v2` implementations.
*   **Problems**: Located in `problems/`. Includes `v2` problem definitions.
*   **Scripts**: Consolidated utility and benchmark scripts are in `scripts/`.
*   **Documentation**: Found in `docs/`. Keep this up-to-date with code changes.
*   **Tests**: Located in `tests/`.
*   **Benchmark Data**: Solomon instances are used for VRP benchmarks, typically found in `data/vrp/Solomon/`. Be aware of temporary file copying to `data/vrp/` during benchmark execution and subsequent cleanup.

## 5. Workflow & Best Practices for Gemini

*   **Understand Context**: Before making any changes, thoroughly read relevant files (`read_file`, `read_many_files`) and understand existing conventions (e.g., imports, formatting, naming, architectural patterns).
*   **Linting**: Always run `ruff` checks (`ruff check .`) after code modifications to ensure compliance. Address any reported issues.
*   **Testing**: Execute `pytest` (`pytest --cov=bioalgocompare`) to verify functionality and ensure no regressions. If new features are added or bugs fixed, consider adding/updating tests.
*   **Script Consolidation**: When dealing with scripts, aim for consolidation into `scripts/` and ensure they are callable via the main `bioalgocompare.py` CLI if appropriate.
*   **Documentation Updates**: If code changes impact user-facing functionality or internal architecture, update the relevant documentation in `docs/`.
*   **Temporary Files**: Be mindful of the benchmark workflow involving temporary copies of Solomon instances. Ensure proper cleanup if manual intervention is required.
*   **Commit Messages**: Follow the project's existing commit message style (check `git log`).
*   **No Legacy Code**: Actively remove or refactor any identified legacy code or files that do not align with the `v2` architecture or current project goals.

## 6. Current Focus

Refer to the `current_plan` in the compressed chat history for immediate priorities, which typically include fixing linting errors, resolving specific code issues, running tests, and updating documentation.