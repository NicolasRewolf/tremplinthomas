import { ResponsiveTreeMap } from '@nivo/treemap'
import type { TreeMapSvgProps, DefaultTreeMapDatum } from '@nivo/treemap'
import { nivoTheme, nivoColors } from '@/lib/nivo-theme'
import { cn } from '@/lib/utils'

interface NivoTreemapProps<D extends object = DefaultTreeMapDatum>
  extends Partial<Omit<TreeMapSvgProps<D>, 'data' | 'width' | 'height'>> {
  data: TreeMapSvgProps<D>['data']
  height?: number
  className?: string
}

export function NivoTreemap<D extends object = DefaultTreeMapDatum>({ data, height = 320, className, ...props }: NivoTreemapProps<D>) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveTreeMap data={data} theme={nivoTheme} colors={nivoColors}
        margin={{ top: 4, right: 4, bottom: 4, left: 4 }}
        identity="name" value="value" valueFormat=".02s" tile="squarify"
        leavesOnly={false} innerPadding={3} outerPadding={3} borderWidth={0}
        labelSkipSize={24} labelTextColor="var(--color-surface)" parentLabelTextColor="var(--color-surface)"
        animate motionConfig="gentle" {...props} />
    </div>
  )
}
