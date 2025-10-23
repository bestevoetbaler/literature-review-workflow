# Literature Review Workflow Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete literature review workflow system for integrative reviews with systematic screening, unbiased data extraction, AI-assisted thematic synthesis, and automated quality assurance.

**Architecture:** Review Project Model - database-centric state management extending Paper Reader's central paper library with review-specific tables. Multi-stage screening (title/abstract → full-text → quality), YAML-driven extraction templates, hybrid AI + manual thematic synthesis, automated inter-rater reliability tracking.

**Tech Stack:** Python 3.10+, SQLite with FTS5, PyYAML, sentence-transformers, scikit-learn, pandas, matplotlib, networkx, click (CLI), pytest

---

## Prerequisites

**Required:** Paper Reader Module must be implemented first (see `docs/plans/2025-01-24-paper-reader-design.md`)

**Dependencies to install:**
```bash
pip install pyyaml sentence-transformers scikit-learn pandas matplotlib networkx click pytest
```

---

## Task 1: Database Schema Foundation

**Files:**
- Create: `academic-helpers/literature-review/database/schema.sql`
- Create: `academic-helpers/literature-review/database/__init__.py`
- Create: `academic-helpers/literature-review/database/connection.py`
- Test: `academic-helpers/literature-review/tests/database/test_schema.py`

**Step 1: Write the failing test**

```python
# tests/database/test_schema.py
import pytest
import sqlite3
from database.connection import get_database_connection

def test_reviews_table_exists():
    """Test that reviews table is created."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='reviews'
    """)

    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 'reviews'

    conn.close()

def test_reviews_table_structure():
    """Test reviews table has required columns."""
    conn = get_database_connection(':memory:')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(reviews)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    assert 'review_id' in columns
    assert 'review_name' in columns
    assert 'research_question' in columns
    assert 'inclusion_criteria_json' in columns
    assert columns['review_id'] == 'INTEGER'

    conn.close()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/database/test_schema.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'database'"

**Step 3: Create database connection module**

```python
# database/__init__.py
"""Literature review database package."""
from .connection import get_database_connection

__all__ = ['get_database_connection']
```

```python
# database/connection.py
"""Database connection management."""
import sqlite3
import os

def get_database_connection(db_path=None):
    """
    Get database connection with schema initialized.

    Args:
        db_path: Path to database file. If None, uses default.
                 Use ':memory:' for in-memory database.

    Returns:
        sqlite3.Connection
    """
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'literature_review.db'
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name

    # Initialize schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())

    return conn
```

**Step 4: Create database schema**

```sql
-- database/schema.sql
-- Literature Review Database Schema

-- Main review projects
CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_name TEXT NOT NULL,
    research_question TEXT NOT NULL,
    inclusion_criteria_json TEXT NOT NULL,
    search_strategy TEXT,
    reviewers_json TEXT NOT NULL,
    use_ai_suggestions BOOLEAN DEFAULT 1,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('active','completed','archived')) DEFAULT 'active'
);

-- Link papers from central library to reviews
CREATE TABLE IF NOT EXISTS review_papers (
    review_id INTEGER NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    paper_id TEXT NOT NULL,  -- References papers.paper_id from paper reader
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, paper_id)
);

-- Screening decisions at each stage
CREATE TABLE IF NOT EXISTS paper_screening (
    screening_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    paper_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    stage TEXT CHECK(stage IN ('title_abstract','full_text','quality')) NOT NULL,
    decision TEXT CHECK(decision IN ('include','exclude','maybe')) NOT NULL,
    rationale TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(review_id, paper_id, reviewer_id, stage)
);

-- Screening conflicts requiring resolution
CREATE TABLE IF NOT EXISTS screening_conflicts (
    conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    paper_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    resolved BOOLEAN DEFAULT 0,
    final_decision TEXT CHECK(final_decision IN ('include','exclude')),
    resolution_notes TEXT,
    resolution_date TIMESTAMP,
    FOREIGN KEY (review_id, paper_id) REFERENCES review_papers(review_id, paper_id)
);

-- Extracted data from papers
CREATE TABLE IF NOT EXISTS paper_extraction (
    extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    paper_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    template_name TEXT NOT NULL,
    extracted_data_json TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(review_id, paper_id, reviewer_id)
);

-- Extraction field-level conflicts
CREATE TABLE IF NOT EXISTS extraction_conflicts (
    conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    paper_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    reviewer1_id TEXT NOT NULL,
    reviewer1_value TEXT,
    reviewer2_id TEXT NOT NULL,
    reviewer2_value TEXT,
    resolved BOOLEAN DEFAULT 0,
    final_value TEXT,
    resolution_notes TEXT,
    resolution_date TIMESTAMP
);

