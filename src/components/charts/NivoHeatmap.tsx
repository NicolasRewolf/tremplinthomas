import { ResponsiveHeatMap } from '@nivo/heatmap'
import type { HeatMapSvgProps, DefaultHeatMapDatum, HeatMapDatum } from '@nivo/heatmap'
import { nivoTheme } from '@/lib/nivo-theme'
import { cn } from '@/lib/utils'

interface NivoHeatmapProps<D extends HeatMapDatum = DefaultHeatMapDatum, E extends object = Record<string, never>>
  extends Partial<Omit<HeatMapSvgProps<D, E>, 'data' | 'width' | 'height'>> {
  data: HeatMapSvgProps<D, E>['data']
  height?: number
  className?: string
}

export function NivoHeatmap<D extends HeatMapDatum = DefaultHeatMapDatum, E extends object = Record<string, never>>({ data, height = 320, className, ...props }: NivoHeatmapProps<D, E>) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveHeatMap data={data} theme={nivoTheme}
        margin={{ top: 20, right: 20, bottom: 60, left: 80 }} axisTop={null}
        axisBottom={{ tickSize: 0, tickPadding: 8, tickRotation: -45 }} axisLeft={{ tickSize: 0, tickPadding: 8 }}
        colors={{ type: 'sequential', scheme: 'greys', minValue: 0 }}
        emptyColor="var(--color-canvas)" borderWidth={2} borderColor="var(--color-surface)"
        animate motionConfig="gentle" {...props} />
    </div>
  )
}
