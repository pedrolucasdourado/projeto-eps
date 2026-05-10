"use client";

import { useCallback, useMemo, useRef, useState } from "react";

type Props = {
  value: number[];
  onChange: (next: number[]) => void;
  disabled?: boolean;
};

const SIZE = 220;
const PAD = 28;
const SPACING = (SIZE - 2 * PAD) / 2;

function dotXY(point: number): { x: number; y: number } {
  const idx = point - 1;
  const col = idx % 3;
  const row = Math.floor(idx / 3);
  return { x: PAD + col * SPACING, y: PAD + row * SPACING };
}

function arrowHead(
  from: { x: number; y: number },
  to: { x: number; y: number },
  length = 10,
): string {
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2;
  const angle = Math.atan2(to.y - from.y, to.x - from.x);
  const tipX = mx + Math.cos(angle) * (length * 0.5);
  const tipY = my + Math.sin(angle) * (length * 0.5);
  const leftX = mx - Math.cos(angle + 2.6) * length;
  const leftY = my - Math.sin(angle + 2.6) * length;
  const rightX = mx - Math.cos(angle - 2.6) * length;
  const rightY = my - Math.sin(angle - 2.6) * length;
  return `M ${leftX},${leftY} L ${tipX},${tipY} L ${rightX},${rightY}`;
}

/**
 * Componente interativo para capturar uma senha-padrão (gesture).
 * O usuário pode clicar nos pontos OU arrastar pelo grid (toque ou mouse).
 * Renderiza setas no meio de cada segmento e destaca o ponto inicial.
 */
export function PatternInput({ value, onChange, disabled }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleClickDot = useCallback(
    (n: number) => {
      if (disabled) return;
      if (value.includes(n)) return;
      onChange([...value, n]);
    },
    [value, onChange, disabled],
  );

  const findNearestDot = useCallback(
    (clientX: number, clientY: number): number | null => {
      const svg = svgRef.current;
      if (!svg) return null;
      const rect = svg.getBoundingClientRect();
      const x = ((clientX - rect.left) / rect.width) * SIZE;
      const y = ((clientY - rect.top) / rect.height) * SIZE;
      for (let n = 1; n <= 9; n++) {
        const { x: cx, y: cy } = dotXY(n);
        if ((x - cx) ** 2 + (y - cy) ** 2 <= 22 * 22) return n;
      }
      return null;
    },
    [],
  );

  function onPointerDown(ev: React.PointerEvent<SVGSVGElement>) {
    if (disabled) return;
    setIsDragging(true);
    const n = findNearestDot(ev.clientX, ev.clientY);
    if (n != null) handleClickDot(n);
  }

  function onPointerMove(ev: React.PointerEvent<SVGSVGElement>) {
    if (!isDragging || disabled) return;
    const n = findNearestDot(ev.clientX, ev.clientY);
    if (n != null && !value.includes(n)) {
      onChange([...value, n]);
    }
  }

  function onPointerUp() {
    setIsDragging(false);
  }

  const coords = useMemo(() => value.map(dotXY), [value]);
  const start = coords[0];

  return (
    <div className="space-y-2">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="touch-none select-none rounded border border-shell-border bg-shell-bg"
        style={{ width: SIZE, height: SIZE, maxWidth: "100%" }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => {
          const { x, y } = dotXY(n);
          const selected = value.includes(n);
          return (
            <g key={n} onClick={() => handleClickDot(n)} style={{ cursor: disabled ? "not-allowed" : "pointer" }}>
              <circle
                cx={x}
                cy={y}
                r={12}
                fill={selected ? "#2a4f86" : "transparent"}
                stroke={selected ? "#7aa9ff" : "#6e6e78"}
                strokeWidth={2}
              />
              <text
                x={x - 14}
                y={y + 22}
                fontSize={10}
                fill="#9ca3af"
                textAnchor="middle"
              >
                {n}
              </text>
            </g>
          );
        })}

        {coords.length > 1
          ? coords.slice(0, -1).map((p, i) => {
              const q = coords[i + 1];
              return (
                <g key={`seg-${i}`}>
                  <line
                    x1={p.x}
                    y1={p.y}
                    x2={q.x}
                    y2={q.y}
                    stroke="#cccccc"
                    strokeWidth={3}
                  />
                  <path
                    d={arrowHead(p, q)}
                    fill="none"
                    stroke="#7aa9ff"
                    strokeWidth={2}
                  />
                </g>
              );
            })
          : null}

        {start ? (
          <circle
            cx={start.x}
            cy={start.y}
            r={18}
            fill="none"
            stroke="#28a745"
            strokeWidth={2}
          />
        ) : null}
      </svg>

      <div className="flex items-center gap-3 text-sm text-shell-muted">
        <span>Sequência:</span>
        <span className="font-mono text-shell-text">
          {value.length > 0 ? value.join(" → ") : "—"}
        </span>
        <button
          type="button"
          onClick={() => onChange([])}
          disabled={disabled || value.length === 0}
          className="ml-auto rounded border border-shell-border px-2 py-1 text-xs text-shell-text disabled:opacity-60"
        >
          Limpar
        </button>
      </div>
      {value.length > 0 && value.length < 4 ? (
        <p className="text-xs text-amber-300">
          O padrão precisa de pelo menos 4 pontos.
        </p>
      ) : null}
    </div>
  );
}