-- Thematic synthesis
CREATE TABLE IF NOT EXISTS themes (
    theme_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    theme_name TEXT NOT NULL,
    theme_description TEXT,
    parent_theme_id INTEGER REFERENCES themes(theme_id),
    created_by TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coding papers to themes
CREATE TABLE IF NOT EXISTS theme_coding (
    coding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id INTEGER NOT NULL REFERENCES themes(theme_id) ON DELETE CASCADE,
    paper_id TEXT NOT NULL,
    field_name TEXT,
    quote TEXT,
    page_number INTEGER,
    coder_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships between themes
CREATE TABLE IF NOT EXISTS theme_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    theme1_id INTEGER NOT NULL REFERENCES themes(theme_id),
    theme2_id INTEGER NOT NULL REFERENCES themes(theme_id),
    relationship_type TEXT CHECK(relationship_type IN ('supports','contradicts','modifies','contextualizes')),
    notes TEXT,
    CHECK(theme1_id < theme2_id)
);

-- Reliability metrics cache
CREATE TABLE IF NOT EXISTS reliability_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL REFERENCES reviews(review_id),
    metric_type TEXT CHECK(metric_type IN ('screening_kappa','extraction_agreement','coding_kappa')) NOT NULL,
    stage TEXT,
    field_name TEXT,
    value REAL NOT NULL,
    interpretation TEXT,
    calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality assurance view
CREATE VIEW IF NOT EXISTS reliability_summary AS
SELECT
    r.review_id,
    r.review_name,
    COUNT(DISTINCT CASE WHEN ps.stage = 'title_abstract' THEN ps.paper_id END) as papers_title_screened,
    COUNT(DISTINCT CASE WHEN ps.stage = 'full_text' THEN ps.paper_id END) as papers_fulltext_screened,
    COUNT(DISTINCT pe.paper_id) as papers_extracted,
    COUNT(DISTINCT t.theme_id) as themes_created,
    COUNT(DISTINCT tc.paper_id) as papers_coded
FROM reviews r
LEFT JOIN paper_screening ps ON r.review_id = ps.review_id
LEFT JOIN paper_extraction pe ON r.review_id = pe.review_id
LEFT JOIN themes t ON r.review_id = t.review_id
LEFT JOIN theme_coding tc ON t.theme_id = tc.theme_id
GROUP BY r.review_id;
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/database/test_schema.py -v`
Expected: PASS (all tests pass)

**Step 6: Commit**

```bash
git add database/schema.sql database/__init__.py database/connection.py tests/database/test_schema.py
git commit -m "feat(database): add literature review database schema"
```

---

## Task 2: Database Query Layer

**Files:**
- Create: `academic-helpers/literature-review/database/queries.py`
- Test: `academic-helpers/literature-review/tests/database/test_queries.py`

**Step 1: Write the failing test**

```python
# tests/database/test_queries.py
import pytest
import json
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database for testing."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

def test_create_review(db):
    """Test creating a new review."""
    review_id = db.create_review(
        review_name='Test Review',
        research_question='What is the impact?',
        inclusion_criteria_json=json.dumps({'criteria': 'test'}),
        reviewers_json=json.dumps(['reviewer_A', 'reviewer_B'])
    )

    assert review_id is not None
    assert isinstance(review_id, int)

def test_get_review(db):
    """Test retrieving a review."""
    review_id = db.create_review(
        review_name='Test Review',
        research_question='What is the impact?',
        inclusion_criteria_json=json.dumps({'criteria': 'test'}),
        reviewers_json=json.dumps(['reviewer_A'])
    )

    review = db.get_review(review_id)

    assert review is not None
    assert review['review_name'] == 'Test Review'
    assert review['research_question'] == 'What is the impact?'

def test_link_paper_to_review(db):
    """Test linking a paper to a review."""
    review_id = db.create_review(
        review_name='Test',
        research_question='Question?',
        inclusion_criteria_json='{}',
        reviewers_json='[]'
    )

    db.link_paper_to_review(review_id, 'paper_001')

    papers = db.get_review_papers(review_id)
    assert len(papers) == 1
    assert papers[0] == 'paper_001'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/database/test_queries.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'database.queries'"

**Step 3: Implement database query layer**

```python
# database/queries.py
"""Database query layer for literature review."""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

class ReviewDatabase:
    """Database operations for literature reviews."""

    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize with database connection.

        Args:
            connection: SQLite connection
        """
        self.conn = connection

    def create_review(
        self,
        review_name: str,
        research_question: str,
        inclusion_criteria_json: str,
        reviewers_json: str,
        search_strategy: Optional[str] = None,
        use_ai_suggestions: bool = True
    ) -> int:
        """
        Create a new review project.

        Returns:
            review_id of created review
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (
                review_name,
                research_question,
                inclusion_criteria_json,
                reviewers_json,
                search_strategy,
                use_ai_suggestions
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            review_name,
            research_question,
            inclusion_criteria_json,
            reviewers_json,
            search_strategy,
            use_ai_suggestions
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_review(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get review by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reviews WHERE review_id = ?
        """, (review_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        return dict(row)

    def link_paper_to_review(self, review_id: int, paper_id: str) -> None:
        """Link a paper from central library to this review."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO review_papers (review_id, paper_id)
            VALUES (?, ?)
        """, (review_id, paper_id))
        self.conn.commit()

    def get_review_papers(self, review_id: int) -> List[str]:
        """Get all paper IDs linked to this review."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT paper_id FROM review_papers
            WHERE review_id = ?
            ORDER BY date_added
        """, (review_id,))

        return [row[0] for row in cursor.fetchall()]

    def insert_screening(
        self,
        review_id: int,
        paper_id: str,
        reviewer_id: str,
        stage: str,
        decision: str,
        rationale: Optional[str] = None
    ) -> int:
        """Record a screening decision."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO paper_screening (
                review_id,
                paper_id,
                reviewer_id,
                stage,
                decision,
                rationale
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (review_id, paper_id, reviewer_id, stage, decision, rationale))
        self.conn.commit()
        return cursor.lastrowid

    def get_screening_decisions(
        self,
        review_id: int,
        paper_id: str,
        stage: str
    ) -> List[Dict[str, Any]]:
        """Get all screening decisions for a paper at a stage."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM paper_screening
            WHERE review_id = ? AND paper_id = ? AND stage = ?
            ORDER BY timestamp
        """, (review_id, paper_id, stage))

        return [dict(row) for row in cursor.fetchall()]

    def insert_extraction(
        self,
        review_id: int,
        paper_id: str,
        reviewer_id: str,
        template_name: str,
        extracted_data_json: str
    ) -> int:
        """Save extraction data."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO paper_extraction (
                review_id,
                paper_id,
                reviewer_id,
                template_name,
                extracted_data_json
            ) VALUES (?, ?, ?, ?, ?)
        """, (review_id, paper_id, reviewer_id, template_name, extracted_data_json))
        self.conn.commit()
        return cursor.lastrowid

    def get_extractions(
        self,
        review_id: int,
        paper_id: str
    ) -> List[Dict[str, Any]]:
        """Get all extractions for a paper."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM paper_extraction
            WHERE review_id = ? AND paper_id = ?
            ORDER BY timestamp
        """, (review_id, paper_id))

        return [dict(row) for row in cursor.fetchall()]

    def insert_theme(
        self,
        review_id: int,
        theme_name: str,
        created_by: str,
        theme_description: Optional[str] = None,
        parent_theme_id: Optional[int] = None
    ) -> int:
        """Create a new theme."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO themes (
                review_id,
                theme_name,
                theme_description,
                parent_theme_id,
                created_by
            ) VALUES (?, ?, ?, ?, ?)
        """, (review_id, theme_name, theme_description, parent_theme_id, created_by))
        self.conn.commit()
        return cursor.lastrowid

    def get_themes(self, review_id: int) -> List[Dict[str, Any]]:
        """Get all themes for a review."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM themes
            WHERE review_id = ?
            ORDER BY timestamp
        """, (review_id,))

        return [dict(row) for row in cursor.fetchall()]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/database/test_queries.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add database/queries.py tests/database/test_queries.py
git commit -m "feat(database): add query layer for reviews, screening, extraction, themes"
```

---

## Task 3: YAML Extraction Templates

**Files:**
- Create: `academic-helpers/literature-review/templates/observational_study.yaml`
- Create: `academic-helpers/literature-review/templates/spatial_analysis.yaml`
- Create: `academic-helpers/literature-review/templates/qualitative_study.yaml`
- Create: `academic-helpers/literature-review/extraction/__init__.py`
- Create: `academic-helpers/literature-review/extraction/template_loader.py`
- Test: `academic-helpers/literature-review/tests/extraction/test_template_loader.py`

**Step 1: Write the failing test**

```python
# tests/extraction/test_template_loader.py
import pytest
from extraction.template_loader import TemplateLoader

def test_load_observational_template():
    """Test loading observational study template."""
    loader = TemplateLoader()
    template = loader.load_template('observational_study')

    assert template is not None
    assert template['name'] == 'Observational Study'
    assert 'fields' in template
    assert 'study_design' in template['fields']

def test_template_field_structure():
    """Test template field has required attributes."""
    loader = TemplateLoader()
    template = loader.load_template('observational_study')

    study_design = template['fields']['study_design']

    assert 'type' in study_design
    assert 'prompt' in study_design
    assert study_design['type'] == 'select'
    assert 'options' in study_design

def test_list_templates():
    """Test listing all available templates."""
    loader = TemplateLoader()
    templates = loader.list_templates()

    assert 'observational_study' in templates
    assert 'spatial_analysis' in templates
    assert 'qualitative_study' in templates
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/extraction/test_template_loader.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'extraction'"

**Step 3: Create observational study template**

```yaml
# templates/observational_study.yaml
name: "Observational Study"
description: "For cross-sectional, cohort, case-control, longitudinal, or ecological studies"

fields:
  study_design:
    type: select
    options: [cross_sectional, cohort, case_control, longitudinal, ecological]
    required: true
    prompt: "Study design (select one)"

  sample_size:
    type: integer
    required: true
    prompt: "Total sample size (n)"

  population_description:
    type: text
    prompt: "Population characteristics (copy from Methods)"
    instruction: "Describe exactly as authors defined (age, location, inclusion criteria)"

  exposure_variables:
    type: text_array
    prompt: "Independent variables / predictors (exactly as named by authors)"
    instruction: "List each exposure without interpretation. Use authors' exact terminology."

  outcome_variables:
    type: text_array
    prompt: "Dependent variables / outcomes (exactly as named by authors)"
    instruction: "List each outcome without interpretation. Use authors' exact terminology."

  covariates:
    type: text_array
    prompt: "Control variables / confounders adjusted for"
    instruction: "List as authors specified in their statistical models"

  statistical_methods:
    type: text
    prompt: "Statistical analysis methods (copy from Methods)"
    instruction: "Quote or paraphrase statistical approach exactly"

  main_results:
    type: text_array
    prompt: "Key findings (copy exact wording when possible)"
    instruction: "Extract verbatim from Results section. Include effect sizes, p-values, confidence intervals as reported."

  null_findings:
    type: text_array
    prompt: "Non-significant or unexpected results (if any)"
    instruction: "Include findings that did NOT reach statistical significance"

  authors_interpretation:
    type: text
    prompt: "Authors' interpretation of findings (from Discussion)"
    instruction: "Summarize how authors explained their results"

  limitations:
    type: text_array
    prompt: "Study limitations (as acknowledged by authors)"
    instruction: "List limitations authors mentioned in Discussion"

  quality_score:
    type: integer
    min: 0
    max: 10
    prompt: "Quality assessment score (0-10)"
    instruction: "Based on review's quality criteria"
```

**Step 4: Create spatial analysis template**

```yaml
# templates/spatial_analysis.yaml
name: "Spatial Analysis Study"
description: "For studies using GIS, spatial statistics, or geographic data"

fields:
  spatial_scale:
    type: select
    options: [individual, household, neighborhood, city, region, national, global]
    required: true
    prompt: "Geographic scale of analysis"

  geographic_area:
    type: text
    required: true
    prompt: "Study area (location and boundaries)"
    instruction: "Describe exactly as defined by authors"

  spatial_unit:
    type: text
    required: true
    prompt: "Unit of analysis (e.g., census tract, grid cell, individual address)"

  sample_size_spatial:
    type: integer
    prompt: "Number of spatial units analyzed"

  spatial_data_sources:
    type: text_array
    prompt: "Data sources (list all datasets used)"
    instruction: "Include dataset names, years, and providers as cited"

  exposure_variables:
    type: text_array
    prompt: "Spatial predictors / exposures (exactly as named)"
    instruction: "List geographic variables without interpretation"

  outcome_variables:
    type: text_array
    prompt: "Outcomes measured (exactly as named)"
    instruction: "List outcomes without interpretation"

  spatial_methods:
    type: text_array
    prompt: "Spatial analysis methods (copy from Methods)"
    instruction: "e.g., 'Moran's I', 'kernel density estimation', 'geographically weighted regression'"

  main_results:
    type: text_array
    prompt: "Key spatial findings (copy exact wording)"
    instruction: "Include spatial autocorrelation statistics, clustering patterns, spatial associations"

  null_findings:
    type: text_array
    prompt: "Non-significant spatial patterns (if any)"

  authors_interpretation:
    type: text
    prompt: "Authors' spatial interpretation (from Discussion)"

  limitations:
    type: text_array
    prompt: "Spatial limitations (e.g., MAUP, edge effects, data resolution)"
```

**Step 5: Create qualitative study template**

```yaml
# templates/qualitative_study.yaml
name: "Qualitative Study"
description: "For interviews, focus groups, ethnography, grounded theory, phenomenology"

fields:
  qualitative_approach:
    type: select
    options: [grounded_theory, phenomenology, ethnography, case_study, narrative_analysis, thematic_analysis, discourse_analysis]
    required: true
    prompt: "Qualitative methodology"

  sample_size:
    type: integer
    prompt: "Number of participants"

  sampling_strategy:
    type: text
    prompt: "Sampling approach (copy from Methods)"
    instruction: "e.g., 'purposive sampling', 'snowball sampling', 'theoretical sampling'"

  participant_characteristics:
    type: text
    prompt: "Participant demographics (as described by authors)"

  data_collection:
    type: text_array
    prompt: "Data collection methods (copy from Methods)"
    instruction: "e.g., 'semi-structured interviews', 'focus groups', 'participant observation'"

  interview_topics:
    type: text_array
    prompt: "Interview guide topics / questions (if provided)"
    instruction: "List main topic areas without interpretation"

  analysis_method:
    type: text
    prompt: "Analysis approach (copy from Methods)"
    instruction: "Describe coding process, software used, validation approach"

  main_themes:
    type: text_array
    prompt: "Major themes identified (exactly as named by authors)"
    instruction: "Use authors' theme names verbatim"

  subthemes:
    type: text_array
    prompt: "Sub-themes or categories (if reported)"

  representative_quotes:
    type: text_array
    prompt: "Exemplar quotes (copy from Results)"
    instruction: "Include 2-3 representative quotes for key themes"

  authors_interpretation:
    type: text
    prompt: "Authors' theoretical interpretation (from Discussion)"

  reflexivity:
    type: text
    prompt: "Authors' reflexivity statement (if provided)"
    instruction: "Note researcher positionality, bias mitigation"

  limitations:
    type: text_array
    prompt: "Study limitations (as acknowledged by authors)"
```

**Step 6: Create template loader**

```python
# extraction/__init__.py
"""Data extraction package."""
from .template_loader import TemplateLoader

__all__ = ['TemplateLoader']
```

```python
# extraction/template_loader.py
"""YAML template loader for data extraction."""
import os
import yaml
from typing import Dict, List, Any

class TemplateLoader:
    """Load and manage extraction templates."""

    def __init__(self, templates_dir: str = None):
        """
        Initialize template loader.

        Args:
            templates_dir: Path to templates directory.
                          If None, uses default templates/ directory.
        """
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(__file__),
                '..',
                'templates'
            )

        self.templates_dir = templates_dir
        self._templates_cache = {}

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load a template by name.

        Args:
            template_name: Template name without .yaml extension

        Returns:
            Template dictionary

        Raises:
            FileNotFoundError: If template does not exist
        """
        # Check cache first
        if template_name in self._templates_cache:
            return self._templates_cache[template_name]

        # Load from file
        template_path = os.path.join(
            self.templates_dir,
            f'{template_name}.yaml'
        )

        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Template '{template_name}' not found at {template_path}"
            )

        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)

        # Cache and return
        self._templates_cache[template_name] = template
        return template

    def list_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            List of template names (without .yaml extension)
        """
        if not os.path.exists(self.templates_dir):
            return []

        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.yaml'):
                templates.append(filename[:-5])  # Remove .yaml extension

        return sorted(templates)

    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate template structure.

        Args:
            template: Template dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if 'name' not in template:
            errors.append("Template missing 'name' field")

        if 'fields' not in template:
            errors.append("Template missing 'fields' field")
            return errors  # Can't validate further

        for field_name, field_config in template['fields'].items():
            if 'type' not in field_config:
                errors.append(f"Field '{field_name}' missing 'type'")

            if 'prompt' not in field_config:
                errors.append(f"Field '{field_name}' missing 'prompt'")

            field_type = field_config.get('type')
            if field_type == 'select' and 'options' not in field_config:
                errors.append(f"Field '{field_name}' type 'select' requires 'options'")

        return errors
