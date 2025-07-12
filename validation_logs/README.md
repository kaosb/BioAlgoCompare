# Validation Logs Directory

This directory stores validation and verification logs from algorithm runs.

## Purpose
- Capture detailed execution logs during validation runs
- Store debugging information for algorithm verification
- Maintain audit trail for experimental results

## Log Types
- Algorithm convergence logs
- Parameter validation logs
- Constraint violation reports
- Performance profiling logs

## Structure
Logs are organized by timestamp:
```
validation_logs/
├── YYYYMMDD_HHMMSS/
│   ├── algorithm_logs.txt
│   ├── validation_report.json
│   └── performance_profile.csv
```

## Usage
Validation logs are automatically generated when running with debug mode:
```bash
python scripts/analyze.py run --algorithm HO --debug --validation
```

## Retention Policy
- Keep logs for significant experiments
- Archive older logs after 30 days
- Remove logs for failed or test runs