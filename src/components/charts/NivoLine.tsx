import { ResponsiveLine } from '@nivo/line'
import type { LineSeries, LineSvgProps } from '@nivo/line'
import { nivoTheme, nivoColors } from '@/lib/nivo-theme'
import { cn } from '@/lib/utils'

interface NivoLineProps extends Partial<Omit<LineSvgProps<LineSeries>, 'data' | 'width' | 'height'>> {
  data: LineSvgProps<LineSeries>['data']
  height?: number
  className?: string
  area?: boolean
}

export function NivoLine({ data, height = 320, className, area = false, ...props }: NivoLineProps) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveLine data={data} theme={nivoTheme} colors={nivoColors.slice(0, data.length)}
        margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
        xScale={{ type: 'point' }} yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false }}
        curve="monotoneX" axisBottom={{ tickSize: 0, tickPadding: 8 }} axisLeft={{ tickSize: 0, tickPadding: 8 }}
        enableGridX={false} lineWidth={2} enablePoints pointSize={6} pointBorderWidth={2}
        pointBorderColor={{ from: 'serieColor' }} pointColor="var(--color-surface)"
        enableArea={area} areaOpacity={0.1} enableSlices="x" animate motionConfig="gentle" {...props} />
    </div>
  )
}
