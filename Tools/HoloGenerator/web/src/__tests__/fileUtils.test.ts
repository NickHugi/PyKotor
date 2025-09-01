import { 
  copyToClipboard, 
  downloadFile, 
  readFileAsText, 
  formatFileSize, 
  validateFileName,
  getFileExtension,
  removeFileExtension 
} from '../utils/fileUtils';

// Mock global objects
const mockClipboard = {
  writeText: jest.fn()
};

const mockDocument = {
  createElement: jest.fn(),
  body: {
    appendChild: jest.fn(),
    removeChild: jest.fn()
  },
  execCommand: jest.fn()
};

const mockURL = {
  createObjectURL: jest.fn(),
  revokeObjectURL: jest.fn()
};

// Setup global mocks
Object.defineProperty(global, 'navigator', {
  value: { clipboard: mockClipboard },
  writable: true
});

Object.defineProperty(global, 'document', {
  value: mockDocument,
  writable: true
});

Object.defineProperty(global, 'URL', {
  value: mockURL,
  writable: true
});

Object.defineProperty(global, 'window', {
  value: { isSecureContext: true },
  writable: true
});

describe('fileUtils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('copyToClipboard', () => {
    it('should copy text using clipboard API when available', async () => {
      mockClipboard.writeText.mockResolvedValue(undefined);
      
      const result = await copyToClipboard('test text');
      
      expect(result).toBe(true);
      expect(mockClipboard.writeText).toHaveBeenCalledWith('test text');
    });

    it('should fall back to execCommand when clipboard API fails', async () => {
      mockClipboard.writeText.mockRejectedValue(new Error('Not available'));
      
      const mockTextArea = {
        value: '',
        style: {},
        focus: jest.fn(),
        select: jest.fn()
      };
      
      mockDocument.createElement.mockReturnValue(mockTextArea);
      mockDocument.execCommand.mockReturnValue(true);
      
      const result = await copyToClipboard('test text');
      
      expect(result).toBe(true);
      expect(mockDocument.createElement).toHaveBeenCalledWith('textarea');
      expect(mockTextArea.value).toBe('test text');
      expect(mockDocument.execCommand).toHaveBeenCalledWith('copy');
    });

    it('should return false when all methods fail', async () => {
      mockClipboard.writeText.mockRejectedValue(new Error('Not available'));
      mockDocument.execCommand.mockReturnValue(false);
      
      const result = await copyToClipboard('test text');
      
      expect(result).toBe(false);
    });
  });

  describe('downloadFile', () => {
    it('should create and trigger download link', () => {
      const mockBlob = {};
      const mockLink = {
        href: '',
        download: '',
        style: { display: '' },
        click: jest.fn()
      };
      
      global.Blob = jest.fn(() => mockBlob) as any;
      mockURL.createObjectURL.mockReturnValue('blob:url');
      mockDocument.createElement.mockReturnValue(mockLink);
      
      downloadFile('test content', 'test.txt', 'text/plain');
      
      expect(global.Blob).toHaveBeenCalledWith(['test content'], { type: 'text/plain' });
      expect(mockURL.createObjectURL).toHaveBeenCalledWith(mockBlob);
      expect(mockLink.href).toBe('blob:url');
      expect(mockLink.download).toBe('test.txt');
      expect(mockLink.click).toHaveBeenCalled();
    });
  });

  describe('readFileAsText', () => {
    it('should read file content successfully', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      
      // Mock FileReader
      const mockReader = {
        onload: null as any,
        onerror: null as any,
        readAsText: jest.fn(),
        result: 'test content'
      };
      
      global.FileReader = jest.fn(() => mockReader) as any;
      
      const promise = readFileAsText(mockFile);
      
      // Simulate successful read
      mockReader.onload({ target: { result: 'test content' } });
      
      const result = await promise;
      expect(result).toBe('test content');
      expect(mockReader.readAsText).toHaveBeenCalledWith(mockFile);
    });

    it('should reject on file read error', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      
      const mockReader = {
        onload: null as any,
        onerror: null as any,
        readAsText: jest.fn()
      };
      
      global.FileReader = jest.fn(() => mockReader) as any;
      
      const promise = readFileAsText(mockFile);
      
      // Simulate error
      mockReader.onerror();
      
      await expect(promise).rejects.toThrow('Error reading file');
    });
  });

  describe('formatFileSize', () => {
    it('should format bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 B');
      expect(formatFileSize(512)).toBe('512 B');
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1536)).toBe('1.5 KB');
      expect(formatFileSize(1048576)).toBe('1 MB');
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });
  });

  describe('validateFileName', () => {
    it('should validate valid filenames', () => {
      expect(validateFileName('test.txt')).toBe(true);
      expect(validateFileName('my-file_name.ext')).toBe(true);
      expect(validateFileName('file with spaces.txt')).toBe(true);
    });

    it('should reject invalid filenames', () => {
      expect(validateFileName('')).toBe(false);
      expect(validateFileName('   ')).toBe(false);
      expect(validateFileName('file<name.txt')).toBe(false);
      expect(validateFileName('file>name.txt')).toBe(false);
      expect(validateFileName('file:name.txt')).toBe(false);
      expect(validateFileName('file"name.txt')).toBe(false);
      expect(validateFileName('file/name.txt')).toBe(false);
      expect(validateFileName('file\\name.txt')).toBe(false);
      expect(validateFileName('file|name.txt')).toBe(false);
      expect(validateFileName('file?name.txt')).toBe(false);
      expect(validateFileName('file*name.txt')).toBe(false);
    });
  });

  describe('getFileExtension', () => {
    it('should extract file extensions correctly', () => {
      expect(getFileExtension('test.txt')).toBe('txt');
      expect(getFileExtension('file.name.ext')).toBe('ext');
      expect(getFileExtension('Test.TXT')).toBe('txt');
      expect(getFileExtension('noextension')).toBe('');
      expect(getFileExtension('.hidden')).toBe('');
    });
  });

  describe('removeFileExtension', () => {
    it('should remove file extensions correctly', () => {
      expect(removeFileExtension('test.txt')).toBe('test');
      expect(removeFileExtension('file.name.ext')).toBe('file.name');
      expect(removeFileExtension('noextension')).toBe('noextension');
      expect(removeFileExtension('.hidden')).toBe('.hidden');
      expect(removeFileExtension('file.')).toBe('file');
    });
  });
});