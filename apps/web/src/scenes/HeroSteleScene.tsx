import React from 'react';
import { SteleViewer } from '../components/stele3d/SteleViewer';
interface HeroSteleSceneProps {
  onHotspotClick?: (point: { title: string; desc: string }) => void;
  className?: string;
}
/** Compatibility entry: every exhibition view uses the same authored stele. */
export const HeroSteleScene: React.FC<HeroSteleSceneProps> = ({onHotspotClick, className = ''}) => (
  <SteleViewer onHotspotClick={onHotspotClick} className={className} />
);
