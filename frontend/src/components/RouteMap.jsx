import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Map as MapIcon } from 'lucide-react';
import { MapContainer, TileLayer, Polyline, CircleMarker } from 'react-leaflet';
import TimelineScrubber from './TimelineScrubber';
import 'leaflet/dist/leaflet.css';

// Simple polyline interpolator
function interpolatePosition(waypoints, progress) {
    if (!waypoints || waypoints.length === 0) return null;
    if (progress <= 0) return waypoints[0];
    if (progress >= 1) return waypoints[waypoints.length - 1];
    
    // Total segments geometry mapped
    const totalSegments = waypoints.length - 1;
    let totalDist = 0;
    const segmentDists = [];
    
    for (let i = 0; i < totalSegments; i++) {
        const p1 = waypoints[i];
        const p2 = waypoints[i+1];
        // Flat euclidean approximation is fine for tiny steps
        const dist = Math.sqrt(Math.pow(p2[0] - p1[0], 2) + Math.pow(p2[1] - p1[1], 2));
        segmentDists.push(dist);
        totalDist += dist;
    }
    
    const targetDist = progress * totalDist;
    let accumulated = 0;
    for (let i = 0; i < totalSegments; i++) {
        const d = segmentDists[i];
        if (accumulated + d >= targetDist) {
            const fraction = d === 0 ? 0 : (targetDist - accumulated) / d;
            const p1 = waypoints[i];
            const p2 = waypoints[i+1];
            return [
                p1[0] + (p2[0] - p1[0]) * fraction,
                p1[1] + (p2[1] - p1[1]) * fraction
            ];
        }
        accumulated += d;
    }
    return waypoints[waypoints.length - 1];
}

export default function RouteMap({ routes }) {
  const [progress, setProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 1) return 0;
        return p + 0.002; // Scrub speed
      });
    }, 30);
    return () => clearInterval(interval);
  }, [isPlaying]);
  const routeLines = useMemo(() => {
    if (!routes || routes.length === 0) return [];

    return routes.map((route, ri) => {
      const routeInfo = route.route || route;
      const isRecommended = route.is_recommended;

      return { 
        waypoints: routeInfo.waypoints || [], 
        isRecommended, 
        mode: routeInfo.mode, 
        name: routeInfo.name, 
        index: ri 
      };
    });
  }, [routes]);

  const bounds = useMemo(() => {
    let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    let hasPoints = false;
    routeLines.forEach(r => {
      r.waypoints.forEach(([lat, lng]) => {
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
        if (lng < minLng) minLng = lng;
        if (lng > maxLng) maxLng = lng;
        hasPoints = true;
      });
    });
    
    // Add some padding to bounds
    if (!hasPoints) return [[-20, -60], [60, 60]];
    return [
      [minLat - 5, minLng - 5],
      [maxLat + 5, maxLng + 5]
    ];
  }, [routeLines]);

  const allLocations = useMemo(() => {
    const locs = [];
    routeLines.forEach((r) => {
      if (r.waypoints.length > 0) {
        locs.push({ coord: r.waypoints[0] });
        locs.push({ coord: r.waypoints[r.waypoints.length - 1] });
      }
    });

    // Remove overlapping dots
    const unique = [];
    const seen = new Set();
    locs.forEach(l => {
       const key = `${l.coord[0].toFixed(2)},${l.coord[1].toFixed(2)}`;
       if(!seen.has(key)) { 
         seen.add(key); 
         unique.push(l); 
       }
    });
    return unique;
  }, [routeLines]);

  if (!routes || routes.length === 0) return null;

  const modeColor = {
    air: '#3b82f6',
    sea: '#06b6d4',
    road: '#10b981',
    rail: '#f59e0b',
    multimodal: '#8b5cf6',
  };

  return (
    <section className="map-section animate-fade-in-up">
      <div className="section-header">
        <div className="section-icon" style={{ background: 'rgba(6, 182, 212, 0.15)' }}>
          <MapIcon size={18} style={{ color: 'var(--accent-cyan)' }} />
        </div>
        <div className="section-title">Interactive Route Map</div>
      </div>

      <div className="glass-card-static map-card" style={{ padding: '4px', overflow: 'hidden' }}>
        <MapContainer 
          bounds={bounds} 
          style={{ height: '400px', width: '100%', borderRadius: 'calc(var(--radius-lg) - 4px)' }} 
          scrollWheelZoom={true}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          
          {/* Unrecommended routes first (z-index) */}
          {routeLines.filter(r => !r.isRecommended).map((r, i) => {
            const color = modeColor[r.mode] || '#3b82f6';
            if (r.waypoints.length === 0) return null;
            return (
              <Polyline 
                key={`poly-unrec-${i}`} 
                positions={r.waypoints} 
                pathOptions={{ 
                  color, 
                  weight: 3,
                  dashArray: '8, 8',
                  opacity: 0.6
                }} 
              />
            );
          })}

          {/* Recommended routes on top */}
          {routeLines.filter(r => r.isRecommended).map((r, i) => {
            const color = modeColor[r.mode] || '#3b82f6';
            if (r.waypoints.length === 0) return null;
            return (
              <polyline key={`poly-rec-${i}`}>
                 {/* Glow effect */}
                 <Polyline 
                  positions={r.waypoints} 
                  pathOptions={{ color, weight: 12, opacity: 0.15 }} 
                />
                {/* Main solid line */}
                <Polyline 
                  positions={r.waypoints} 
                  pathOptions={{ color, weight: 4, opacity: 1.0 }} 
                />
              </polyline>
            );
          })}

          {/* Locations marker dots */}
          {allLocations.map((loc, i) => (
            <CircleMarker 
              key={`marker-${i}`}
              center={loc.coord}
              radius={6}
              pathOptions={{ 
                fillColor: '#3b82f6', 
                color: '#fff', 
                weight: 2, 
                fillOpacity: 1 
              }}
            />
          ))}

          {/* Animated Fleet Markers */}
          {routeLines.map((r, i) => {
             const currentPos = interpolatePosition(r.waypoints, progress);
             if (!currentPos) return null;
             const color = modeColor[r.mode] || '#3b82f6';
             const radius = r.isRecommended ? 10 : 6;
             
             return (
               <CircleMarker 
                 key={`fleet-${i}`}
                 center={currentPos}
                 radius={radius}
                 pathOptions={{
                   fillColor: 'white',
                   color: color,
                   weight: 3,
                   fillOpacity: 1
                 }}
               />
             )
          })}
        </MapContainer>

        {/* Legend */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', padding: '0.5rem 1rem' }}>
          {Object.entries(modeColor).map(([mode, color]) => (
            <div key={mode} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
              <div style={{ width: '16px', height: '4px', background: color, borderRadius: '2px' }} />
              {mode}
            </div>
          ))}
        </div>
        
        <TimelineScrubber 
          progress={progress} 
          setProgress={setProgress} 
          isPlaying={isPlaying} 
          setIsPlaying={setIsPlaying} 
        />
      </div>
    </section>
  );
}