```

**Step 7: Run test to verify it passes**

Run: `pytest tests/extraction/test_template_loader.py -v`
Expected: PASS (all tests pass)

**Step 8: Commit**

```bash
git add templates/ extraction/ tests/extraction/test_template_loader.py
git commit -m "feat(extraction): add YAML templates and loader for observational, spatial, qualitative studies"
```

---

## Task 4: Screening Interface

**Files:**
- Create: `academic-helpers/literature-review/screening/__init__.py`
- Create: `academic-helpers/literature-review/screening/interface.py`
- Test: `academic-helpers/literature-review/tests/screening/test_interface.py`

**Step 1: Write the failing test**

```python
# tests/screening/test_interface.py
import pytest
from screening.interface import ScreeningInterface
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

@pytest.fixture
def screener(db):
    """Create screening interface."""
    return ScreeningInterface(db)

def test_record_decision_include(screener, db):
    """Test recording include decision."""
    review_id = db.create_review(
        'Test Review',
        'Question?',
        '{}',
        '[]'
    )

    screener.record_decision(
        review_id=review_id,
        paper_id='paper_001',
        reviewer_id='reviewer_A',
        stage='title_abstract',
        decision='include'
    )

    decisions = db.get_screening_decisions(review_id, 'paper_001', 'title_abstract')
    assert len(decisions) == 1
    assert decisions[0]['decision'] == 'include'

