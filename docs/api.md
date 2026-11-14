# Public API contract

Base path: `/api/v1`

## Endpoint list

- `GET /health` — service and point-cloud readiness.
- `GET /projects` — list published projects.
- `GET /projects/{slug}` — public project details.
- `GET /projects/{slug}/point-cloud` — primary EPT metadata and URL.
- `GET /projects/{slug}/annotations` — published viewer annotations.

## Request/response examples

### `GET /projects`

Request body: none.

Success `200`:

```json
{
  "items": [
    {
      "slug": "webodm-demo",
      "title": "空拍數位地景",
      "subtitle": "從空拍影像重建的三維地景",
      "location_name": "WebODM 示範測區",
      "processed_at": "2026-05-09T01:30:42Z"
    }
  ]
}
```

### `GET /projects/{slug}`

Request body: none. `slug` must be 1–64 lowercase letters, digits, or hyphens.

Success `200`:

```json
{
  "slug": "webodm-demo",
  "title": "空拍數位地景",
  "subtitle": "從空拍影像重建的三維地景",
  "description": "以 87 張空拍影像與地面控制點建立的公開三維成果。",
  "location_name": "WebODM 示範測區",
  "processed_at": "2026-05-09T01:30:42Z"
}
```

Not found `404`:

```json
{"detail":"Project not found"}
```

Validation error `422` uses FastAPI's standard `detail` field with field locations.

### `GET /projects/{slug}/point-cloud`

Success `200`:

```json
{
  "name": "2026 WebODM point cloud",
  "ept_url": "/pointclouds/webodm-demo/ept.json",
  "epsg": 32651,
  "point_count": 5150570,
  "size_bytes": 28574855,
  "bounds": [256353.3, 2627159.02, 89.77, 256898.01, 2627847.73, 137.62]
}
```

### `GET /projects/{slug}/annotations`

Success `200`:

```json
{"items":[]}
```

Only records where `is_published = 1` are returned.
