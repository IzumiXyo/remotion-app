import type {FC} from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Hello: FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const scale = interpolate(entrance, [0, 1], [0.6, 1]);
  const opacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const rotation = interpolate(frame, [0, 90], [0, 360]);
  const glow = interpolate(frame, [0, 45, 90], [0.35, 0.7, 0.35]);

  return (
    <AbsoluteFill
      style={{
        background:
          'linear-gradient(160deg, #0f172a 0%, #1e1b4b 45%, #312e81 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'sans-serif',
      }}
    >
      <div
        style={{
          position: 'absolute',
          width: 700,
          height: 700,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(129,140,248,0.8) 0%, rgba(129,140,248,0) 70%)',
          opacity: glow,
          transform: `scale(${1 + Math.sin(frame / 10) * 0.08})`,
        }}
      />
      <div
        style={{
          width: 260,
          height: 260,
          borderRadius: 64,
          border: '6px solid rgba(255,255,255,0.85)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transform: `scale(${scale}) rotate(${rotation}deg)`,
          boxShadow: '0 0 80px rgba(129,140,248,0.6)',
          marginBottom: 80,
        }}
      >
        <div
          style={{
            width: 90,
            height: 90,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #f472b6, #38bdf8)',
          }}
        />
      </div>
      <h1
        style={{
          color: 'white',
          fontSize: 96,
          fontWeight: 800,
          margin: 0,
          opacity,
          transform: `translateY(${(1 - entrance) * 60}px)`,
          textAlign: 'center',
          letterSpacing: -2,
        }}
      >
        Halo dari
        <br />
        Remotion!
      </h1>
      <p
        style={{
          color: 'rgba(226,232,240,0.85)',
          fontSize: 40,
          marginTop: 32,
          opacity,
          textAlign: 'center',
        }}
      >
        Termux • Node 26 • FFmpeg 9
      </p>
    </AbsoluteFill>
  );
};
