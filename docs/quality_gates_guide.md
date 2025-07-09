# Quality Gates Guide for BioAlgoCompare

## Overview

BioAlgoCompare implements a comprehensive **local quality gates system** that ensures code quality without using cloud CI/CD resources. All checks run on your development machine, providing immediate feedback before code is committed.

## Why Local Quality Gates?

1. **Immediate Feedback**: No waiting for CI/CD pipelines
2. **Zero Cloud Costs**: Everything runs on your machine
3. **Early Detection**: Issues caught before they reach the repository
4. **Developer Friendly**: Fast, focused checks that don't interrupt flow
5. **Privacy**: Code never leaves your machine for validation

## Available Quality Checks

### Required Checks ✅
These must pass before committing:

| Check | Description | Tool |
|-------|-------------|------|
| `code_formatting` | Ensures consistent code style | Ruff |
| `code_linting` | Detects code quality issues | Ruff |
| `critical_tests` | Runs fast, essential tests | Pytest |
| `circular_imports` | Detects import cycles | Custom |
| `reproducibility` | Validates seed handling | Custom |

### Optional Checks 📋
Recommended but not blocking:

| Check | Description | Tool |
|-------|-------------|------|
| `complexity_check` | Measures cyclomatic complexity | Custom |
| `naming_conventions` | Validates naming standards | Custom |
| `security_check` | Scans for vulnerabilities | Bandit |
| `type_checking` | Validates type annotations | MyPy |
| `docstring_coverage` | Measures documentation | Interrogate |

## Quick Start

### 1. Install Quality Tools

```bash
# Install all required tools
pip install ruff pytest bandit mypy pre-commit interrogate

# Install BioAlgoCompare in development mode
pip install -e .
```

### 2. Install Git Hooks

```bash
# Install pre-commit hooks
bioalgo quality install-hooks

# This installs:
# - Pre-commit hook (runs before each commit)
# - Commit-msg hook (validates commit messages)
```

### 3. Run Quality Checks

```bash
# Run all checks
bioalgo quality check

# Run only required checks
bioalgo quality check --required-only

# Run specific checks
bioalgo quality check --checks code_formatting --checks critical_tests

# Skip certain checks
bioalgo quality check --skip type_checking
```

## Usage Examples

### Before Committing Code

```bash
# 1. Format your code
bioalgo quality format --fix

# 2. Fix linting issues
bioalgo quality lint --fix

# 3. Run all quality gates
bioalgo quality check --required-only
```

### Check Code Complexity

```bash
# Check specific file
bioalgo quality complexity algorithms/hoa.py

# Check entire directory with custom threshold
bioalgo quality complexity algorithms/ --max-complexity 15

# Generate detailed report
bioalgo quality complexity . --report
```

### Verify Naming Conventions

```bash
# Check algorithms
bioalgo quality naming algorithms/

# Check entire project
bioalgo quality naming .
```

### Run Critical Tests

```bash
# Run all critical tests
bioalgo quality test-critical

# Run only failed tests
bioalgo quality test-critical --failed
```

## Pre-commit Configuration

The `.pre-commit-config.yaml` file defines all automatic checks:

```yaml
repos:
  # Code formatting and linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff         # Linting
      - id: ruff-format  # Formatting

  # Security scanning  
  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit

  # Custom project checks
  - repo: local
    hooks:
      - id: check-circular-imports
      - id: check-reproducibility
      - id: check-naming
      - id: check-complexity
```

## Quality Standards

### Code Formatting
- **Style**: Black-compatible formatting via Ruff
- **Line Length**: 88 characters (configurable)
- **Import Sorting**: Automatic with Ruff

### Code Complexity
- **Max Complexity**: 10 (default), 15 (algorithms)
- **Measurement**: Cyclomatic complexity
- **Action**: Refactor complex functions

### Naming Conventions
- **Modules**: `snake_case`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Test Coverage
- **Critical Tests**: Must pass 100%
- **Convergence Tests**: Algorithm stability
- **Reproducibility Tests**: Deterministic results

## Troubleshooting

### Check What's Wrong

```bash
# Diagnose setup
bioalgo quality doctor

# List available checks
bioalgo quality list

# Generate detailed report
bioalgo quality report
```

### Common Issues

1. **"Ruff not found"**
   ```bash
   pip install ruff
   ```

2. **"Pre-commit hook failed"**
   ```bash
   # Run checks manually to see details
   bioalgo quality check
   ```

3. **"Tests failing"**
   ```bash
   # Run specific test with verbose output
   pytest tests/test_algorithms_convergence.py -xvs
   ```

## Advanced Usage

### Custom Quality Checks

Add custom checks to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: my-custom-check
      name: "My Custom Check"
      entry: python scripts/my_check.py
      language: system
      files: \.py$
```

### Parallel Execution

For faster checks on multi-core systems:

```bash
# Experimental parallel mode
bioalgo quality check --parallel
```

### JSON Output

For integration with other tools:

```bash
# Get results as JSON
bioalgo quality check --json > results.json
```

## Best Practices

1. **Run Before Committing**: Always run `bioalgo quality check --required-only`
2. **Fix Issues Early**: Use `--fix` flags when available
3. **Keep Complexity Low**: Refactor functions with complexity > 10
4. **Document Your Code**: Maintain > 50% docstring coverage
5. **Use Type Hints**: Helps catch bugs early

## Integration with Development Workflow

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true
}
```

### Git Workflow

```bash
# 1. Make changes
git add .

# 2. Quality gates run automatically on commit
git commit -m "feat: add new algorithm"

# 3. If checks fail, fix and retry
bioalgo quality format --fix
bioalgo quality lint --fix
git add .
git commit -m "feat: add new algorithm"
```

## Summary

The local quality gates system ensures:

- ✅ **Consistent code style** across the project
- ✅ **Early bug detection** before commits
- ✅ **Maintained standards** without manual review
- ✅ **Fast feedback** without cloud delays
- ✅ **Zero infrastructure costs**

All while keeping the development process smooth and efficient!