def test_record_exclude_without_rationale_fails(screener, db):
    """Test that exclude decisions require rationale."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    with pytest.raises(ValueError, match="rationale"):
        screener.record_decision(
            review_id=review_id,
            paper_id='paper_001',
            reviewer_id='reviewer_A',
            stage='title_abstract',
            decision='exclude',
            rationale=None
        )

def test_record_exclude_with_rationale_succeeds(screener, db):
    """Test exclude with rationale works."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    screener.record_decision(
        review_id=review_id,
        paper_id='paper_001',
        reviewer_id='reviewer_A',
        stage='title_abstract',
        decision='exclude',
        rationale='Not in scope'
    )

    decisions = db.get_screening_decisions(review_id, 'paper_001', 'title_abstract')
    assert decisions[0]['rationale'] == 'Not in scope'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/screening/test_interface.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'screening'"

**Step 3: Implement screening interface**

```python
# screening/__init__.py
"""Screening workflow package."""
from .interface import ScreeningInterface

__all__ = ['ScreeningInterface']
```

```python
# screening/interface.py
"""Screening interface for literature review."""
from typing import Optional, Dict, Any
from database.queries import ReviewDatabase

class ScreeningInterface:
    """Interface for paper screening workflow."""

    def __init__(self, review_db: ReviewDatabase):
        """
        Initialize screening interface.

        Args:
            review_db: ReviewDatabase instance
        """
        self.review_db = review_db

    def record_decision(
        self,
        review_id: int,
        paper_id: str,
        reviewer_id: str,
        stage: str,
        decision: str,
        rationale: Optional[str] = None
    ) -> int:
        """
        Record a screening decision.

        Args:
            review_id: Review ID
            paper_id: Paper ID
            reviewer_id: Reviewer ID
            stage: Screening stage ('title_abstract', 'full_text', 'quality')
            decision: Decision ('include', 'exclude', 'maybe')
            rationale: Rationale for decision (required for 'exclude')

        Returns:
            screening_id

        Raises:
            ValueError: If exclude decision lacks rationale
        """
        # Validate exclude decisions have rationale
        if decision == 'exclude' and not rationale:
            raise ValueError(
                "Exclude decisions require rationale referencing inclusion criteria"
            )

        # Record decision
        screening_id = self.review_db.insert_screening(
            review_id=review_id,
            paper_id=paper_id,
            reviewer_id=reviewer_id,
            stage=stage,
            decision=decision,
            rationale=rationale
        )

        return screening_id

    def get_papers_needing_screening(
        self,
        review_id: int,
        reviewer_id: str,
        stage: str
    ) -> list:
        """
        Get papers that need screening by this reviewer at this stage.

        Args:
            review_id: Review ID
            reviewer_id: Reviewer ID
            stage: Screening stage

        Returns:
            List of paper IDs needing screening
        """
        # Get all papers in review
        all_papers = self.review_db.get_review_papers(review_id)

        # Filter to papers not yet screened by this reviewer
        needing_screening = []
        for paper_id in all_papers:
            decisions = self.review_db.get_screening_decisions(
                review_id,
                paper_id,
                stage
            )

            # Check if this reviewer has already screened
            reviewer_screened = any(
                d['reviewer_id'] == reviewer_id
                for d in decisions
            )

            if not reviewer_screened:
                needing_screening.append(paper_id)

        return needing_screening
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/screening/test_interface.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add screening/ tests/screening/test_interface.py
git commit -m "feat(screening): add screening interface with decision validation"
```

