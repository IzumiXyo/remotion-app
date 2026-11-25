import type {FC} from 'react';
import {useMemo, useRef} from 'react';
import {Bloom, EffectComposer, Vignette} from '@react-three/postprocessing';
import {ThreeCanvas} from '@remotion/three';
import {useFrame} from '@react-three/fiber';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {Group, Mesh} from 'three';

const COUNT = 140;

const Scene: FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const group = useRef<Group>(null);
  const knot = useRef<Mesh>(null);

  useFrame(() => {
    if (group.current) {
      group.current.rotation.y = t * 0.35;
    }
    if (knot.current) {
      knot.current.rotation.x = t * 0.7;
      knot.current.rotation.y = t * 1.1;
    }
  });

  const cubes = useMemo(
    () =>
      Array.from({length: COUNT}, (_, i) => {
        const angle = (i / COUNT) * Math.PI * 2;
        const radius = 2.2 + (i % 7) * 0.28;
        return {
          x: Math.cos(angle) * radius,
          z: Math.sin(angle) * radius,
          y: (((i * 37) % 100) / 100) * 2.4 - 0.2,
          s: 0.12 + (((i * 13) % 10) / 55),
          color: ['#f472b6', '#38bdf8', '#fbbf24', '#a78bfa'][i % 4],
        };
      }),
    [],
  );

  return (
    <>
      <color attach="background" args={['#070b18']} />
      <fog attach="fog" args={['#070b18', 6, 16]} />
      <ambientLight intensity={0.6} color="#b7c7ff" />
      <directionalLight position={[4, 6, 3]} intensity={2.2} color="#ffd9a0" />
      <pointLight position={[-4, 2, -3]} intensity={20} color="#6d7cff" />

      <group ref={group}>
        {cubes.map((c, i) => (
          <mesh
            key={i}
            position={[c.x, c.y + Math.sin(t * 2 + i) * 0.15, c.z]}
            scale={c.s}
          >
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial
              color={c.color}
              roughness={0.35}
              metalness={0.25}
            />
          </mesh>
        ))}
      </group>

      <mesh ref={knot} position={[0, 1.3, 0]}>
        <torusKnotGeometry args={[0.8, 0.26, 220, 32]} />
        <meshStandardMaterial
          color="#ff8a5c"
          emissive="#ff5a1f"
          emissiveIntensity={1.6}
          roughness={0.2}
          metalness={0.7}
        />
      </mesh>

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.35, 0]}>
        <circleGeometry args={[9, 64]} />
        <meshStandardMaterial color="#111827" roughness={0.9} />
      </mesh>

      <EffectComposer multisampling={4}>
        <Bloom
          intensity={0.9}
          luminanceThreshold={1}
          mipmapBlur
          radius={0.7}
        />
        <Vignette eskil={false} offset={0.2} darkness={0.85} />
      </EffectComposer>
    </>
  );
};

export const Bench: FC = () => {
  const {width, height} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: '#070b18'}}>
      <ThreeCanvas
        width={width}
        height={height}
        camera={{position: [0, 2.2, 7], fov: 42}}
      >
        <Scene />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
