import { describe, expect, it } from 'vitest'

import { formatDate, formatDuration, formatSize, getReportTitle } from './reports'
import type { Report } from '../types/reports'

describe('formatDate', () => {
  it('returns placeholder for null or invalid values', () => {
    expect(formatDate(null)).toBe('-')
    expect(formatDate('not-a-date')).toBe('-')
  })

  it('formats valid dates', () => {
    expect(formatDate('2024-03-05T10:20:00')).toMatch(/2024/)
  })
})

describe('formatSize', () => {
  it('formats zero bytes', () => {
    expect(formatSize(0)).toBe('0 B')
  })

  it('scales to larger units', () => {
    expect(formatSize(2048)).toBe('2.0 KB')
    expect(formatSize(5 * 1024 * 1024)).toBe('5.0 MB')
  })
})

describe('formatDuration', () => {
  it('returns placeholder for missing values', () => {
    expect(formatDuration(null)).toBe('-')
    expect(formatDuration(undefined)).toBe('-')
  })

  it('formats hours, minutes and seconds', () => {
    expect(formatDuration(0)).toBe('00:00:00')
    expect(formatDuration(61_000)).toBe('00:01:01')
    expect(formatDuration(3_661_000)).toBe('01:01:01')
  })
})

describe('getReportTitle', () => {
  const base: Report = {
    id: 'report-id',
    name: '',
    created_at: '2024-03-05T10:20:00',
    size: 0,
    entry_path: null,
  }

  it('prefers explicit name', () => {
    expect(getReportTitle({ ...base, name: 'Nightly' })).toBe('Nightly')
  })

  it('falls back to entry path tail', () => {
    expect(getReportTitle({ ...base, entry_path: 'runs/2024-03-05/index.html' })).toBe('index.html')
  })

  it('falls back to id', () => {
    expect(getReportTitle(base)).toBe('report-id')
  })
})
