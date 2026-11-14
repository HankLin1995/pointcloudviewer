# Database design

## Assumptions

- The first release publishes one WebODM survey, but the schema supports more projects later.
- Point-cloud files stay on the filesystem or object storage. SQLite stores metadata and public URLs only.
- The public site is read-only. Publishing and editing are future authenticated admin operations.

## ERD structure

### Project

- `id`: integer primary key
- `slug`: public, URL-safe identifier
- `title`: public project title
- `subtitle`: short introduction
- `description`: visitor-facing description
- `location_name`: non-sensitive public location label
- `processed_at`: WebODM processing date
- `status`: `draft` or `published`
- `created_at`, `updated_at`: audit timestamps

### PointCloudDataset

- `id`: integer primary key
- `project_id`: required parent project
- `name`: dataset label
- `ept_path`: server-side relative EPT path
- `epsg`: projected coordinate system
- `point_count`: total point count
- `bounds_json`: six-number native EPT bounds
- `size_bytes`: EPT directory size
- `is_primary`: marks the default viewer dataset
- `created_at`, `updated_at`: audit timestamps

### Annotation

- `id`: integer primary key
- `project_id`: required parent project
- `title`, `description`: visitor content
- `position_x`, `position_y`, `position_z`: native project coordinates
- `display_order`: stable presentation ordering
- `is_published`: public visibility
- `created_at`, `updated_at`: audit timestamps

## Relationships

- Project 1:N PointCloudDataset
- Project 1:N Annotation

## SQL schema

The executable SQLite DDL is in `backend/app/db/schema.sql`.
