import { Button } from '@renderer/components/ui/button'
import { Checkbox } from '@renderer/components/ui/checkbox'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@renderer/components/ui/dropdown-menu'
import { Input } from '@renderer/components/ui/input'
import { useAppStore } from '@renderer/stores/appStore'
import { Filter, X } from 'lucide-react'
import { useMemo, useState } from 'react'

interface FileFiltersProps {
  availableCameraModels: string[]
}

export function FileFilters({ availableCameraModels }: FileFiltersProps) {
  const { filters, setDateFilter, setGPSFilter, toggleCameraModel, resetFilters } = useAppStore()
  const [dateFromStr, setDateFromStr] = useState('')
  const [dateToStr, setDateToStr] = useState('')

  const activeFilterCount = useMemo(() => {
    let count = 0
    if (filters.dateFrom || filters.dateTo) count++
    if (filters.hasGPS !== null) count++
    if (filters.cameraModels.length > 0) count++
    return count
  }, [filters])

  const handleDateFromChange = (value: string) => {
    setDateFromStr(value)
    const date = value ? new Date(value) : null
    setDateFilter(date, filters.dateTo)
  }

  const handleDateToChange = (value: string) => {
    setDateToStr(value)
    const date = value ? new Date(value) : null
    setDateFilter(filters.dateFrom, date)
  }

  const handleResetFilters = () => {
    resetFilters()
    setDateFromStr('')
    setDateToStr('')
  }

  return (
    <div className="flex items-center gap-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Filter className="h-4 w-4" />
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-1 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                {activeFilterCount}
              </span>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-80" align="start">
          <DropdownMenuLabel>Filter Options</DropdownMenuLabel>
          <DropdownMenuSeparator />

          {/* Date Range Filter */}
          <div className="p-2 space-y-2">
            <div className="text-sm font-medium">Date Range</div>
            <div className="grid gap-2">
              <Input
                type="date"
                value={dateFromStr}
                onChange={(e) => handleDateFromChange(e.target.value)}
                placeholder="From date"
              />
              <Input
                type="date"
                value={dateToStr}
                onChange={(e) => handleDateToChange(e.target.value)}
                placeholder="To date"
              />
            </div>
          </div>

          <DropdownMenuSeparator />

          {/* GPS Filter */}
          <div className="p-2 space-y-2">
            <div className="text-sm font-medium">GPS Location</div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="filter-all-gps"
                  checked={filters.hasGPS === null}
                  onCheckedChange={() => setGPSFilter(null)}
                />
                <label
                  htmlFor="filter-all-gps"
                  className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  All photos
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="filter-with-gps"
                  checked={filters.hasGPS === true}
                  onCheckedChange={() => setGPSFilter(true)}
                />
                <label
                  htmlFor="filter-with-gps"
                  className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  With GPS data
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="filter-without-gps"
                  checked={filters.hasGPS === false}
                  onCheckedChange={() => setGPSFilter(false)}
                />
                <label
                  htmlFor="filter-without-gps"
                  className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Without GPS data
                </label>
              </div>
            </div>
          </div>

          <DropdownMenuSeparator />

          {/* Camera Model Filter */}
          {availableCameraModels.length > 0 && (
            <>
              <div className="p-2">
                <div className="text-sm font-medium mb-2">Camera Model</div>
                <div className="max-h-40 overflow-y-auto space-y-1">
                  {availableCameraModels.map((model) => (
                    <DropdownMenuCheckboxItem
                      key={model}
                      checked={filters.cameraModels.includes(model)}
                      onCheckedChange={() => toggleCameraModel(model)}
                    >
                      {model}
                    </DropdownMenuCheckboxItem>
                  ))}
                </div>
              </div>
              <DropdownMenuSeparator />
            </>
          )}

          {/* Reset Button */}
          <div className="p-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full gap-2"
              onClick={handleResetFilters}
              disabled={activeFilterCount === 0}
            >
              <X className="h-4 w-4" />
              Reset Filters
            </Button>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>

      {activeFilterCount > 0 && (
        <span className="text-sm text-muted-foreground">
          {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} active
        </span>
      )}
    </div>
  )
}