---

## Task 5: Inter-Rater Reliability Calculator

**Files:**
- Create: `academic-helpers/literature-review/quality/__init__.py`
- Create: `academic-helpers/literature-review/quality/reliability.py`
- Test: `academic-helpers/literature-review/tests/quality/test_reliability.py`

**Step 1: Write the failing test**

```python
# tests/quality/test_reliability.py
import pytest
from quality.reliability import ReliabilityCalculator
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

@pytest.fixture
def calculator(db):
    """Create reliability calculator."""
    return ReliabilityCalculator(db)

def test_calculate_kappa_perfect_agreement(calculator, db):
    """Test kappa calculation with perfect agreement."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')
    db.link_paper_to_review(review_id, 'paper_001')
    db.link_paper_to_review(review_id, 'paper_002')

    # Both reviewers agree on both papers
    db.insert_screening(review_id, 'paper_001', 'reviewer_A', 'title_abstract', 'include')
    db.insert_screening(review_id, 'paper_001', 'reviewer_B', 'title_abstract', 'include')
    db.insert_screening(review_id, 'paper_002', 'reviewer_A', 'title_abstract', 'exclude', 'Out of scope')
    db.insert_screening(review_id, 'paper_002', 'reviewer_B', 'title_abstract', 'exclude', 'Out of scope')

    result = calculator.calculate_screening_kappa(review_id, 'title_abstract')

    assert result['kappa'] == 1.0
    assert result['interpretation'] == 'Almost Perfect'
    assert result['percent_agreement'] == 100.0

def test_calculate_kappa_no_agreement(calculator, db):
    """Test kappa with complete disagreement."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')
    db.link_paper_to_review(review_id, 'paper_001')
    db.link_paper_to_review(review_id, 'paper_002')

    # Reviewers disagree on both papers
    db.insert_screening(review_id, 'paper_001', 'reviewer_A', 'title_abstract', 'include')
    db.insert_screening(review_id, 'paper_001', 'reviewer_B', 'title_abstract', 'exclude', 'Bad')
    db.insert_screening(review_id, 'paper_002', 'reviewer_A', 'title_abstract', 'exclude', 'Bad')
    db.insert_screening(review_id, 'paper_002', 'reviewer_B', 'title_abstract', 'include')

    result = calculator.calculate_screening_kappa(review_id, 'title_abstract')

    assert result['kappa'] < 0.2
    assert result['percent_agreement'] == 0.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/quality/test_reliability.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quality'"

**Step 3: Implement reliability calculator**

```python
# quality/__init__.py
"""Quality assurance package."""
from .reliability import ReliabilityCalculator

__all__ = ['ReliabilityCalculator']
```

```python
# quality/reliability.py
"""Inter-rater reliability calculation."""
from typing import Dict, List, Any
from database.queries import ReviewDatabase

try:
    from sklearn.metrics import cohen_kappa_score
except ImportError:
    cohen_kappa_score = None

class ReliabilityCalculator:
    """Calculate inter-rater reliability metrics."""

    def __init__(self, review_db: ReviewDatabase):
        """
        Initialize reliability calculator.

        Args:
            review_db: ReviewDatabase instance
        """
        self.review_db = review_db

    def calculate_screening_kappa(
        self,
        review_id: int,
        stage: str
    ) -> Dict[str, Any]:
        """
        Calculate Cohen's kappa for screening decisions.

        Args:
            review_id: Review ID
            stage: Screening stage

        Returns:
            Dictionary with kappa, interpretation, agreements
        """
        if cohen_kappa_score is None:
            raise ImportError("scikit-learn required for kappa calculation")

        # Get all papers in review
        papers = self.review_db.get_review_papers(review_id)

        # Find papers screened by exactly 2 reviewers
        agreements = []
        for paper_id in papers:
            decisions = self.review_db.get_screening_decisions(
                review_id,
                paper_id,
                stage
            )

            if len(decisions) == 2:
                agreements.append({
                    'paper_id': paper_id,
                    'reviewer1': decisions[0]['reviewer_id'],
                    'reviewer2': decisions[1]['reviewer_id'],
                    'decision1': decisions[0]['decision'],
                    'decision2': decisions[1]['decision'],
                    'agree': decisions[0]['decision'] == decisions[1]['decision']
                })

        if not agreements:
            return {'error': 'No dual-screened papers found'}

        # Calculate Cohen's kappa
        labels1 = [a['decision1'] for a in agreements]
        labels2 = [a['decision2'] for a in agreements]
        kappa = cohen_kappa_score(labels1, labels2)

        # Interpret (Landis & Koch)
        if kappa < 0:
            interpretation = 'Poor'
        elif kappa < 0.20:
            interpretation = 'Slight'
        elif kappa < 0.40:
            interpretation = 'Fair'
        elif kappa < 0.60:
            interpretation = 'Moderate'
        elif kappa < 0.80:
            interpretation = 'Substantial'
        else:
            interpretation = 'Almost Perfect'

        # Calculate percent agreement
        agree_count = sum(a['agree'] for a in agreements)
        percent_agreement = (agree_count / len(agreements)) * 100

        return {
            'kappa': kappa,
            'interpretation': interpretation,
            'total_papers': len(agreements),
            'agreements': agree_count,
            'percent_agreement': percent_agreement,
            'disagreements': [a for a in agreements if not a['agree']]
        }

    def _interpret_kappa(self, kappa: float) -> str:
        """Interpret kappa value using Landis & Koch scale."""
        if kappa < 0:
            return 'Poor'
        elif kappa < 0.20:
            return 'Slight'
        elif kappa < 0.40:
            return 'Fair'
        elif kappa < 0.60:
            return 'Moderate'
        elif kappa < 0.80:
            return 'Substantial'
        else:
            return 'Almost Perfect'
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/quality/test_reliability.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add quality/ tests/quality/test_reliability.py
git commit -m "feat(quality): add Cohen's kappa calculator for screening reliability"
```

---

## Task 6: Thematic Synthesis (AI-Assisted)

**Files:**
- Create: `academic-helpers/literature-review/synthesis/__init__.py`
- Create: `academic-helpers/literature-review/synthesis/thematic_analyzer.py`
- Test: `academic-helpers/literature-review/tests/synthesis/test_thematic_analyzer.py`

**Step 1: Write the failing test**

```python
# tests/synthesis/test_thematic_analyzer.py
import pytest
import json
from synthesis.thematic_analyzer import ThematicSynthesizer
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

