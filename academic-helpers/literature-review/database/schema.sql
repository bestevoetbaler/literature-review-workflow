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
