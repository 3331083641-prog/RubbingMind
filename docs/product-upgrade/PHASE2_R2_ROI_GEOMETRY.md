# Phase2 R2 — ROI geometry contract (arch-backend)

- Canonical export schema: **glyph-bbox** `{x,y,w,h}` plus `schema` / `sourceSchema`.
- Ingest still accepts **review-box** `{x,y,width,height}` via `normalize_roi`.
- Ambiguous objects that carry both `w/h` and `width/height` are rejected (no silent mix).
- Module: `roi_geometry.py`. HTTP: `GET /api/roi-geometry/normalize`.
- Downstream: `roi_compare.build_roi_compare_session` always stores canonical bbox.