@pytest.fixture
def synthesizer(db):
    """Create thematic synthesizer."""
    return ThematicSynthesizer(db, use_ai=False)  # Disable AI for unit tests

def test_suggest_themes_manual_mode(synthesizer, db):
    """Test theme suggestion in manual mode."""
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    # Add some extractions
    db.insert_extraction(
        review_id, 'paper_001', 'reviewer_A', 'observational_study',
        json.dumps({'main_results': ['Food deserts limit access']})
    )

    result = synthesizer.suggest_themes(review_id, field_name='main_results')

    assert result['mode'] == 'manual'
    assert 'extractions' in result

@pytest.mark.skipif(
    not ThematicSynthesizer._check_ai_dependencies(),
    reason="AI dependencies not available"
)
def test_suggest_themes_ai_mode(db):
    """Test AI theme suggestion."""
    synthesizer = ThematicSynthesizer(db, use_ai=True)
    review_id = db.create_review('Test', 'Q?', '{}', '[]')

    # Add similar extractions
    db.insert_extraction(
        review_id, 'paper_001', 'reviewer_A', 'observational_study',
        json.dumps({'main_results': ['Food deserts limit access', 'Transportation barriers']})
    )
    db.insert_extraction(
        review_id, 'paper_002', 'reviewer_A', 'observational_study',
        json.dumps({'main_results': ['Distance to stores', 'Car ownership low']})
    )

    result = synthesizer.suggest_themes(review_id, field_name='main_results')

    assert result['mode'] == 'ai'
    assert 'themes' in result
    assert len(result['themes']) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/synthesis/test_thematic_analyzer.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'synthesis'"

**Step 3: Implement thematic synthesizer**

```python
# synthesis/__init__.py
"""Thematic synthesis package."""
from .thematic_analyzer import ThematicSynthesizer

__all__ = ['ThematicSynthesizer']
```

```python
# synthesis/thematic_analyzer.py
"""AI-assisted thematic synthesis."""
import json
from typing import Dict, List, Any, Optional
from collections import Counter
import re
from database.queries import ReviewDatabase

class ThematicSynthesizer:
    """Thematic synthesis with optional AI assistance."""

    def __init__(self, review_db: ReviewDatabase, use_ai: bool = True):
        """
        Initialize thematic synthesizer.

        Args:
            review_db: ReviewDatabase instance
            use_ai: Whether to use AI for theme suggestions
        """
        self.review_db = review_db
        self.use_ai = use_ai

        if use_ai:
            try:
                from sentence_transformers import SentenceTransformer
                from sklearn.cluster import DBSCAN
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                self.DBSCAN = DBSCAN
            except ImportError:
                self.use_ai = False
                self.embedder = None
                self.DBSCAN = None

    @staticmethod
    def _check_ai_dependencies() -> bool:
        """Check if AI dependencies are available."""
        try:
            import sentence_transformers
            import sklearn
            return True
        except ImportError:
            return False

    def suggest_themes(
        self,
        review_id: int,
        field_name: str = 'main_results'
    ) -> Dict[str, Any]:
        """
        Suggest themes from extracted data.

        Args:
            review_id: Review ID
            field_name: Extraction field to analyze

        Returns:
            Dictionary with suggested themes or raw extractions
        """
        # Get all extractions for this review
        extractions = self._get_all_extractions_field(review_id, field_name)

        if not self.use_ai or self.embedder is None:
            # Manual mode - return raw data
            return {
                'mode': 'manual',
                'extractions': extractions
            }

        # Extract text values
        texts = []
        paper_ids = []

        for extraction in extractions:
            data = json.loads(extraction['extracted_data_json'])
            value = data.get(field_name)

            if isinstance(value, list):
                for item in value:
                    texts.append(str(item))
                    paper_ids.append(extraction['paper_id'])
            elif value:
                texts.append(str(value))
                paper_ids.append(extraction['paper_id'])

        if not texts:
            return {
                'mode': 'ai',
                'themes': [],
                'note': 'No text to cluster'
            }

        # Embed all findings
        embeddings = self.embedder.encode(texts)

        # Cluster similar findings
        clusterer = self.DBSCAN(eps=0.5, min_samples=2, metric='cosine')
        clusters = clusterer.fit_predict(embeddings)

        # Generate theme suggestions
        suggested_themes = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Noise cluster
                continue

            # Get texts in this cluster
            cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
            cluster_texts = [texts[i] for i in cluster_indices]
            cluster_papers = [paper_ids[i] for i in cluster_indices]

            # Extract keywords for theme name
            theme_name = self._extract_keywords(cluster_texts)

            suggested_themes.append({
                'suggested_name': theme_name,
                'example_quotes': cluster_texts[:5],
                'paper_ids': list(set(cluster_papers)),
                'paper_count': len(set(cluster_papers)),
                'finding_count': len(cluster_texts)
            })

        # Sort by paper count
        suggested_themes.sort(key=lambda t: t['paper_count'], reverse=True)

        return {
            'mode': 'ai',
            'themes': suggested_themes,
            'total_findings': len(texts),
            'clustered_findings': sum(1 for c in clusters if c != -1),
            'unclustered_findings': sum(1 for c in clusters if c == -1)
        }

    def _get_all_extractions_field(
        self,
        review_id: int,
        field_name: str
    ) -> List[Dict[str, Any]]:
        """Get all extractions with specified field."""
        # Get all papers in review
        papers = self.review_db.get_review_papers(review_id)

        extractions = []
        for paper_id in papers:
            paper_extractions = self.review_db.get_extractions(review_id, paper_id)

            for extraction in paper_extractions:
                data = json.loads(extraction['extracted_data_json'])
                if field_name in data:
                    extractions.append(extraction)

        return extractions

    def _extract_keywords(self, texts: List[str]) -> str:
        """Extract common keywords from cluster texts."""
        # Tokenize and count words
        words = []
        for text in texts:
            # Remove punctuation, lowercase, split
            tokens = re.findall(r'\b[a-z]{4,}\b', text.lower())
            words.extend(tokens)

        # Get most common words
        common_words = Counter(words).most_common(3)

        # Create theme name
        theme_name = ' + '.join(word for word, count in common_words)
        return theme_name.title()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/synthesis/test_thematic_analyzer.py -v`
