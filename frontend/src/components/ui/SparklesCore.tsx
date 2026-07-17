import { loadSlim } from "@tsparticles/slim";
import { Particles, ParticlesProvider } from "@tsparticles/react";
import type { ISourceOptions } from "@tsparticles/engine";

interface SparklesCoreProps {
  id?: string;
  className?: string;
  background?: string;
  minSize?: number;
  maxSize?: number;
  speed?: number;
  particleColor?: string;
  particleDensity?: number;
}

function SparklesCoreInner({
  id = "sparkles",
  className,
  background = "transparent",
  minSize = 0.6,
  maxSize = 1.4,
  speed = 1,
  particleColor = "#3d7a6e",
  particleDensity = 80,
}: SparklesCoreProps) {
  const options: ISourceOptions = {
    background: {
      color: {
        value: background,
      },
    },
    fpsLimit: 120,
    interactivity: {
      events: {
        resize: { enable: true },
      },
    },
    particles: {
      color: {
        value: particleColor,
      },
      move: {
        direction: "none",
        enable: true,
        outModes: {
          default: "bounce",
        },
        random: false,
        speed: speed,
        straight: false,
      },
      number: {
        density: {
          enable: true,
        },
        value: particleDensity,
      },
      opacity: {
        value: {
          min: 0.2,
          max: 0.6,
        },
        animation: {
          enable: true,
          speed: speed * 0.5,
          sync: false,
        },
      },
      size: {
        value: {
          min: minSize,
          max: maxSize,
        },
        animation: {
          enable: true,
          speed: speed * 0.5,
          sync: false,
        },
      },
    },
    detectRetina: true,
  };

  return <Particles id={id} className={className} options={options} />;
}

export function SparklesCore(props: SparklesCoreProps) {
  return (
    <ParticlesProvider
      init={async (engine) => {
        await loadSlim(engine);
      }}
    >
      <SparklesCoreInner {...props} />
    </ParticlesProvider>
  );
}

export function SparklesFullPage({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`relative ${className}`}>
      <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 0 }}>
        <SparklesCore
          id="fullpage-sparkles"
          background="transparent"
          minSize={0.6}
          maxSize={1.8}
          speed={0.6}
          particleColor="var(--color-primary)"
          particleDensity={140}
          className="w-full h-full"
        />
      </div>
      <div className="relative" style={{ zIndex: 1 }}>
        {children}
      </div>
    </div>
  );
}

export default SparklesCore;
