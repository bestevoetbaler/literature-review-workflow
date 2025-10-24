-- Main papers table
CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    title TEXT NOT NULL,
    authors_json TEXT,           -- JSON array of author names
    year INTEGER,
    journal TEXT,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    doi TEXT UNIQUE,
    abstract TEXT,
    keywords_json TEXT,          -- JSON array
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ml_enhanced BOOLEAN DEFAULT 0
);

-- Sections table (for embeddings and search)
CREATE TABLE IF NOT EXISTS sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,  -- 'abstract', 'introduction', 'methods', etc.
    content TEXT NOT NULL,
    embedding BLOB,              -- numpy array (768 floats)
    word_count INTEGER
);

-- Tables from papers
CREATE TABLE IF NOT EXISTS paper_tables (
    table_id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    table_number TEXT,
    caption TEXT,
    data_json TEXT               -- JSON representation of table
);

-- Figures from papers
CREATE TABLE IF NOT EXISTS paper_figures (
    figure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    figure_number TEXT,
    caption TEXT,
    image_path TEXT
);

-- Citations (references within papers)
CREATE TABLE IF NOT EXISTS citations (
    citation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper_id TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    cited_title TEXT,
    cited_authors_json TEXT,
    cited_year INTEGER,
    cited_doi TEXT,
    confidence TEXT CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- Collections (user-defined tags)
CREATE TABLE IF NOT EXISTS collections (
    collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many: papers ↔ collections
CREATE TABLE IF NOT EXISTS paper_collections (
    paper_id TEXT REFERENCES papers(paper_id) ON DELETE CASCADE,
    collection_id INTEGER REFERENCES collections(collection_id) ON DELETE CASCADE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (paper_id, collection_id)
);

-- Key findings
CREATE TABLE IF NOT EXISTS key_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    finding_text TEXT NOT NULL,
    confidence REAL,             -- 0.0-1.0
    section_source TEXT          -- 'results', 'discussion', etc.
);

-- Full-text search (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
    paper_id UNINDEXED,
    title,
    authors,
    abstract,
    keywords,
    content='papers',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
    INSERT INTO papers_fts(paper_id, title, authors, abstract, keywords)
    VALUES (new.paper_id, new.title, new.authors_json, new.abstract, new.keywords_json);
END;

CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
    DELETE FROM papers_fts WHERE paper_id = old.paper_id;
END;

CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
    UPDATE papers_fts
    SET title = new.title,
        authors = new.authors_json,
        abstract = new.abstract,
        keywords = new.keywords_json
    WHERE paper_id = new.paper_id;
END;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_journal ON papers(journal);
CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited_doi ON citations(cited_doi);
