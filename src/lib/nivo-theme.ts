/**
 * nivo-theme.ts
 * Theme Nivo synchronisé avec les design tokens REWOLF.
 * Usage : import { nivoTheme } from '@/lib/nivo-theme'
 */

import type { PartialTheme } from '@nivo/theming'

function cssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

export const nivoTheme: PartialTheme = {
  background: 'transparent',
  text: {
    fontSize: 12,
    fill: cssVar('--color-text-secondary', '#6B6860'),
    fontFamily: 'Geist Variable, sans-serif',
  },
  axis: {
    domain: { line: { stroke: cssVar('--color-border', '#E2DED7'), strokeWidth: 1 } },
    legend: { text: { fontSize: 11, fill: cssVar('--color-text-secondary', '#6B6860'), fontFamily: 'Geist Variable, sans-serif' } },
    ticks: {
      line: { stroke: cssVar('--color-border', '#E2DED7'), strokeWidth: 1 },
      text: { fontSize: 11, fill: cssVar('--color-text-secondary', '#6B6860'), fontFamily: 'Geist Variable, sans-serif' },
    },
  },
  grid: { line: { stroke: cssVar('--color-border', '#E2DED7'), strokeWidth: 1, strokeOpacity: 0.5 } },
  legends: {
    text: { fontSize: 11, fill: cssVar('--color-text-secondary', '#6B6860'), fontFamily: 'Geist Variable, sans-serif' },
    ticks: { text: { fontSize: 11, fill: cssVar('--color-text-secondary', '#6B6860') } },
  },
  tooltip: {
    container: {
      background: cssVar('--color-surface', '#FFFFFF'),
      border: `1px solid ${cssVar('--color-border', '#E2DED7')}`,
      borderRadius: '8px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      color: cssVar('--color-text-primary', '#111110'),
      fontSize: 12,
      fontFamily: 'Geist Variable, sans-serif',
      padding: '8px 12px',
    },
  },
  crosshair: {
    line: { stroke: cssVar('--color-accent', '#1A1916'), strokeWidth: 1, strokeOpacity: 0.3, strokeDasharray: '4 4' },
  },
  annotations: {
    text: { fontSize: 11, fill: cssVar('--color-text-primary', '#111110'), outlineWidth: 2, outlineColor: cssVar('--color-surface', '#FFFFFF') },
    link: { stroke: cssVar('--color-accent', '#1A1916'), strokeWidth: 1 },
    outline: { fill: 'none', stroke: cssVar('--color-accent', '#1A1916'), strokeWidth: 2 },
    symbol: { fill: cssVar('--color-accent', '#1A1916'), outlineWidth: 2, outlineColor: cssVar('--color-surface', '#FFFFFF') },
  },
}

export const nivoColors = [
  '#1A1916',
  '#6B6860',
  '#B5B0A8',
  '#D4CFC7',
  '#8B5CF6',
  '#10B981',
  '#F59E0B',
  '#EF4444',
]
