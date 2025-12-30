import { cn } from '@renderer/lib/utils'

interface KeyboardHintProps {
  keys: string[]
  description: string
  className?: string
}

/**
 * Display a keyboard shortcut hint
 * @example
 * <KeyboardHint keys={['Ctrl', 'K']} description="Search" />
 */
export function KeyboardHint({ keys, description, className }: KeyboardHintProps) {
  return (
    <div className={cn('flex items-center gap-2 text-sm', className)}>
      <div className="flex items-center gap-1">
        {keys.map((key) => (
          <span key={key}>
            <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
              {key}
            </kbd>
            {key !== keys[keys.length - 1] && (
              <span className="mx-0.5 text-muted-foreground">+</span>
            )}
          </span>
        ))}
      </div>
      <span className="text-muted-foreground">{description}</span>
    </div>
  )
}

interface KeyboardShortcutsHelpProps {
  className?: string
}

/**
 * Display all available keyboard shortcuts
 */
export function KeyboardShortcutsHelp({ className }: KeyboardShortcutsHelpProps) {
  const shortcuts = [
    { keys: ['←'], description: 'Previous image' },
    { keys: ['→'], description: 'Next image' },
    { keys: ['Home'], description: 'First image' },
    { keys: ['End'], description: 'Last image' },
    { keys: ['Esc'], description: 'Clear selection' },
  ]

  return (
    <div className={cn('space-y-2', className)}>
      <h3 className="text-sm font-semibold">Keyboard Shortcuts</h3>
      <div className="space-y-1.5">
        {shortcuts.map((shortcut) => (
          <KeyboardHint
            key={shortcut.keys.join('-')}
            keys={shortcut.keys}
            description={shortcut.description}
          />
        ))}
      </div>
    </div>
  )
}
