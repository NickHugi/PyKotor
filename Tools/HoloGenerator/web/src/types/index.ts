export interface FileContent {
  name: string;
  content: string;
  type: 'gff' | '2da' | 'tlk' | 'ssf' | 'lip' | 'ini' | 'text';
}

export interface DiffResult {
  id: string;
  originalFile: FileContent;
  modifiedFile: FileContent;
  diffContent: string;
  timestamp: Date;
}

export interface HistoryState {
  diffs: DiffResult[];
  currentIndex: number;
}

export interface ConfigurationSection {
  name: string;
  entries: Record<string, string>;
}

export interface GeneratedConfig {
  sections: ConfigurationSection[];
  content: string;
}