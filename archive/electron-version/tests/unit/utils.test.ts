import { cn } from '@renderer/lib/utils'
import { describe, expect, it } from 'vitest'

describe('Utils', () => {
  describe('cn (class name utility)', () => {
    it('should merge class names correctly', () => {
      expect(cn('foo', 'bar')).toBe('foo bar')
    })

    it('should handle conditional classes', () => {
      expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz')
    })

    it('should handle undefined and null', () => {
      expect(cn('foo', null, undefined, 'bar')).toBe('foo bar')
    })

    it('should merge tailwind classes correctly', () => {
      expect(cn('px-4 py-2', 'px-2')).toBe('py-2 px-2')
    })
  })
})
