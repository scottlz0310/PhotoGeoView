import { queryClient } from '@renderer/lib/queryClient'
import { describe, expect, it } from 'vitest'

describe('QueryClient', () => {
  it('should be properly configured', () => {
    expect(queryClient).toBeDefined()
    expect(queryClient.getDefaultOptions()).toBeDefined()
  })

  it('should have correct query default options', () => {
    const defaultOptions = queryClient.getDefaultOptions()

    expect(defaultOptions.queries?.staleTime).toBe(1000 * 60 * 5) // 5 minutes
    expect(defaultOptions.queries?.gcTime).toBe(1000 * 60 * 10) // 10 minutes
    expect(defaultOptions.queries?.retry).toBe(3)
    expect(defaultOptions.queries?.refetchOnWindowFocus).toBe(true)
    expect(defaultOptions.queries?.refetchOnMount).toBe(false)
  })

  it('should have correct mutation default options', () => {
    const defaultOptions = queryClient.getDefaultOptions()

    expect(defaultOptions.mutations?.retry).toBe(1)
  })

  it('should have retryDelay function', () => {
    const defaultOptions = queryClient.getDefaultOptions()

    expect(defaultOptions.queries?.retryDelay).toBeInstanceOf(Function)

    const retryDelay = defaultOptions.queries?.retryDelay as (attemptIndex: number) => number

    // Test exponential backoff
    expect(retryDelay(0)).toBe(1000) // 2^0 * 1000 = 1000ms
    expect(retryDelay(1)).toBe(2000) // 2^1 * 1000 = 2000ms
    expect(retryDelay(2)).toBe(4000) // 2^2 * 1000 = 4000ms
    expect(retryDelay(3)).toBe(8000) // 2^3 * 1000 = 8000ms

    // Test max cap at 30000ms
    expect(retryDelay(10)).toBe(30000) // 2^10 * 1000 = 1024000, capped at 30000
  })
})
