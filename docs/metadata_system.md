# Metadata System Documentation

## Overview

The BioAlgoCompare metadata system ensures complete reproducibility by automatically capturing comprehensive information about every algorithm execution. This system is crucial for scientific rigor and allows exact reproduction of experimental results.

## What is Captured

### 1. System Information
- Platform (OS type and version)
- CPU architecture and count
- Memory (total and available)
- Python version and implementation

### 2. Git Information
- Current commit hash
- Branch name
- Dirty state (uncommitted changes)
- Remote URL
- Author information
- Commit message and date

### 3. Execution Information
- Start and end timestamps
- Total duration
- CPU usage (average and peak)
- Memory usage (average and peak)
- Random seed used
- Parallelization settings

### 4. Dependencies
- Complete list of installed packages
- Exact version of each package
- Ensures environment can be recreated

### 5. Result Integrity
- SHA256 checksum of results
- Validation status
- Any validation errors

## Usage

### Basic Usage with CLI

```bash
# Run algorithm with full metadata capture
python scripts/cli/run_with_metadata.py -a hoa -i A-n32-k5.vrp -r 30

# Run without resource monitoring (faster)
python scripts/cli/run_with_metadata.py -a egto -i P-n16-k8.vrp --no-monitor-resources

# Run benchmark with metadata
python scripts/cli/benchmark_with_metadata.py -a "hoa,egto,foa" -i small
```

### Programmatic Usage

```python
from utils.result_metadata_integration import wrap_algorithm_with_metadata
from algorithms.hoa_v2 import HOAV2

# Wrap any algorithm to capture metadata
MetadataHOA = wrap_algorithm_with_metadata(HOAV2)

# Use as normal
algo = MetadataHOA(problem, population_size=30, max_iterations=100, seed=42)
best_solution = algo.execute()

# Get complete result with metadata
result = algo.get_complete_result()
```

### Using the Enhanced Result Schema

```python
from utils.result_schema_v2 import StandardResultV2

# Results automatically include metadata
result = StandardResultV2(...)

# Access metadata
print(f"Platform: {result.system_info.platform}")
print(f"Git commit: {result.git_info.commit_hash}")
print(f"Checksum: {result.checksum}")

# Verify integrity
if result.verify_integrity():
    print("Result integrity verified")
```

## Result Storage

### Directory Structure
```
results/
├── metadata/
│   ├── algorithm_instance_timestamp_metadata.json  # Complete results
│   └── algorithm_instance_timestamp_summary.txt    # Human-readable summary
├── benchmark_timestamp/
│   ├── metadata/                                   # Enhanced results
│   ├── results_timestamp.json                      # Standard format
│   └── benchmark_config.json                       # Configuration
└── plots/
```

### Result Format

The enhanced result format (`StandardResultV2`) includes:

```json
{
  "result_id": "unique-uuid",
  "version": "2.0.0",
  "timestamp": "2024-01-15T10:30:00",
  "result_type": "MULTI_RUN",
  "problem_info": {...},
  "algorithm_info": {...},
  "runs": [...],
  "statistics": {...},
  "system_info": {
    "platform": "Darwin",
    "cpu_count": 10,
    "memory_total_gb": 16.0,
    ...
  },
  "git_info": {
    "commit_hash": "abc123...",
    "branch": "main",
    "is_dirty": false,
    ...
  },
  "execution_info": {
    "start_time": "...",
    "duration_seconds": 123.45,
    "cpu_percent_avg": 85.2,
    "memory_peak_mb": 512.3,
    ...
  },
  "dependencies": [...],
  "checksum": "sha256-hash",
  "validated": true
}
```

## Resource Monitoring

Resource monitoring runs in a separate thread during execution:

- CPU usage sampled every 0.5 seconds
- Memory usage tracked continuously
- No significant performance impact
- Can be disabled with `--no-monitor-resources`

## Reproducibility Workflow

1. **Capture**: Metadata is automatically captured during execution
2. **Store**: Results include all necessary information
3. **Share**: Complete result files can be shared
4. **Reproduce**: Others can verify environment and reproduce results

### Verifying Reproducibility

```python
# Load result
result = StandardResultV2.from_json("result.json")

# Check environment compatibility
current_system = SystemInfo.capture()
if current_system.platform != result.system_info.platform:
    print("Warning: Different platform")

# Verify integrity
if not result.verify_integrity():
    print("Warning: Result may have been modified")

# Get exact configuration
repro_info = result.get_reproducibility_info()
```

## Best Practices

1. **Always use metadata capture for experiments**
   - Ensures results can be reproduced
   - Provides context for analysis

2. **Include git information**
   - Commit changes before experiments
   - Note any uncommitted changes

3. **Document dependencies**
   - Use requirements.txt or environment.yml
   - Metadata captures current state

4. **Verify checksums**
   - Check integrity before analysis
   - Detect any modifications

5. **Archive complete results**
   - Keep metadata with results
   - Enable future verification

## Integration with Existing Tools

The metadata system integrates seamlessly with:

- **Benchmarking**: Enhanced benchmarks capture metadata for all runs
- **Statistical Analysis**: Metadata provides context for comparisons
- **Visualization**: System info helps explain performance variations
- **Publication**: Complete information for reproducible research

## Performance Considerations

- Metadata capture adds ~0.1s overhead per run
- Resource monitoring adds ~2-5% CPU overhead
- Can be disabled for preliminary tests
- Always enable for final experiments

## Troubleshooting

### Git information not captured
- Ensure you're in a git repository
- Git must be installed and accessible

### High resource usage reported
- Normal during parallel execution
- Check `n_workers` setting

### Checksum verification fails
- File may have been modified
- Check for encoding issues