import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { cn } from '@/lib/utils'

interface LineConfig {
  key: string
  label?: string
  color?: string
  strokeWidth?: number
  dashed?: boolean
}

interface AreaChartCardProps {
  data: Record<string, unknown>[]
  xKey: string
  lines: LineConfig[]
  height?: number
  className?: string
  showGrid?: boolean
  showLegend?: boolean
  formatter?: (value: number) => string
}

function CustomTooltip({ active, payload, label, formatter }: {
  active?: boolean
  payload?: { color: string; name: string; value: number }[]
  label?: string
  formatter?: (value: number) => string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-[var(--radius-md)] border px-3 py-2 text-xs shadow-md"
      style={{ background: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text-primary)', fontFamily: 'Geist Variable, sans-serif' }}>
      <p className="mb-1 font-medium" style={{ color: 'var(--color-text-secondary)' }}>{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name} : {formatter ? formatter(entry.value) : entry.value}
        </p>
      ))}
    </div>
  )
}

const DEFAULT_COLORS = ['var(--color-accent)', '#6B6860', '#B5B0A8', '#8B5CF6']

export function AreaChartCard({ data, xKey, lines, height = 240, className, showGrid = true, showLegend = false, formatter }: AreaChartCardProps) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            {lines.map((line, i) => {
              const color = line.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length]
              return (
                <linearGradient key={line.key} id={`gradient-${line.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              )
            })}
          </defs>
          {showGrid && <CartesianGrid strokeDasharray="0" stroke="var(--color-border)" strokeOpacity={0.5} vertical={false} />}
          <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: 'var(--color-text-secondary)', fontFamily: 'Geist Variable, sans-serif' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-secondary)', fontFamily: 'Geist Variable, sans-serif' }} axisLine={false} tickLine={false} tickFormatter={formatter} />
          <Tooltip content={<CustomTooltip formatter={formatter} />} />
          {showLegend && <Legend wrapperStyle={{ fontSize: 11, color: 'var(--color-text-secondary)' }} />}
          {lines.map((line, i) => {
            const color = line.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length]
            return (
              <Area key={line.key} type="monotone" dataKey={line.key} name={line.label ?? line.key}
                stroke={color} strokeWidth={line.strokeWidth ?? 2} strokeDasharray={line.dashed ? '4 4' : undefined}
                fill={`url(#gradient-${line.key})`} dot={false} activeDot={{ r: 4, strokeWidth: 0, fill: color }} />
            )
          })}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
