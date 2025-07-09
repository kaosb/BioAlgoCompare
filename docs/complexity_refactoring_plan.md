# Complexity Refactoring Plan

## Overview

This document outlines the refactoring plan for 17 complexity violations identified in the codebase. The analysis focuses on actively used files and prioritizes refactoring based on importance and complexity.

## File Status Analysis

### Active Files (In Use)
1. **utils/statistical_analysis.py** - Core statistical functionality used by main scripts
2. **utils/benchmarking.py** - Core benchmarking functionality 
3. **utils/advanced_statistical_analysis.py** - Advanced stats used by analyze.py
4. **problems/vrp.py** - Core VRP problem implementation

### Potentially Obsolete Files (No Active References)
1. **convert_solomon_format.py** - No imports found
2. **run_extended_solomon_benchmark.py** - No imports found
3. **utils/fixed_method.py** - Only referenced by modify_statistical_analysis.py
4. **utils/html_generator.py** - No direct imports found

## Priority Ranking

### Priority 1 (Critical - Highest Complexity & Most Used)
1. **utils/statistical_analysis.py::generate_statistical_analysis_report** (Complexity: 29)
   - Critical for generating statistical reports
   - Used by main analyze.py script
   - Extremely high complexity needs immediate attention

### Priority 2 (High - Core Functionality)
2. **utils/benchmarking.py::create_benchmark_report** (Complexity: 17)
   - Essential for benchmark reporting
   - Used by main CLI and scripts
   
3. **problems/vrp.py::load_instance** (Complexity: 16)
   - Core functionality for loading VRP instances
   - Used by all VRP algorithms

### Priority 3 (Medium - Supporting Functions)
4. **utils/advanced_statistical_analysis.py::generate_stats_report** (Complexity: 14)
5. **utils/statistical_analysis.py::vargha_delaney_a_measure** (Complexity: 14)
6. **utils/statistical_analysis.py::interpret_effect_size** (Complexity: 14)
7. **utils/benchmarking.py::run_benchmark** (Complexity: 13)
8. **utils/benchmarking.py::plot_performance_radar** (Complexity: 13)

### Priority 4 (Low - Potentially Obsolete)
- Files in this category may be candidates for removal rather than refactoring

## Detailed Refactoring Strategies

### 1. utils/statistical_analysis.py::generate_statistical_analysis_report (Complexity: 29)

**Current Issues:**
- Single massive function handling multiple responsibilities
- Deeply nested conditionals and try-except blocks
- Mixed concerns: data validation, statistical tests, visualization, HTML generation
- Inline CSS and HTML generation

**Refactoring Strategy:**

```python
# Break down into smaller, focused functions:

class StatisticalReportGenerator:
    def __init__(self, data_df, metric="best_fitness", alpha=0.05):
        self.data_df = data_df
        self.metric = metric
        self.alpha = alpha
        self.results = {}
        
    def generate_report(self, output_file=None):
        """Main entry point - orchestrates report generation"""
        output_file = self._prepare_output_file(output_file)
        
        if not self._validate_data():
            return self._generate_error_report(output_file)
            
        self._run_statistical_tests()
        self._generate_visualizations()
        html_content = self._build_html_report()
        
        self._save_report(output_file, html_content)
        return output_file
        
    def _validate_data(self):
        """Validate input data has sufficient instances/algorithms"""
        # Extract validation logic
        pass
        
    def _run_statistical_tests(self):
        """Execute all statistical tests and store results"""
        self.results['friedman'] = self._run_friedman_test()
        self.results['posthoc'] = self._run_posthoc_tests()
        self.results['wilcoxon'] = self._run_wilcoxon_tests()
        self.results['effect_sizes'] = self._calculate_effect_sizes()
        
    def _generate_visualizations(self):
        """Generate all plots and convert to base64"""
        self.visualizations = {
            'cd_diagram': self._create_cd_diagram(),
            'rank_boxplot': self._create_rank_boxplot(),
            'posthoc_heatmap': self._create_posthoc_heatmap(),
            'effect_heatmap': self._create_effect_heatmap(),
            'vd_heatmap': self._create_vd_heatmap()
        }
        
    def _build_html_report(self):
        """Build HTML report using template"""
        template = self._load_html_template()
        return template.render(**self.results, **self.visualizations)
```

**Benefits:**
- Separation of concerns
- Easier testing of individual components
- Reusable visualization methods
- Template-based HTML generation

