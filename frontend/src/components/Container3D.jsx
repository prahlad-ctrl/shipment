import { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Edges, Text } from '@react-three/drei';
import { Package } from 'lucide-react';

export default function Container3D({ constraints }) {
  // Teu standard internal dims: 5.9m L x 2.35m W x 2.39m H
  const TEU_DIMS = [5.9, 2.39, 2.35];

  const boxes = useMemo(() => {
    let items = [];
    if (constraints?.cargo_items && constraints.cargo_items.length > 0) {
      items = constraints.cargo_items;
    } else {
      // Fallback: generate mock individual boxes based on weight
      const weight = constraints?.weight_kg || 500;
      // Let's assume each typical box is 25kg to make it look visually packed!
      const numBoxes = Math.max(1, Math.ceil(weight / 25));
      // Standard small carton size: 0.5m x 0.4m x 0.4m
      items = [{ type: 'Cartons', qty: Math.min(numBoxes, 200), dim: [0.5, 0.4, 0.4] }];
    }

    const generatedBoxes = [];
    // Super basic rudimentary 3D packing algorithm for visuals
    let currentX = -TEU_DIMS[0] / 2;
    let currentY = -TEU_DIMS[1] / 2;
    let currentZ = -TEU_DIMS[2] / 2;
    
    let maxRowHeight = 0;
    let maxRowDepth = 0;

    items.forEach(item => {
      const dim = item.dim || [1, 1, 1];
      const w = dim[0]; // Length
      const h = dim[1]; // Height
      const d = dim[2]; // Depth

      for (let i = 0; i < item.qty; i++) {
        // If it overflows length, wrap to next row in depth
        if (currentX + w > TEU_DIMS[0] / 2) {
          currentX = -TEU_DIMS[0] / 2;
          currentZ += maxRowDepth;
          maxRowDepth = 0;
        }
        // If it overflows depth, wrap to next level in height
        if (currentZ + d > TEU_DIMS[2] / 2) {
          currentZ = -TEU_DIMS[2] / 2;
          currentY += maxRowHeight;
          maxRowHeight = 0;
        }

        // If it overflows height, container is functionally full (visual only constraint)
        if (currentY + h > TEU_DIMS[1] / 2) {
            break;
        }

        // Add box center coordinates
        generatedBoxes.push({
          position: [currentX + w/2, currentY + h/2, currentZ + d/2],
          size: [w, h, d],
          color: `hsl(${(generatedBoxes.length * 15) % 360}, 70%, 50%)`
        });

        currentX += w;
        if (h > maxRowHeight) maxRowHeight = h;
        if (d > maxRowDepth) maxRowDepth = d;
      }
    });

    return generatedBoxes;
  }, [constraints]);

  if (!constraints) return null;

  return (
    <div className="glass-card-static" style={{ height: '300px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: '1rem', left: '1rem', zIndex: 10, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontWeight: 500 }}>
        <Package size={18} style={{ color: 'var(--accent-purple)' }}/>
        3D Cargo Load
      </div>
      
      <Canvas camera={{ position: [8, 4, 8], fov: 45 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, 10, -5]} intensity={0.5} />
        <OrbitControls makeDefault enablePan={false} autoRotate autoRotateSpeed={0.5} />
        
        {/* Container Wireframe */}
        <Box args={TEU_DIMS} position={[0, 0, 0]}>
          <meshBasicMaterial transparent opacity={0.05} color="#3b82f6" />
          <Edges color="#3b82f6" scale={1} threshold={15} />
        </Box>

        {/* Cargo Boxes */}
        {boxes.map((box, i) => (
          <Box key={i} args={box.size} position={box.position}>
             <meshStandardMaterial color={box.color} roughness={0.3} metalness={0.1} />
             <Edges color="white" scale={1.01} linewidth={1} opacity={0.3} transparent/>
          </Box>
        ))}

        <gridHelper args={[10, 10, '#ffffff', '#ffffff']} position={[0, -TEU_DIMS[1]/2 - 0.01, 0]} opacity={0.1} transparent />
      </Canvas>
      
      <div style={{ position: 'absolute', bottom: '1rem', right: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        Total Packed: {boxes.length} units
      </div>
    </div>
  );
}