Expected: PASS (manual mode test passes, AI test skipped if dependencies unavailable)

**Step 5: Commit**

```bash
git add synthesis/ tests/synthesis/test_thematic_analyzer.py
git commit -m "feat(synthesis): add AI-assisted thematic synthesis with clustering"
```

---

## Task 7: CLI - Create Review Command

**Files:**
- Create: `academic-helpers/literature-review/cli/__init__.py`
- Create: `academic-helpers/literature-review/cli/create_review.py`
- Test: `academic-helpers/literature-review/tests/cli/test_create_review.py`

**Step 1: Write the failing test**

```python
# tests/cli/test_create_review.py
import pytest
from click.testing import CliRunner
from cli.create_review import create_review
from database.connection import get_database_connection
from database.queries import ReviewDatabase

def test_create_review_command():
    """Test create review CLI command."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(create_review, [
            '--name', 'Test Review',
            '--question', 'What is the impact?',
            '--reviewers', 'reviewer_A,reviewer_B',
            '--ai'
        ])

        assert result.exit_code == 0
        assert 'Created review project' in result.output
        assert 'reviewer_A' in result.output

def test_create_review_no_ai():
    """Test creating review without AI."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(create_review, [
            '--name', 'Manual Review',
            '--question', 'Research question?',
            '--reviewers', 'reviewer_A',
            '--no-ai'
        ])

        assert result.exit_code == 0
        assert 'Created review project' in result.output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_create_review.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'cli'"

**Step 3: Implement create review command**

```python
# cli/__init__.py
"""CLI commands package."""
```

```python
# cli/create_review.py
"""CLI command to create a new review project."""
import click
import json
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@click.command()
@click.option('--name', required=True, help='Review project name')
@click.option('--question', required=True, help='Research question')
@click.option('--reviewers', required=True, help='Comma-separated reviewer IDs')
@click.option('--criteria', help='Inclusion criteria (JSON string)')
@click.option('--ai/--no-ai', default=True, help='Use AI theme suggestions')
@click.option('--db-path', help='Database path (default: literature_review.db)')
def create_review(name, question, reviewers, criteria, ai, db_path):
    """Initialize a new literature review project."""
    # Parse reviewers
    reviewer_list = [r.strip() for r in reviewers.split(',')]

    # Parse criteria
    if criteria:
        try:
            criteria_dict = json.loads(criteria)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON for criteria", err=True)
            raise click.Abort()
    else:
        criteria_dict = {}

    # Create review
    conn = get_database_connection(db_path)
    review_db = ReviewDatabase(conn)

    review_id = review_db.create_review(
        review_name=name,
        research_question=question,
        inclusion_criteria_json=json.dumps(criteria_dict),
        reviewers_json=json.dumps(reviewer_list),
        use_ai_suggestions=ai
    )

    conn.close()

    # Output success
    click.echo(f"✓ Created review project: {review_id}")
    click.echo(f"  Name: {name}")
    click.echo(f"  Research Question: {question}")
    click.echo(f"  Reviewers: {', '.join(reviewer_list)}")
    click.echo(f"  AI Suggestions: {'Enabled' if ai else 'Disabled'}")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  1. Import papers: python cli/import_papers.py --review-id {review_id} --pdf-dir path/to/pdfs")
    click.echo(f"  2. Start screening: python cli/run_screening.py --review-id {review_id} --reviewer-id <your-id> --stage title_abstract")

if __name__ == '__main__':
    create_review()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_create_review.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add cli/ tests/cli/test_create_review.py
git commit -m "feat(cli): add create-review command for initializing review projects"
```

---

## Task 8: Integration Test - Complete Workflow

**Files:**
- Create: `academic-helpers/literature-review/tests/integration/test_complete_workflow.py`

**Step 1: Write the integration test**

```python
# tests/integration/test_complete_workflow.py
"""Integration test for complete literature review workflow."""
import pytest
import json
from database.connection import get_database_connection
from database.queries import ReviewDatabase
from screening.interface import ScreeningInterface
from quality.reliability import ReliabilityCalculator
from extraction.template_loader import TemplateLoader

@pytest.fixture
def db():
    """Create in-memory database."""
    conn = get_database_connection(':memory:')
    return ReviewDatabase(conn)

