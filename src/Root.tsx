import type {FC} from 'react';
import {Composition} from 'remotion';
import {Hello} from './Hello';
import {Bench} from './videos/bench/Bench';

export const RemotionRoot: FC = () => {
  return (
    <>
      <Composition
        id="Hello"
        component={Hello}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Bench"
        component={Bench}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