### 2. utils/benchmarking.py::create_benchmark_report (Complexity: 17)

**Current Issues:**
- Long function with multiple responsibilities
- Inline HTML/CSS generation
- Mixed data processing and visualization

**Refactoring Strategy:**

```python
class BenchmarkReportBuilder:
    def __init__(self, benchmark_results):
        self.results = benchmark_results
        self.instances = self._group_by_instance()
        
    def create_report(self, filename=None):
        """Main method to create benchmark report"""
        filename = self._prepare_filename(filename)
        
        summary_df = self._create_summary_dataframe()
        visualizations = self._generate_visualizations()
        
        html_content = self._render_html_report(summary_df, visualizations)
        self._save_report(filename, html_content)
        
        return filename
        
    def _group_by_instance(self):
        """Group results by instance name"""
        instances = defaultdict(list)
        for result in self.results:
            instances[result.instance_name].append(result)
        return dict(instances)
        
    def _create_summary_dataframe(self):
        """Create summary DataFrame from results"""
        # Extract summary data creation logic
        pass
        
    def _generate_visualizations(self):
        """Generate all visualizations for each instance"""
        visualizations = {}
        for instance_name, results in self.instances.items():
            visualizations[instance_name] = {
                'quality': self._plot_quality(results),
                'time': self._plot_time(results),
                'convergence': self._plot_convergence(results)
            }
        return visualizations
        
    def _render_html_report(self, summary_df, visualizations):
        """Render HTML using template engine"""
        template = HTMLReportTemplate()
        return template.render(
            summary=summary_df,
            visualizations=visualizations,
            instances=self.instances,
            timestamp=datetime.now()
        )
```

### 3. problems/vrp.py::load_instance (Complexity: 16)

**Current Issues:**
- Complex parsing logic with multiple conditionals
- Mixed file I/O and data processing
- Error handling scattered throughout

**Refactoring Strategy:**

```python
class VRPInstanceLoader:
    """Dedicated class for loading VRP instances"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.metadata = {}
        self.nodes = []
        self.demands = []
        
    def load(self):
        """Main loading method"""
        content = self._read_file()
        self._parse_metadata(content)
        self._parse_nodes(content)
        self._parse_demands(content)
        self._validate_instance()
        
        return VRPInstance(
            metadata=self.metadata,
            nodes=self.nodes,
            demands=self.demands
        )
        
    def _read_file(self):
        """Read and return file content"""
        with open(self.filepath, 'r') as f:
            return f.read()
            
    def _parse_metadata(self, content):
        """Extract instance metadata"""
        parsers = {
            'NAME': self._parse_name,
            'TYPE': self._parse_type,
            'DIMENSION': self._parse_dimension,
            'CAPACITY': self._parse_capacity
        }
        
        for line in content.split('\n'):
            for key, parser in parsers.items():
                if line.startswith(key):
                    parser(line)
                    break
                    
    def _parse_nodes(self, content):
        """Parse node coordinates section"""
        # Extract node parsing logic
        pass
        
    def _parse_demands(self, content):
        """Parse demand section"""
        # Extract demand parsing logic
        pass
```

## Implementation Plan

### Phase 1 (Week 1-2)
1. Refactor `generate_statistical_analysis_report` 
   - Create `StatisticalReportGenerator` class
   - Extract visualization methods
   - Implement template-based HTML generation
   - Add comprehensive tests

### Phase 2 (Week 2-3)
2. Refactor `create_benchmark_report`
   - Create `BenchmarkReportBuilder` class
   - Separate data processing from visualization
   - Implement reusable components

3. Refactor `load_instance` in vrp.py
   - Create `VRPInstanceLoader` class
   - Separate parsing logic
   - Improve error handling

### Phase 3 (Week 3-4)
4. Refactor remaining Priority 3 functions
5. Review and potentially remove obsolete files
6. Update all imports and dependencies

## Testing Strategy

1. **Unit Tests**: Create tests for each extracted method
2. **Integration Tests**: Ensure refactored code produces same output
3. **Performance Tests**: Verify no performance degradation
4. **Regression Tests**: Run full test suite after each refactoring

## Success Metrics

1. All functions have complexity ≤ 10
2. Test coverage remains at or above current levels
3. No breaking changes to public APIs
4. Performance metrics remain stable or improve

## Notes

- Consider using template engines (Jinja2) for HTML generation
- Extract common visualization utilities to shared module
- Consider deprecation warnings for obsolete files before removal
- Document all API changes in CHANGELOG.md