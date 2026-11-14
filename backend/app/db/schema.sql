PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE
        CHECK (length(slug) BETWEEN 1 AND 64),
    title TEXT NOT NULL
        CHECK (length(title) BETWEEN 1 AND 120),
    subtitle TEXT NOT NULL DEFAULT ''
        CHECK (length(subtitle) <= 200),
    description TEXT NOT NULL DEFAULT ''
        CHECK (length(description) <= 2000),
    location_name TEXT NOT NULL DEFAULT ''
        CHECK (length(location_name) <= 120),
    processed_at TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS point_cloud_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL
        CHECK (length(name) BETWEEN 1 AND 120),
    ept_path TEXT NOT NULL,
    epsg INTEGER NOT NULL CHECK (epsg > 0),
    point_count INTEGER NOT NULL CHECK (point_count >= 0),
    bounds_json TEXT NOT NULL CHECK (json_valid(bounds_json)),
    size_bytes INTEGER NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE (project_id, ept_path)
);

CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 120),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 1000),
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_published INTEGER NOT NULL DEFAULT 1 CHECK (is_published IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_projects_status
    ON projects(status);
CREATE INDEX IF NOT EXISTS idx_point_cloud_project
    ON point_cloud_datasets(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_point_cloud_primary
    ON point_cloud_datasets(project_id)
    WHERE is_primary = 1;
CREATE INDEX IF NOT EXISTS idx_annotations_public
    ON annotations(project_id, is_published, display_order);
