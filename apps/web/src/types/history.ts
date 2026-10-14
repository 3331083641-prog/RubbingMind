export type Precision = 'exact' | 'approximate' | 'regional' | 'unknown';
export interface HistoricalLocation {
  id: string; name: string; modernName: string; longitude: number | null; latitude: number | null;
  coordinateSystem: 'WGS84'; precision: Precision; type: string; sourceId: string; sourceUrl: string;
  sourceTitle: string; verified: boolean; coordinateSourceUrl: string | null; coordinateMethod: string;
  accuracyKm: number | null; province: string | null; note: string; regionLocationId?: string | null;
}
export interface HistoricalNode {
  id: string; name: string; category: 'stele' | 'person' | 'place' | 'era' | 'document' | 'script' | 'office';
  desc: string; sourceIds: string[]; sourceUrl?: string; locationIds: string[]; verification: string;
  value: number; symbolSize: number;
}
export interface HistoricalLink { source: string; target: string; relation: string; sourceIds: string[]; sourceUrl: string; verification: string }
export interface HistoricalEvent {
  id: string; steleId: string; yearCE: number | null; eraName: string; title: string; description: string;
  locationId: string | null; eventType: string; sourceId: string; sourceUrl: string; verification: string;
}
export interface Source { id: string; title: string; url: string; institution: string; status: string; notes: string }
export interface HistoryDataset {
  steleId: string; formalName: string; eraName: string; yearCE: number | null; script: string; image: string;
  imageStatus: string; identity: string; rubbingPeriod: string; collectionNumber: string;
  originalStoneCollection: string; digitalRubbingCollection: string; authors: string[]; sourceIds: string[];
  sources: Source[]; locations: HistoricalLocation[]; nodes: HistoricalNode[]; links: HistoricalLink[];
  events: HistoricalEvent[]; routes: { id: string; kind: 'stone_transfer' | 'person_activity'; locationIds: string[]; sourceUrl: string; verified: boolean }[];
  offline?: boolean;
}
export type Selection = { kind: 'node' | 'place' | 'event'; id: string };
