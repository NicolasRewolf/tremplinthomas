/**
 * format.ts
 * Helpers de formatage — toujours utiliser ces fonctions, jamais de formatage inline.
 * Usage : import { formatCurrency, formatNumber, formatPercent } from '@/lib/format'
 */

import numeral from 'numeral'

export function formatCurrency(value: number, symbol = '€'): string {
  return `${numeral(value).format('0,0')} ${symbol}`
}

export function formatCurrencyFull(value: number, symbol = '€'): string {
  return `${numeral(value).format('0,0.00')} ${symbol}`
}

export function formatNumber(value: number): string {
  return numeral(value).format('0,0')
}

export function formatCompact(value: number): string {
  return numeral(value).format('0.[0]a').toUpperCase()
}

export function formatPercent(value: number, decimals = 1): string {
  return numeral(value).format(`0.[${'0'.repeat(decimals)}]`) + '%'
}

export function formatPercentSigned(value: number, decimals = 1): string {
  const formatted = numeral(Math.abs(value)).format(`0.${'0'.repeat(decimals)}`)
  return `${value >= 0 ? '+' : '-'}${formatted}%`
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export type Trend = 'up' | 'down' | 'neutral'

export function getTrend(value: number, positiveIsGood = true): Trend {
  if (value === 0) return 'neutral'
  if (value > 0) return positiveIsGood ? 'up' : 'down'
  return positiveIsGood ? 'down' : 'up'
}
