/**
 * Shared number/amount formatting helpers.
 *
 * Per the number-formatting rule, every displayed number/amount must go through
 * these helpers — never render raw numbers or hand-rolled separators.
 */

const DEFAULT_LOCALE = 'en-US';

export function formatNumber(value: number, fractionDigits = 0): string {
  return new Intl.NumberFormat(DEFAULT_LOCALE, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function formatPercent(value: number, fractionDigits = 0): string {
  return new Intl.NumberFormat(DEFAULT_LOCALE, {
    style: 'percent',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat(DEFAULT_LOCALE, { style: 'currency', currency }).format(value);
}
