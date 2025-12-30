import { FileFilters } from '@renderer/components/filters/FileFilters'
import { useAppStore } from '@renderer/stores/appStore'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'

describe('FileFilters', () => {
  beforeEach(() => {
    // Reset store before each test
    useAppStore.setState({
      filters: {
        dateFrom: null,
        dateTo: null,
        hasGPS: null,
        cameraModels: [],
      },
    })
  })

  describe('Filter Button Display', () => {
    it('should render filter button', () => {
      render(<FileFilters availableCameraModels={[]} />)

      expect(screen.getByText('Filters')).toBeInTheDocument()
    })

    it('should not show active filter count when no filters are active', () => {
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      expect(filterButton).not.toHaveTextContent(/\d/)
    })

    it('should show active filter count when date filter is active', () => {
      useAppStore.setState({
        filters: {
          dateFrom: new Date('2024-01-01'),
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        },
      })

      render(<FileFilters availableCameraModels={[]} />)

      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('should show active filter count when GPS filter is active', () => {
      useAppStore.setState({
        filters: {
          dateFrom: null,
          dateTo: null,
          hasGPS: true,
          cameraModels: [],
        },
      })

      render(<FileFilters availableCameraModels={[]} />)

      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('should show active filter count when camera models are selected', () => {
      useAppStore.setState({
        filters: {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: ['Canon EOS R5', 'Sony A7 III'],
        },
      })

      render(<FileFilters availableCameraModels={['Canon EOS R5', 'Sony A7 III']} />)

      expect(screen.getByText('1')).toBeInTheDocument() // Camera filter counts as 1
    })

    it('should show total active filter count when multiple filters are active', () => {
      useAppStore.setState({
        filters: {
          dateFrom: new Date('2024-01-01'),
          dateTo: new Date('2024-12-31'),
          hasGPS: true,
          cameraModels: ['Canon EOS R5'],
        },
      })

      render(<FileFilters availableCameraModels={['Canon EOS R5']} />)

      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('should display active filter count text below button', () => {
      useAppStore.setState({
        filters: {
          dateFrom: new Date('2024-01-01'),
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        },
      })

      render(<FileFilters availableCameraModels={[]} />)

      expect(screen.getByText('1 filter active')).toBeInTheDocument()
    })

    it('should display plural form for multiple filters', () => {
      useAppStore.setState({
        filters: {
          dateFrom: new Date('2024-01-01'),
          dateTo: null,
          hasGPS: true,
          cameraModels: [],
        },
      })

      render(<FileFilters availableCameraModels={[]} />)

      expect(screen.getByText('2 filters active')).toBeInTheDocument()
    })
  })

  describe('Date Range Filter', () => {
    it('should display date range inputs when menu is opened', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      expect(screen.getByText('Date Range')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('From date')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('To date')).toBeInTheDocument()
    })

    it('should update store when "from" date is changed', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const fromDateInput = screen.getByPlaceholderText('From date')
      await user.type(fromDateInput, '2024-01-15')

      const state = useAppStore.getState()
      expect(state.filters.dateFrom).toBeInstanceOf(Date)
    })

    it('should update store when "to" date is changed', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const toDateInput = screen.getByPlaceholderText('To date')
      await user.type(toDateInput, '2024-12-31')

      const state = useAppStore.getState()
      expect(state.filters.dateTo).toBeInstanceOf(Date)
    })
  })

  describe('GPS Filter', () => {
    it('should display GPS filter options when menu is opened', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      expect(screen.getByText('GPS Location')).toBeInTheDocument()
      expect(screen.getByLabelText('All photos')).toBeInTheDocument()
      expect(screen.getByLabelText('With GPS data')).toBeInTheDocument()
      expect(screen.getByLabelText('Without GPS data')).toBeInTheDocument()
    })

    it('should check "All photos" by default', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const allPhotosCheckbox = screen.getByLabelText('All photos')
      expect(allPhotosCheckbox).toBeChecked()
    })

    it('should update store when "With GPS data" is selected', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const withGPSCheckbox = screen.getByLabelText('With GPS data')
      await user.click(withGPSCheckbox)

      const state = useAppStore.getState()
      expect(state.filters.hasGPS).toBe(true)
    })

    it('should update store when "Without GPS data" is selected', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const withoutGPSCheckbox = screen.getByLabelText('Without GPS data')
      await user.click(withoutGPSCheckbox)

      const state = useAppStore.getState()
      expect(state.filters.hasGPS).toBe(false)
    })

    it('should reset GPS filter when "All photos" is selected', async () => {
      const user = userEvent.setup()
      useAppStore.setState({
        filters: {
          dateFrom: null,
          dateTo: null,
          hasGPS: true,
          cameraModels: [],
        },
      })

      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const allPhotosCheckbox = screen.getByLabelText('All photos')
      await user.click(allPhotosCheckbox)

      const state = useAppStore.getState()
      expect(state.filters.hasGPS).toBe(null)
    })
  })

  describe('Camera Model Filter', () => {
    const mockCameraModels = ['Canon EOS R5', 'Sony A7 III', 'Nikon Z6']

    it('should not display camera model section when no models are available', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      expect(screen.queryByText('Camera Model')).not.toBeInTheDocument()
    })

    it('should display camera model section when models are available', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={mockCameraModels} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      expect(screen.getByText('Camera Model')).toBeInTheDocument()
    })

    it('should display all available camera models', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={mockCameraModels} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      for (const model of mockCameraModels) {
        expect(screen.getByText(model)).toBeInTheDocument()
      }
    })

    it('should toggle camera model selection when clicked', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={mockCameraModels} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const canonOption = screen.getByText('Canon EOS R5')
      await user.click(canonOption)

      // Wait a bit for the state to update
      await new Promise((resolve) => setTimeout(resolve, 50))

      const state = useAppStore.getState()
      expect(state.filters.cameraModels).toContain('Canon EOS R5')
    })

    it('should allow selecting multiple camera models via store', () => {
      // Test store directly as UI behavior is complex with dropdown menus
      const { toggleCameraModel } = useAppStore.getState()

      toggleCameraModel('Canon EOS R5')
      toggleCameraModel('Sony A7 III')

      const state = useAppStore.getState()
      expect(state.filters.cameraModels).toContain('Canon EOS R5')
      expect(state.filters.cameraModels).toContain('Sony A7 III')
      expect(state.filters.cameraModels).toHaveLength(2)
    })

    it('should deselect camera model when clicked again', async () => {
      const user = userEvent.setup()
      useAppStore.setState({
        filters: {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: ['Canon EOS R5'],
        },
      })

      render(<FileFilters availableCameraModels={mockCameraModels} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const canonOption = screen.getByText('Canon EOS R5')
      await user.click(canonOption)

      // Wait a bit for the state to update
      await new Promise((resolve) => setTimeout(resolve, 50))

      const state = useAppStore.getState()
      expect(state.filters.cameraModels).not.toContain('Canon EOS R5')
      expect(state.filters.cameraModels).toHaveLength(0)
    })
  })

  describe('Reset Filters', () => {
    it('should display reset button', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      expect(screen.getByText('Reset Filters')).toBeInTheDocument()
    })

    it('should disable reset button when no filters are active', async () => {
      const user = userEvent.setup()
      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const resetButton = screen.getByRole('button', { name: /Reset Filters/i })
      expect(resetButton).toBeDisabled()
    })

    it('should enable reset button when filters are active', async () => {
      const user = userEvent.setup()
      useAppStore.setState({
        filters: {
          dateFrom: new Date('2024-01-01'),
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        },
      })

      render(<FileFilters availableCameraModels={[]} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const resetButton = screen.getByRole('button', { name: /Reset Filters/i })
      expect(resetButton).not.toBeDisabled()
    })

    it('should clear all filters when reset button is clicked', async () => {
      const user = userEvent.setup()
      useAppStore.setState({
        filters: {
          dateFrom: new Date('2024-01-01'),
          dateTo: new Date('2024-12-31'),
          hasGPS: true,
          cameraModels: ['Canon EOS R5'],
        },
      })

      render(<FileFilters availableCameraModels={['Canon EOS R5']} />)

      const filterButton = screen.getByRole('button', { name: /Filters/i })
      await user.click(filterButton)

      const resetButton = screen.getByRole('button', { name: /Reset Filters/i })
      await user.click(resetButton)

      const state = useAppStore.getState()
      expect(state.filters.dateFrom).toBe(null)
      expect(state.filters.dateTo).toBe(null)
      expect(state.filters.hasGPS).toBe(null)
      expect(state.filters.cameraModels).toHaveLength(0)
    })
  })
})
