import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts'
import { cn } from '@/lib/utils'

interface BarConfig { key: string; label?: string; color?: string; radius?: number }

interface BarChartCardProps {
  data: Record<string, unknown>[]
  xKey: string
  bars: BarConfig[]
  height?: number
  className?: string
  showGrid?: boolean
  showLegend?: boolean
  layout?: 'vertical' | 'horizontal'
  formatter?: (value: number) => string
  highlightLast?: boolean
}

function CustomTooltip({ active, payload, label, formatter }: {
  active?: boolean; payload?: { color: string; name: string; value: number }[]; label?: string; formatter?: (value: number) => string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-[var(--radius-md)] border px-3 py-2 text-xs shadow-md"
      style={{ background: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text-primary)', fontFamily: 'Geist Variable, sans-serif' }}>
      <p className="mb-1 font-medium" style={{ color: 'var(--color-text-secondary)' }}>{label}</p>
      {payload.map((e) => <p key={e.name} style={{ color: e.color }}>{e.name} : {formatter ? formatter(e.value) : e.value}</p>)}
    </div>
  )
}

const DEFAULT_COLORS = ['var(--color-accent)', '#6B6860', '#B5B0A8', '#8B5CF6']

export function BarChartCard({ data, xKey, bars, height = 240, className, showGrid = true, showLegend = false, layout = 'horizontal', formatter, highlightLast = false }: BarChartCardProps) {
  const lastIndex = data.length - 1
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout={layout} margin={{ top: 8, right: 8, left: layout === 'vertical' ? 80 : -16, bottom: 0 }}>
          {showGrid && <CartesianGrid strokeDasharray="0" stroke="var(--color-border)" strokeOpacity={0.5} vertical={false} />}
          {layout === 'horizontal' ? (
            <>
              <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} tickFormatter={formatter} />
            </>
          ) : (
            <>
              <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} tickFormatter={formatter} />
              <YAxis dataKey={xKey} type="category" tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} width={80} />
            </>
          )}
          <Tooltip content={<CustomTooltip formatter={formatter} />} cursor={{ fill: 'var(--color-border)', fillOpacity: 0.3 }} />
          {showLegend && <Legend wrapperStyle={{ fontSize: 11 }} />}
          {bars.map((bar, i) => {
            const color = bar.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length]
            return (
              <Bar key={bar.key} dataKey={bar.key} name={bar.label ?? bar.key} fill={color} radius={bar.radius ?? 4}>
                {highlightLast && data.map((_, idx) => <Cell key={`cell-${idx}`} fill={idx === lastIndex ? color : `${color}60`} />)}
              </Bar>
            )
          })}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
