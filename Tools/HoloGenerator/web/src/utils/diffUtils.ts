import { FileContent, DiffResult, GeneratedConfig } from '../types';
import { diffLines, diffWords, Change } from 'diff';

export const generateDiffId = (): string => {
  return `diff_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const detectFileType = (filename: string, content: string): FileContent['type'] => {
  const ext = filename.toLowerCase().split('.').pop();
  
  if (ext === 'ini' || content.includes('[Settings]') || content.includes('[InstallList]')) {
    return 'ini';
  }
  
  if (ext === '2da' || content.startsWith('2DA V2.b')) {
    return '2da';
  }
  
  if (ext === 'tlk' || content.includes('TLK Language:')) {
    return 'tlk';
  }
  
  if (ext === 'ssf') {
    return 'ssf';
  }
  
  if (ext === 'lip') {
    return 'lip';
  }
  
  // Check if it looks like GFF (simplified check)
  if (['utc', 'uti', 'dlg', 'are', 'git', 'ifo', 'jrl', 'gff'].includes(ext || '')) {
    return 'gff';
  }
  
  return 'text';
};

export const generateUnifiedDiff = (original: string, modified: string, filename: string): string => {
  const changes = diffLines(original, modified);
  
  if (changes.length === 1 && !changes[0].added && !changes[0].removed) {
    return 'No differences found';
  }
  
  let result = `--- original/${filename}\n+++ modified/${filename}\n`;
  let originalLineNum = 1;
  let modifiedLineNum = 1;
  
  for (const change of changes) {
    const lines = change.value.split('\n');
    if (lines[lines.length - 1] === '') {
      lines.pop(); // Remove empty last line
    }
    
    if (change.added) {
      for (const line of lines) {
        result += `+${line}\n`;
        modifiedLineNum++;
      }
    } else if (change.removed) {
      for (const line of lines) {
        result += `-${line}\n`;
        originalLineNum++;
      }
    } else {
      for (const line of lines) {
        result += ` ${line}\n`;
        originalLineNum++;
        modifiedLineNum++;
      }
    }
  }
  
  return result;
};

export const generateWordDiff = (original: string, modified: string): Change[] => {
  return diffWords(original, modified);
};

export const createDiffResult = (
  originalFile: FileContent,
  modifiedFile: FileContent
): DiffResult => {
  const diffContent = generateUnifiedDiff(
    originalFile.content,
    modifiedFile.content,
    originalFile.name || modifiedFile.name || 'unnamed'
  );
  
  return {
    id: generateDiffId(),
    originalFile,
    modifiedFile,
    diffContent,
    timestamp: new Date()
  };
};

export const generateChangesIni = (diffs: DiffResult[]): GeneratedConfig => {
  const sections: GeneratedConfig['sections'] = [];
  
  // Settings section
  sections.push({
    name: 'Settings',
    entries: {
      'WindowCaption': 'Generated Mod Configuration',
      'ConfirmMessage': 'This mod was generated from file differences.'
    }
  });
  
  // Process each diff to determine what type of change it represents
  const gffFiles: string[] = [];
  const twodaFiles: string[] = [];
  const installFiles: string[] = [];
  const tlkChanges: Record<string, string> = {};
  
  for (const diff of diffs) {
    const fileType = diff.originalFile.type || diff.modifiedFile.type;
    const fileName = diff.modifiedFile.name || diff.originalFile.name || 'unnamed';
    
    switch (fileType) {
      case 'gff':
        if (!gffFiles.includes(fileName)) {
          gffFiles.push(fileName);
        }
        break;
      case '2da':
        if (!twodaFiles.includes(fileName)) {
          twodaFiles.push(fileName);
        }
        break;
      case 'tlk':
        // Extract TLK changes from diff content
        const tlkMatches = diff.diffContent.match(/\+.*Entry (\d+):/g);
        if (tlkMatches) {
          for (const match of tlkMatches) {
            const entryMatch = match.match(/Entry (\d+):/);
            if (entryMatch) {
              tlkChanges[`StrRef${entryMatch[1]}`] = 'Modified';
            }
          }
        }
        break;
      default:
        // For other file types, add to install list
        if (!installFiles.includes(fileName)) {
          installFiles.push(fileName);
        }
        break;
    }
  }
  
  // Add GFFList section
  if (gffFiles.length > 0) {
    const gffEntries: Record<string, string> = {};
    gffFiles.forEach((file, index) => {
      gffEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: 'GFFList',
      entries: gffEntries
    });
  }
  
  // Add 2DAList section
  if (twodaFiles.length > 0) {
    const twodaEntries: Record<string, string> = {};
    twodaFiles.forEach((file, index) => {
      twodaEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: '2DAList',
      entries: twodaEntries
    });
  }
  
  // Add TLKList section
  if (Object.keys(tlkChanges).length > 0) {
    sections.push({
      name: 'TLKList',
      entries: tlkChanges
    });
  }
  
  // Add InstallList section
  if (installFiles.length > 0) {
    const installEntries: Record<string, string> = {};
    installFiles.forEach((file, index) => {
      installEntries[`File${index + 1}`] = 'Override';
    });
    sections.push({
      name: 'InstallList',
      entries: installEntries
    });
    
    // Add Override section
    const overrideEntries: Record<string, string> = {};
    installFiles.forEach((file, index) => {
      overrideEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: 'Override',
      entries: overrideEntries
    });
  }
  
  // Generate INI content
  let content = '';
  for (const section of sections) {
    content += `[${section.name}]\n`;
    for (const [key, value] of Object.entries(section.entries)) {
      content += `${key}=${value}\n`;
    }
    content += '\n';
  }
  
  return {
    sections,
    content
  };
};