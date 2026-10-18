import type { StyleSpecification } from 'maplibre-gl';

/** Visual theme only. Coordinates stay on the existing GeoJSON and DEM tiles. */
export function chinaMapStyle(): StyleSpecification {
  const origin = location.origin;
  return {
    version: 8,
    sources: {
      china: { type: 'geojson', data: '/assets/gis/china-provinces.cgcs2000.geojson', attribution: '天地图行政区划 · CGCS2000 · geodeparse 镜像（MIT）' },
      terrain: { type: 'raster-dem', tiles: [`${origin}/assets/gis/terrain/{z}/{x}/{y}.png`], tileSize: 256, encoding: 'terrarium', minzoom: 0, maxzoom: 3, attribution: 'Mapzen Terrain Tiles · USGS / NOAA 等' },
      relief: { type: 'raster', tiles: [`${origin}/assets/gis/relief/{z}/{x}/{y}.png`], tileSize: 256, minzoom: 0, maxzoom: 3, attribution: '由上述 DEM 离线分层设色，未改坐标' },
      rivers: { type: 'geojson', data: '/assets/gis/rivers.geojson' },
      regions: { type: 'geojson', data: '/assets/gis/coordinate-regions.geojson' },
      relations: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    },
    layers: [
      { id: 'ink', type: 'background', paint: { 'background-color': '#061018' } },
      { id: 'terrain-color', type: 'raster', source: 'relief', paint: { 'raster-opacity': 1, 'raster-fade-duration': 0, 'raster-resampling': 'linear' } },
      { id: 'terrain-shade', type: 'hillshade', source: 'terrain', paint: { 'hillshade-exaggeration': 0.36, 'hillshade-illumination-direction': 315, 'hillshade-illumination-anchor': 'map', 'hillshade-shadow-color': '#021018', 'hillshade-highlight-color': '#e4efe4', 'hillshade-accent-color': '#c8a45a' } },
      { id: 'land', type: 'fill', source: 'china', filter: ['in', ['geometry-type'], ['literal', ['Polygon', 'MultiPolygon']]], paint: { 'fill-color': '#13252a', 'fill-opacity': 0 } },
      { id: 'province-outline', type: 'line', source: 'china', filter: ['in', ['geometry-type'], ['literal', ['Polygon', 'MultiPolygon']]], paint: { 'line-color': '#C8A45A', 'line-opacity': 0.88, 'line-width': ['interpolate', ['linear'], ['zoom'], 2, 0.55, 5, 1.05, 8, 1.5] } },
      { id: 'national-outline', type: 'line', source: 'china', filter: ['in', ['geometry-type'], ['literal', ['LineString', 'MultiLineString']]], paint: { 'line-color': '#E6BB61', 'line-opacity': 0.95, 'line-width': ['interpolate', ['linear'], ['zoom'], 2, 1.1, 5, 1.8, 8, 2.4] } },
      { id: 'rivers', type: 'line', source: 'rivers', paint: { 'line-color': '#43A99A', 'line-opacity': 0.82, 'line-width': ['interpolate', ['linear'], ['zoom'], 2, 0.7, 5, 1.5, 8, 2.4] } },
      { id: 'region-fill', type: 'fill', source: 'regions', minzoom: 4, paint: { 'fill-color': '#2b6150', 'fill-opacity': 0.22 } },
      { id: 'region-outline', type: 'line', source: 'regions', minzoom: 4, paint: { 'line-color': '#74ae96', 'line-width': 1.2, 'line-dasharray': [3, 3] } },
      { id: 'stone-links', type: 'line', source: 'relations', filter: ['==', ['get', 'kind'], 'stone_transfer'], paint: { 'line-color': '#dfb85e', 'line-width': 1.5, 'line-dasharray': [3, 3] } },
      { id: 'person-links', type: 'line', source: 'relations', filter: ['==', ['get', 'kind'], 'person_activity'], paint: { 'line-color': '#71bead', 'line-width': 1.2, 'line-dasharray': [1, 4] } },
    ],
  };
}