def test_complete_workflow(db):
    """Test complete literature review workflow."""

    # Step 1: Create review
    review_id = db.create_review(
        review_name='Food Environment Review',
        research_question='What is the impact of food deserts on health?',
        inclusion_criteria_json=json.dumps({
            'population': 'Urban adults',
            'outcome': 'Diet quality or health outcomes'
        }),
        reviewers_json=json.dumps(['reviewer_A', 'reviewer_B'])
    )

    assert review_id is not None

    # Step 2: Import papers
    db.link_paper_to_review(review_id, 'paper_001')
    db.link_paper_to_review(review_id, 'paper_002')
    db.link_paper_to_review(review_id, 'paper_003')

    papers = db.get_review_papers(review_id)
    assert len(papers) == 3

    # Step 3: Title/Abstract Screening - Dual independent
    screener = ScreeningInterface(db)

    # Reviewer A screens
    screener.record_decision(review_id, 'paper_001', 'reviewer_A', 'title_abstract', 'include')
    screener.record_decision(review_id, 'paper_002', 'reviewer_A', 'title_abstract', 'exclude', 'Wrong population')
    screener.record_decision(review_id, 'paper_003', 'reviewer_A', 'title_abstract', 'include')

    # Reviewer B screens
    screener.record_decision(review_id, 'paper_001', 'reviewer_B', 'title_abstract', 'include')
    screener.record_decision(review_id, 'paper_002', 'reviewer_B', 'title_abstract', 'exclude', 'Out of scope')
    screener.record_decision(review_id, 'paper_003', 'reviewer_B', 'title_abstract', 'include')

    # Step 4: Calculate screening reliability
    calculator = ReliabilityCalculator(db)
    kappa_result = calculator.calculate_screening_kappa(review_id, 'title_abstract')

    assert kappa_result['kappa'] == 1.0  # Perfect agreement
    assert kappa_result['interpretation'] == 'Almost Perfect'

    # Step 5: Data extraction for included papers
    loader = TemplateLoader()
    template = loader.load_template('observational_study')

    extraction_data = {
        'study_design': 'cross_sectional',
        'sample_size': 500,
        'population_description': 'Urban adults in food deserts',
        'exposure_variables': ['Distance to supermarket'],
        'outcome_variables': ['Diet quality score'],
        'main_results': ['Greater distance associated with lower diet quality'],
        'quality_score': 7
    }

    db.insert_extraction(
        review_id, 'paper_001', 'reviewer_A',
        'observational_study',
        json.dumps(extraction_data)
    )

    extractions = db.get_extractions(review_id, 'paper_001')
    assert len(extractions) == 1

    # Step 6: Thematic synthesis
    theme_id = db.insert_theme(
        review_id=review_id,
        theme_name='Geographic Barriers',
        theme_description='Physical distance limiting food access',
        created_by='reviewer_A'
    )

    assert theme_id is not None

    themes = db.get_themes(review_id)
    assert len(themes) == 1
    assert themes[0]['theme_name'] == 'Geographic Barriers'

    # Workflow complete
    review = db.get_review(review_id)
    assert review['status'] == 'active'
```

**Step 2: Run integration test**

Run: `pytest tests/integration/test_complete_workflow.py -v`
Expected: PASS (entire workflow executes successfully)

**Step 3: Commit**

```bash
git add tests/integration/test_complete_workflow.py
git commit -m "test(integration): add complete workflow integration test"
```

---

## Task 9: Documentation - README

**Files:**
- Create: `academic-helpers/literature-review/README.md`

**Step 1: Create README**

```markdown
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
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README with installation, usage, architecture"
```

---

## Task 10: Requirements File

**Files:**
- Create: `academic-helpers/literature-review/requirements.txt`

**Step 1: Create requirements file**

```txt
# Core dependencies
pyyaml>=6.0
click>=8.0
pandas>=2.0
matplotlib>=3.7
networkx>=3.0

# Testing
pytest>=7.4
pytest-cov>=4.1

# Optional: AI features
sentence-transformers>=2.2  # For AI theme suggestions
scikit-learn>=1.3          # For clustering and Cohen's kappa
```

**Step 2: Create requirements-dev.txt**

```txt
# Development dependencies
-r requirements.txt

# Code quality
black>=23.0
flake8>=6.0
mypy>=1.5

# Documentation
sphinx>=7.0
sphinx-rtd-theme>=1.3
```

**Step 3: Commit**

```bash
git add requirements.txt requirements-dev.txt
git commit -m "build: add requirements files for core and development dependencies"
```

---

## Final Integration Notes

### Directory Structure (Final)

```
academic-helpers/literature-review/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── queries.py
│   └── schema.sql
├── templates/
│   ├── observational_study.yaml
│   ├── spatial_analysis.yaml
│   └── qualitative_study.yaml
├── screening/
│   ├── __init__.py
│   └── interface.py
├── extraction/
│   ├── __init__.py
│   └── template_loader.py
├── synthesis/
│   ├── __init__.py
│   └── thematic_analyzer.py
├── quality/
│   ├── __init__.py
│   └── reliability.py
├── cli/
│   ├── __init__.py
│   └── create_review.py
└── tests/
    ├── database/
    │   ├── test_schema.py
    │   └── test_queries.py
    ├── extraction/
    │   └── test_template_loader.py
    ├── screening/
    │   └── test_interface.py
    ├── quality/
    │   └── test_reliability.py
    ├── synthesis/
    │   └── test_thematic_analyzer.py
    ├── cli/
    │   └── test_create_review.py
    └── integration/
        └── test_complete_workflow.py
```

### Testing the Module

```bash
# Install dependencies
cd academic-helpers/literature-review
pip install -r requirements.txt

# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration test only
pytest tests/integration/test_complete_workflow.py -v

# Test CLI commands
python cli/create_review.py --name "Test" --question "Q?" --reviewers "A,B"
```

### Next Steps (Not in This Plan)

Additional features to implement separately:

1. **Output Generation** - PRISMA diagrams, evidence tables, theme visualizations
2. **Conflict Resolution Interface** - UI for resolving screening disagreements
3. **Batch Import** - Bulk PDF import with progress tracking
4. **Web Interface** - Flask/FastAPI web UI for screening and extraction
5. **Export Formats** - CSV, Excel, JSON export utilities
6. **Advanced Reliability** - Intraclass correlation, Fleiss' kappa for >2 reviewers

---

## Implementation Complete

This plan implements the core Literature Review Workflow Module with:

✅ Database schema and query layer
✅ YAML extraction templates (observational, spatial, qualitative)
✅ Screening interface with decision validation
✅ Inter-rater reliability calculator (Cohen's kappa)
✅ AI-assisted thematic synthesis with clustering
✅ CLI command for creating review projects
✅ Complete integration test
✅ Comprehensive documentation

**Total Implementation Time Estimate**: 8-12 hours for experienced developer

**Testing Coverage**: All core components have unit tests + integration test for complete workflow
