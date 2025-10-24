# Literature Review Workflow Module

Complete system for conducting integrative literature reviews with systematic screening, unbiased data extraction, AI-assisted thematic synthesis, and automated quality assurance.

## Features

- **Multi-stage screening**: Title/abstract → Full-text → Quality assessment
- **Parallel independent review**: Built-in inter-rater reliability tracking
- **Domain-agnostic extraction templates**: Unbiased YAML-driven forms
- **AI-assisted thematic synthesis**: Optional AI theme suggestions with researcher control
- **Automated quality assurance**: Cohen's kappa calculation, quality flags
- **Publication-ready outputs**: PRISMA diagrams, evidence tables, theme visualizations

## Installation

```bash
cd academic-helpers/literature-review
pip install -r requirements.txt
```

**Requirements:**
- Python 3.10+
- Paper Reader Module (see `academic-helpers/paper-reader/`)

**Dependencies:**
```
pyyaml
sentence-transformers  # Optional: for AI theme suggestions
scikit-learn          # Optional: for clustering and kappa
pandas
matplotlib
networkx
click
pytest
```

## Quick Start

### 1. Create a Review Project

```bash
python cli/create_review.py \
  --name "Food Environment Review" \
  --question "What is the impact of food deserts on health outcomes?" \
  --reviewers "reviewer_A,reviewer_B" \
  --ai
```

### 2. Import Papers

```bash
python cli/import_papers.py \
  --review-id 1 \
  --pdf-dir path/to/pdfs
```

### 3. Screen Papers

```bash
python cli/run_screening.py \
  --review-id 1 \
  --reviewer-id reviewer_A \
  --stage title_abstract
```

### 4. Extract Data

```bash
python cli/run_extraction.py \
  --review-id 1 \
  --reviewer-id reviewer_A
```

### 5. Generate Outputs

```bash
python cli/generate_outputs.py --review-id 1
```

## Database Schema

Review-specific tables extend Paper Reader's central paper library:

- `reviews` - Review project metadata
- `review_papers` - Links papers to reviews
- `paper_screening` - Screening decisions (title/abstract, full-text, quality)
- `paper_extraction` - Extracted data from papers
- `themes` - Thematic synthesis themes
- `theme_coding` - Paper-to-theme assignments
- `reliability_metrics` - Cached inter-rater reliability scores

## Extraction Templates

Domain-agnostic YAML templates for unbiased data extraction:

- `observational_study.yaml` - Cross-sectional, cohort, case-control, longitudinal
- `spatial_analysis.yaml` - GIS, spatial statistics, geographic data
- `qualitative_study.yaml` - Interviews, focus groups, ethnography
- `mixed_methods.yaml` - Combined quantitative and qualitative
- `intervention_study.yaml` - RCTs, quasi-experiments
- `systematic_review.yaml` - Meta-analyses, systematic reviews

## Testing

```bash
# Unit tests
pytest tests/

# Integration test
pytest tests/integration/test_complete_workflow.py -v

# With coverage
pytest --cov=. --cov-report=html
```

## Architecture

**Review Project Model**: Database-centric state management with review-specific tables referencing Paper Reader's central library. One paper can be screened/coded differently in multiple reviews.

**Integration**: Extends `academic-helpers/paper-reader/` database with review-specific tables. Paper Reader handles PDF parsing, metadata extraction, citation validation. Literature Review adds screening, extraction, synthesis layers.

## License

MIT

## Citation

If you use this module in your research, please cite:

```
[Citation details]
```
