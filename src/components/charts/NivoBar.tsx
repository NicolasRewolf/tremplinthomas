import { ResponsiveBar } from '@nivo/bar'
import type { BarDatum, BarSvgProps } from '@nivo/bar'
import { nivoTheme, nivoColors } from '@/lib/nivo-theme'
import { cn } from '@/lib/utils'

interface NivoBarProps<D extends BarDatum = BarDatum>
  extends Partial<Omit<BarSvgProps<D>, 'data' | 'width' | 'height'>> {
  data: D[]
  keys: string[]
  indexBy: string
  height?: number
  className?: string
  layout?: 'horizontal' | 'vertical'
}

export function NivoBar<D extends BarDatum = BarDatum>({ data, keys, indexBy, height = 320, className, layout = 'vertical', ...props }: NivoBarProps<D>) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveBar data={data} keys={keys} indexBy={indexBy} theme={nivoTheme}
        colors={nivoColors.slice(0, keys.length)} layout={layout}
        margin={{ top: 20, right: 20, bottom: 50, left: 60 }} padding={0.3} borderRadius={4}
        axisBottom={{ tickSize: 0, tickPadding: 8 }} axisLeft={{ tickSize: 0, tickPadding: 8 }}
        enableGridX={false} enableLabel={false} animate motionConfig="gentle" {...props} />
    </div>
  )
}
