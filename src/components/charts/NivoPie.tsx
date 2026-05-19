import { ResponsivePie } from '@nivo/pie'
import type { PieSvgProps } from '@nivo/pie'
import { nivoTheme, nivoColors } from '@/lib/nivo-theme'
import { cn } from '@/lib/utils'

type PieDatum = { id: string; value: number; label?: string }

interface NivoPieProps extends Partial<Omit<PieSvgProps<PieDatum>, 'data' | 'width' | 'height'>> {
  data: PieDatum[]
  height?: number
  className?: string
  donut?: boolean
}

export function NivoPie({ data, height = 280, className, donut = true, ...props }: NivoPieProps) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsivePie data={data} theme={nivoTheme} colors={nivoColors.slice(0, data.length)}
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        innerRadius={donut ? 0.6 : 0} padAngle={0.5} cornerRadius={3} activeOuterRadiusOffset={4}
        borderWidth={0} arcLinkLabelsSkipAngle={10} arcLinkLabelsTextColor="var(--color-text-secondary)"
        arcLinkLabelsThickness={1} arcLinkLabelsColor={{ from: 'color' }} arcLabelsSkipAngle={10}
        arcLabelsTextColor="var(--color-surface)" animate motionConfig="gentle" {...props} />
    </div>
  )
}
