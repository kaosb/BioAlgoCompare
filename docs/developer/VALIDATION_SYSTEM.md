# Result Validation System

## Overview

The BioAlgoCompare validation system provides comprehensive validation of experimental results to ensure data integrity, consistency, and scientific validity. It supports multiple validation levels, custom validators, and seamless integration with the experiment tracking and database systems.

## Features

- **Multi-level Validation**: From basic structure checks to advanced statistical analysis
- **Custom Validators**: Extensible system for domain-specific validation rules
- **Automatic Integration**: Works seamlessly with ExperimentTracker and ResultsDatabase
- **Detailed Reporting**: Comprehensive reports with actionable feedback
- **Batch Processing**: Efficient validation of multiple results
- **Persistence**: Save and load validation reports

## Validation Levels

### 1. BASIC
- Structure validation
- Required fields check
- Data type verification

### 2. STANDARD (default)
- All BASIC checks
- Numeric stability (NaN, Inf detection)
- Value range validation
- Consistency checks

### 3. STRICT
- All STANDARD checks
- Constraint validation (e.g., VRP solution validity)
- Solution quality assessment
- Cross-field consistency

### 4. SCIENTIFIC
- All STRICT checks
- Statistical properties validation
- Reproducibility checks
- Sample size adequacy
- Outlier detection

## Quick Start

### Basic Usage

```python
from utils.result_validation import ResultValidator, ValidationLevel, quick_validate
from utils.result_schema import StandardResult

# Quick validation
result = load_result()  # Your result
is_valid = quick_validate(result)  # Returns True/False

# Detailed validation
validator = ResultValidator(ValidationLevel.STANDARD)
report = validator.validate_result(result)

if not report.passed:
    print(f"Validation failed with {len(report.issues)} issues")
    for issue in report.issues:
        print(f"[{issue.level.value}] {issue.message}")
```

### Integration with ExperimentTracker

```python
from utils.validation_integration import ValidatedExperimentTracker

# Create tracker with automatic validation
tracker = ValidatedExperimentTracker(
    base_dir="experiments",
    auto_validate=True,
    validation_level=ValidationLevel.STANDARD
)

# Results are automatically validated when saved
tracker.start_experiment(config)
# ... run experiment ...
tracker.save_current()  # Validation happens here

# Get validation report
report = tracker.get_validation_report(experiment_id)
```

### Integration with ResultsDatabase

```python
from utils.validation_integration import ValidatedResultsDatabase

# Create database with automatic validation
db = ValidatedResultsDatabase(
    db_path="results.db",
    auto_validate=True,
    validation_level=ValidationLevel.STANDARD
)

# Results are validated before insertion
db.insert_result(result)  # Validation happens here

# Query validation statistics
stats = db.get_validation_statistics()
print(f"Pass rate: {stats['pass_rate']:.2%}")
```

## Custom Validators

### Creating Custom Validators

```python
from utils.result_validation import ValidationIssue, ValidationStatus

def my_custom_validator(result: StandardResult, report: ValidationReport) -> None:
    """Custom validation logic."""
    # Check some condition
    if result.data.best_fitness > 1000:
        report.add_issue(ValidationIssue(
            level=ValidationStatus.WARNING,
            category='custom',
            message='Fitness value is unusually high',
            field='best_fitness',
            value=result.data.best_fitness,
            suggestion='Check problem scaling or algorithm parameters'
        ))

# Add to validator
validator = ResultValidator()
validator.add_custom_validator('high_fitness', my_custom_validator)
```

### Pre-built Validators

#### VRP Validator

```python
from utils.result_validation import create_vrp_validator

# Create VRP-specific validator
vrp_validator = create_vrp_validator(
    capacity_check=True,
    distance_check=True
)

validator.add_custom_validator('vrp', vrp_validator)
```

#### Convergence Validator

```python
from utils.result_validation import create_convergence_validator

# Create convergence quality validator
conv_validator = create_convergence_validator(
    min_improvement=0.05,  # 5% minimum improvement
    max_stagnation=50      # Max iterations without improvement
)

validator.add_custom_validator('convergence', conv_validator)
```

## Validation Report Structure

```python
@dataclass
class ValidationReport:
    result_id: str
    validation_level: ValidationLevel
    timestamp: datetime
    passed: bool
    issues: List[ValidationIssue]
    summary: Dict[str, Any]
```

### Issue Categories

