import { 
  generateDiffId, 
  detectFileType, 
  generateUnifiedDiff, 
  createDiffResult,
  generateChangesIni 
} from '../utils/diffUtils';
import { FileContent, DiffResult } from '../types';

describe('diffUtils', () => {
  describe('generateDiffId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateDiffId();
      const id2 = generateDiffId();
      
      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^diff_\d+_[a-z0-9]+$/);
    });
  });

  describe('detectFileType', () => {
    it('should detect INI files', () => {
      expect(detectFileType('test.ini', '[Settings]')).toBe('ini');
      expect(detectFileType('changes.txt', '[InstallList]')).toBe('ini');
    });

    it('should detect 2DA files', () => {
      expect(detectFileType('test.2da', '2DA V2.b')).toBe('2da');
      expect(detectFileType('appearance.2da', 'some content')).toBe('2da');
    });

    it('should detect TLK files', () => {
      expect(detectFileType('dialog.tlk', 'TLK Language: English')).toBe('tlk');
      expect(detectFileType('test.tlk', 'some content')).toBe('tlk');
    });

    it('should detect GFF files', () => {
      expect(detectFileType('test.utc', 'content')).toBe('gff');
      expect(detectFileType('test.dlg', 'content')).toBe('gff');
      expect(detectFileType('test.are', 'content')).toBe('gff');
    });

    it('should default to text for unknown types', () => {
      expect(detectFileType('unknown.xyz', 'content')).toBe('text');
      expect(detectFileType('readme.txt', 'content')).toBe('text');
    });
  });

  describe('generateUnifiedDiff', () => {
    it('should generate diff for different content', () => {
      const original = 'line1\nline2\nline3';
      const modified = 'line1\nmodified line2\nline3';
      
      const diff = generateUnifiedDiff(original, modified, 'test.txt');
      
      expect(diff).toContain('--- original/test.txt');
      expect(diff).toContain('+++ modified/test.txt');
      expect(diff).toContain('+modified line2');
      expect(diff).toContain('-line2');
    });

    it('should handle identical content', () => {
      const content = 'line1\nline2\nline3';
      
      const diff = generateUnifiedDiff(content, content, 'test.txt');
      
      expect(diff).toBe('No differences found');
    });

    it('should handle empty content', () => {
      const diff = generateUnifiedDiff('', 'new content', 'test.txt');
      
      expect(diff).toContain('+new content');
    });
  });

  describe('createDiffResult', () => {
    it('should create a complete diff result', () => {
      const originalFile: FileContent = {
        name: 'test.txt',
        content: 'original content',
        type: 'text'
      };
      
      const modifiedFile: FileContent = {
        name: 'test.txt',
        content: 'modified content',
        type: 'text'
      };
      
      const result = createDiffResult(originalFile, modifiedFile);
      
      expect(result.id).toBeDefined();
      expect(result.originalFile).toBe(originalFile);
      expect(result.modifiedFile).toBe(modifiedFile);
      expect(result.diffContent).toContain('original content');
      expect(result.diffContent).toContain('modified content');
      expect(result.timestamp).toBeInstanceOf(Date);
    });
  });

  describe('generateChangesIni', () => {
    it('should generate basic settings section', () => {
      const config = generateChangesIni([]);
      
      expect(config.sections).toHaveLength(1);
      expect(config.sections[0].name).toBe('Settings');
      expect(config.content).toContain('[Settings]');
      expect(config.content).toContain('WindowCaption=Generated Mod Configuration');
    });

    it('should handle GFF file diffs', () => {
      const diffResult: DiffResult = {
        id: 'test1',
        originalFile: { name: 'test.utc', content: 'old', type: 'gff' },
        modifiedFile: { name: 'test.utc', content: 'new', type: 'gff' },
        diffContent: 'diff content',
        timestamp: new Date()
      };
      
      const config = generateChangesIni([diffResult]);
      
      expect(config.sections.some(s => s.name === 'GFFList')).toBe(true);
      expect(config.content).toContain('[GFFList]');
      expect(config.content).toContain('File1=test.utc');
    });

    it('should handle 2DA file diffs', () => {
      const diffResult: DiffResult = {
        id: 'test2',
        originalFile: { name: 'test.2da', content: 'old', type: '2da' },
        modifiedFile: { name: 'test.2da', content: 'new', type: '2da' },
        diffContent: 'diff content',
        timestamp: new Date()
      };
      
      const config = generateChangesIni([diffResult]);
      
      expect(config.sections.some(s => s.name === '2DAList')).toBe(true);
      expect(config.content).toContain('[2DAList]');
      expect(config.content).toContain('File1=test.2da');
    });

    it('should handle TLK file diffs', () => {
      const diffResult: DiffResult = {
        id: 'test3',
        originalFile: { name: 'dialog.tlk', content: 'old', type: 'tlk' },
        modifiedFile: { name: 'dialog.tlk', content: 'new', type: 'tlk' },
        diffContent: '+Entry 42: Modified text\n+Entry 100: Another change',
        timestamp: new Date()
      };
      
      const config = generateChangesIni([diffResult]);
      
      expect(config.sections.some(s => s.name === 'TLKList')).toBe(true);
      expect(config.content).toContain('[TLKList]');
      expect(config.content).toContain('StrRef42=Modified');
      expect(config.content).toContain('StrRef100=Modified');
    });

    it('should handle install files', () => {
      const diffResult: DiffResult = {
        id: 'test4',
        originalFile: { name: 'test.txt', content: 'old', type: 'text' },
        modifiedFile: { name: 'test.txt', content: 'new', type: 'text' },
        diffContent: 'diff content',
        timestamp: new Date()
      };
      
      const config = generateChangesIni([diffResult]);
      
      expect(config.sections.some(s => s.name === 'InstallList')).toBe(true);
      expect(config.sections.some(s => s.name === 'Override')).toBe(true);
      expect(config.content).toContain('[InstallList]');
      expect(config.content).toContain('File1=Override');
      expect(config.content).toContain('[Override]');
      expect(config.content).toContain('File1=test.txt');
    });

    it('should handle multiple diffs', () => {
      const diffs: DiffResult[] = [
        {
          id: 'test1',
          originalFile: { name: 'test.gff', content: 'old', type: 'gff' },
          modifiedFile: { name: 'test.gff', content: 'new', type: 'gff' },
          diffContent: 'diff content',
          timestamp: new Date()
        },
        {
          id: 'test2',
          originalFile: { name: 'test.2da', content: 'old', type: '2da' },
          modifiedFile: { name: 'test.2da', content: 'new', type: '2da' },
          diffContent: 'diff content',
          timestamp: new Date()
        }
      ];
      
      const config = generateChangesIni(diffs);
      
      expect(config.sections.some(s => s.name === 'GFFList')).toBe(true);
      expect(config.sections.some(s => s.name === '2DAList')).toBe(true);
      expect(config.content).toContain('[GFFList]');
      expect(config.content).toContain('[2DAList]');
    });
  });
});