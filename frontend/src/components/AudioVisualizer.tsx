import { useEffect, useRef } from "react";

interface AudioVisualizerProps {
  isSpeaking: boolean;
  isConnected: boolean;
}

export default function AudioVisualizer({ isSpeaking, isConnected }: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let phase = 0;

    // Set canvas dimensions dynamically based on parent container size
    const resizeCanvas = () => {
      if (canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight || 100;
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const render = () => {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      // Dynamically morph speed and max height based on speaking state
      const speed = isSpeaking ? 0.08 : 0.025;
      const maxAmplitude = isSpeaking ? height * 0.32 : height * 0.12;

      phase += speed;

      // Draw three overlaying sine waves with different offsets, frequencies, and transparencies
      const waves = [
        {
          amplitude: maxAmplitude,
          frequency: 0.015,
          color: isSpeaking ? "rgba(90, 168, 154, 0.55)" : "rgba(120, 116, 110, 0.25)",
          offset: 0,
        },
        {
          amplitude: maxAmplitude * 0.7,
          frequency: 0.024,
          color: isSpeaking ? "rgba(74, 140, 111, 0.4)" : "rgba(120, 116, 110, 0.15)",
          offset: Math.PI / 3,
        },
        {
          amplitude: maxAmplitude * 0.45,
          frequency: 0.035,
          color: isSpeaking ? "rgba(90, 168, 154, 0.25)" : "rgba(120, 116, 110, 0.1)",
          offset: (2 * Math.PI) / 3,
        },
      ];

      waves.forEach((wave) => {
        ctx.beginPath();
        ctx.strokeStyle = wave.color;
        ctx.lineWidth = isSpeaking ? 2.5 : 1.5;

        // Apply a glowing shadow blur when speaking
        if (isSpeaking) {
          ctx.shadowBlur = 10;
          ctx.shadowColor = wave.color;
        } else {
          ctx.shadowBlur = 0;
        }

        for (let x = 0; x < width; x++) {
          // Use a sine wave modulated by a bell curve (taper) so it starts/ends at 0 at the margins
          const taper = Math.sin((x / width) * Math.PI);
          const y =
            centerY +
            Math.sin(x * wave.frequency + phase + wave.offset) * wave.amplitude * taper;

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      });

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, [isSpeaking, isConnected]);

  return (
    <div style={{ width: "100%", height: "80px", position: "relative", overflow: "hidden" }}>
      <canvas ref={canvasRef} style={{ display: "block", width: "100%", height: "100%" }} />
    </div>
  );
}