- `structure`: Data structure problems
- `metadata`: Missing or invalid metadata
- `numeric`: Numeric errors (NaN, Inf, out of range)
- `consistency`: Internal consistency violations
- `convergence`: Convergence quality issues
- `solution`: Solution validity problems
- `statistical`: Statistical property violations
- `reproducibility`: Reproducibility concerns
- `custom`: Custom validator issues

### Issue Levels

- `WARNING`: Potential problems that don't invalidate results
- `ERROR`: Serious problems that affect validity
- `CRITICAL`: Severe errors that completely invalidate results

## Batch Validation

```python
# Validate multiple results
results = load_multiple_results()

# Serial processing
reports = validator.validate_batch(results, parallel=False)

# Parallel processing (faster for many results)
reports = validator.validate_batch(results, parallel=True)

# Analyze results
passed = sum(1 for r in reports.values() if r.passed)
print(f"Passed: {passed}/{len(results)}")
```

## Configuration

### Setting Validation Limits

```python
validator = ResultValidator()

# Customize validation limits
validator.limits.update({
    'min_fitness': 0.0,
    'max_fitness': 10000.0,
    'min_time': 0.001,
    'max_time': 7200.0,  # 2 hours
    'fitness_tolerance': 1e-9
})
```

### Auto-validation Setup

```python
from utils.validation_integration import setup_auto_validation

# Setup automatic validation for existing components
tracker, database = setup_auto_validation(
    tracker=existing_tracker,    # Optional
    database=existing_database,  # Optional
    level=ValidationLevel.STANDARD
)
```

## Use Cases

### 1. Post-Experiment Validation

```python
# After running experiments
results = run_experiments()

# Validate all results
validator = ResultValidator(ValidationLevel.STRICT)
for result in results:
    report = validator.validate_result(result)
    if not report.passed:
        logger.warning(f"Result {result.result_id} has issues")
        # Handle invalid results
```

### 2. Pre-Publication Validation

```python
# Scientific validation before publishing results
validator = ResultValidator(ValidationLevel.SCIENTIFIC)

# Add domain-specific validators
validator.add_custom_validator('vrp', create_vrp_validator())
validator.add_custom_validator('stats', statistical_validator)

# Validate with strict criteria
report = validator.validate_result(result)
if not report.passed:
    print("Result does not meet publication standards")
    # Fix issues before publishing
```

### 3. Continuous Integration

```python
# In CI/CD pipeline
def test_algorithm_results():
    results = run_algorithm_tests()
    
    for result in results:
        assert quick_validate(result, ValidationLevel.STANDARD), \
            f"Algorithm produced invalid result: {result.result_id}"
```

### 4. Data Quality Monitoring

```python
# Monitor data quality over time
db = ValidatedResultsDatabase()

# Get validation statistics
stats = db.get_validation_statistics()
print(f"Overall pass rate: {stats['pass_rate']:.2%}")
print(f"Average issues per result: {stats['avg_issues_per_result']:.1f}")

# Get failed validations for investigation
failed = db.get_failed_validations()
for result in failed:
    print(f"Failed: {result['result_id']} - {result['total_issues']} issues")
```

## Best Practices

1. **Choose Appropriate Level**: Use STANDARD for development, STRICT for benchmarks, SCIENTIFIC for publications

2. **Add Domain-Specific Validators**: Create custom validators for your specific problem domain

3. **Handle Validation Failures**: Don't ignore validation failures - they indicate potential problems

4. **Review Warnings**: Even if validation passes, review warnings for quality improvements

5. **Validate Early**: Enable auto-validation to catch issues as soon as they occur

6. **Document Custom Rules**: Clearly document any custom validation rules for reproducibility

## Troubleshooting

### Common Issues

1. **False Positives**: Adjust validation limits if getting incorrect failures
2. **Missing Validators**: Add custom validators for domain-specific checks
3. **Performance**: Use batch validation with parallel=True for many results
4. **Memory Usage**: Process large result sets in chunks

### Debug Mode

```python
# Enable detailed logging
import logging
logging.getLogger('utils.result_validation').setLevel(logging.DEBUG)

# Validate with detailed output
report = validator.validate_result(result)
```

## API Reference

See the inline documentation in:
- `utils/result_validation.py` - Core validation system
- `utils/validation_integration.py` - Integration components
- `tests/test_result_validation.py` - Usage examples