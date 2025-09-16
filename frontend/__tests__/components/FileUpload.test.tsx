import { render, screen, fireEvent } from '@testing-library/react'
import FileUpload from '@/components/FileUpload'

describe('FileUpload Component', () => {
  const mockOnFilesAdded = jest.fn()

  beforeEach(() => {
    mockOnFilesAdded.mockClear()
  })

  it('renders file upload area', () => {
    render(<FileUpload onFilesAdded={mockOnFilesAdded} />)
    
    expect(screen.getByText(/ここにファイルをドラッグ＆ドロップするか/)).toBeInTheDocument()
    expect(screen.getByText(/対応ファイル: .xlsx, .xls/)).toBeInTheDocument()
  })

  it('handles file selection via input', () => {
    render(<FileUpload onFilesAdded={mockOnFilesAdded} />)
    
    const fileInput = document.getElementById('fileInput') as HTMLInputElement
    const testFile = new File(['test content'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })

    Object.defineProperty(fileInput, 'files', {
      value: [testFile],
      writable: false,
    })

    fireEvent.change(fileInput)
    
    expect(mockOnFilesAdded).toHaveBeenCalledWith([testFile])
  })

  it('handles drag and drop', () => {
    render(<FileUpload onFilesAdded={mockOnFilesAdded} />)
    
    const dropArea = screen.getByText(/ここにファイルをドラッグ＆ドロップするか/).parentElement
    const testFile = new File(['test content'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })

    const dropEvent = new Event('drop', { bubbles: true })
    Object.defineProperty(dropEvent, 'dataTransfer', {
      value: {
        files: [testFile]
      }
    })

    fireEvent(dropArea!, dropEvent)
    
    expect(mockOnFilesAdded).toHaveBeenCalledWith([testFile])
  })

  it('prevents default behavior on drag over', () => {
    render(<FileUpload onFilesAdded={mockOnFilesAdded} />)
    
    const dropArea = screen.getByText(/ここにファイルをドラッグ＆ドロップするか/).parentElement
    const dragOverEvent = new Event('dragover', { bubbles: true })
    const preventDefaultSpy = jest.spyOn(dragOverEvent, 'preventDefault')

    fireEvent(dropArea!, dragOverEvent)
    
    expect(preventDefaultSpy).toHaveBeenCalled()
  })

  it('opens file dialog when clicked', () => {
    render(<FileUpload onFilesAdded={mockOnFilesAdded} />)
    
    const dropArea = screen.getByText(/ここにファイルをドラッグ＆ドロップするか/).parentElement
    const fileInput = document.getElementById('fileInput') as HTMLInputElement
    const clickSpy = jest.spyOn(fileInput, 'click').mockImplementation()

    fireEvent.click(dropArea!)
    
    expect(clickSpy).toHaveBeenCalled()
    
    clickSpy.mockRestore()
  })
})