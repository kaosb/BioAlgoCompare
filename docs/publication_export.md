# Publication Export System

The BioAlgoCompare publication export system generates publication-ready materials from benchmark results for scientific conferences and journals.

## Overview

The system automatically creates:
- **LaTeX tables** with descriptive statistics and rankings
- **Statistical test results** with significance levels 
- **Convergence plots** and distribution analysis figures
- **Replication data** for reproducibility
- **Citation files** in BibTeX, APA, and IEEE formats
- **Conference-specific packages** with submission guidelines

## Quick Start

### Basic Export
```bash
# Export all materials for CISTI 2025
bioalgo publish -i results/benchmark_results/ --conference "CISTI 2025"
```

### Selective Export
```bash
# Export only tables and figures
bioalgo publish -i results/ --include tables --include figures

# Export with IEEE formatting
bioalgo publish -i results/ --format ieee --compress
```

### Custom Output
```bash
# Specify output directory
bioalgo publish -i results/ -o publication_materials/
```

## Generated Materials

### 1. Statistical Tables (LaTeX)

- **Descriptive Statistics**: Mean, std dev, median for each algorithm-instance combination
- **Statistical Tests**: Friedman test results, p-values, effect sizes
- **Instance Rankings**: Algorithm rankings per VRP instance
- **Overall Performance**: Summary rankings across all instances

### 2. Figures and Visualizations

- **Convergence Plots**: Algorithm convergence behavior (PDF format)
- **Distribution Analysis**: Box plots and violin plots of performance
- **Statistical Diagrams**: Critical difference diagrams for post-hoc analysis

### 3. Replication Data

- **Raw Results**: Complete CSV with all experimental data
- **Metadata**: Experiment configuration, timestamps, system info
- **Checksums**: Data integrity verification

### 4. Citation Support

- **Algorithm Citations**: BibTeX entries for all 18 implemented algorithms
- **Platform Citation**: BioAlgoCompare reference for methodology section
- **Multiple Formats**: BibTeX, APA, IEEE styles

## Command Line Options

```
bioalgo publish [OPTIONS]

Options:
  -i, --input PATH                Input directory with benchmark results [required]
  -o, --output PATH               Output directory (default: input/publication)
  --format [latex|ieee|acm|springer|all]  Publication format
  --conference TEXT               Target conference/journal
  --include [tables|figures|data|summary|all]  Components to include
  --statistical-tests / --no-statistical-tests  Include statistical tests
  --convergence-plots / --no-convergence-plots  Generate convergence plots
  --distribution-analysis / --no-distribution-analysis  Include distributions
  --replication-data / --no-replication-data  Export replication data
  --compress / --no-compress      Create compressed archive
  -v, --verbose                   Verbose output
```

## Format-Specific Adaptations

### IEEE Format
- Table formatting with `\hline` instead of `\toprule/\midrule`
- Top placement preference `[t]`
- Compact styling

### ACM Format  
- Small font sizing for tables
- Bottom/top placement `[tb]`
- ACM-specific formatting

### Springer Format
- Footnote sizing for tables
- LNCS-compatible formatting
- Minimal placement options

## Conference Packages

Each export creates a conference-specific package including:

1. **Submission Checklist**: Step-by-step guide for including materials
2. **File Manifest**: Complete list of generated files
3. **Requirements Guide**: Format-specific submission requirements
4. **Next Steps**: Actions needed for paper submission

## Integration Examples

### In LaTeX Documents

```latex
% Include descriptive statistics table
\input{table_descriptive_statistics}

% Reference in text
As shown in Table~\ref{tab:descriptive_stats}, the AHA algorithm 
achieved the best performance...

% Include statistical test results
\input{table_statistical_tests}

% Cite algorithms and platform
The experiments used BioAlgoCompare v2.0~\cite{bioalgocompare2025} 
to evaluate the Artificial Hummingbird Algorithm~\cite{aha_2022}.
```

### In Manuscripts

1. **Results Section**: Include descriptive statistics table
2. **Discussion**: Reference statistical significance tests  
3. **Methodology**: Cite BioAlgoCompare platform
4. **Supplementary**: Include replication data as attachment

## File Structure

```
publication_output/
├── table_descriptive_statistics.tex    # Main results table
├── table_statistical_tests.tex         # Statistical analysis
├── table_instance_rankings.tex         # Per-instance rankings
├── convergence_plots/                  # Algorithm convergence
├── distribution_analysis/              # Performance distributions
├── replication_data.csv               # Raw experimental data
├── experiment_metadata.json           # Configuration details
├── citations.bib                      # BibTeX references
├── citations_apa.txt                  # APA format citations
├── citations_ieee.txt                 # IEEE format citations
└── cisti_2025_package/               # Conference-specific package
    └── submission_checklist.md        # Submission guidance
```

## Quality Assurance

### Statistical Rigor
- Non-parametric tests appropriate for algorithm comparison
- Multiple comparison correction (Bonferroni, Holm)
- Effect size calculations (Cliff's Delta, Vargha-Delaney)
- Confidence intervals for all estimates

### Reproducibility
- Complete experimental metadata capture
- Random seed tracking for deterministic results
- System configuration documentation
- Data integrity checksums

### Publication Standards
- IEEE/ACM/Springer formatting compliance
- High-resolution figures (300 DPI)
- Professional LaTeX table formatting
- Complete bibliographic information

## Advanced Usage

### Custom Statistical Tests
```python
from utils.publication_export import PublicationExporter

exporter = PublicationExporter(results_dir, output_dir)
exporter.export_statistical_tables(
    alpha=0.01,  # Custom significance level
    tests=['friedman', 'kruskal'],  # Specific tests
    post_hoc='nemenyi'  # Post-hoc method
)
```

### Batch Processing
```bash
# Process multiple result directories
for dir in results/*/; do
    bioalgo publish -i "$dir" -o "publications/$(basename "$dir")"
done
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install matplotlib seaborn scipy scikit-posthocs
   ```

2. **Empty Results**
   - Ensure input directory contains JSON result files
   - Check that results follow StandardResultV2 schema

3. **LaTeX Compilation Errors**
   - Tables require `booktabs` package: `\usepackage{booktabs}`
   - Figures require `graphicx` package: `\usepackage{graphicx}`

### Performance Optimization

- Use `--include tables` for fastest export
- Use `--no-convergence-plots` to skip figure generation
- Use `--compress` only for final submission packages

## Citation

When using the publication export system, please cite:

```bibtex
@inproceedings{bioalgocompare2025,
  title = {BioAlgoCompare: A Comprehensive Platform for Rigorous Statistical Evaluation of Bio-Inspired Algorithms},
  author = {Anonymous},
  year = {2025},
  booktitle = {CISTI 2025},
  note = {Submitted for review}
}
```

## Support

For issues or feature requests:
- Check the troubleshooting section above
- Review the generated `submission_checklist.md` 
- Consult the main BioAlgoCompare documentation