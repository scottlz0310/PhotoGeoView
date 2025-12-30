import { describe, expect, it } from 'vitest'
import { cn } from './utils'

describe('utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      expect(cn('c-1', 'c-2')).toBe('c-1 c-2')
    })

    it('should handle conditional classes', () => {
      expect(cn('c-1', 'c-2', false)).toBe('c-1 c-2')
    })

    it('should merge tailwind classes correctly', () => {
      expect(cn('p-4', 'p-2')).toBe('p-2')
      expect(cn('px-2 py-2', 'p-4')).toBe('p-4')
    })

    it('should handle arrays and objects', () => {
      expect(cn(['c-1', 'c-2'], { 'c-3': true, 'c-4': false })).toBe('c-1 c-2 c-3')
    })
  })
})
