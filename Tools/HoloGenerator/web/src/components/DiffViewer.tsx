import React, { useMemo } from 'react';
import styled from 'styled-components';
import { DiffResult } from '../types';
import { copyToClipboard, downloadFile } from '../utils/fileUtils';
import { generateWordDiff } from '../utils/diffUtils';

const DiffContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
`;

const DiffHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f6f8fa;
  border-bottom: 1px solid #e1e5e9;
  font-size: 14px;
  font-weight: 600;
`;

const DiffContent = styled.div`
  flex: 1;
  overflow-y: auto;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 13px;
  line-height: 1.45;
`;

const DiffLine = styled.div<{ type: 'added' | 'removed' | 'context' | 'header' }>`
  padding: 2px 8px;
  white-space: pre-wrap;
  word-break: break-all;
  
  ${props => {
    switch (props.type) {
      case 'added':
        return `
          background-color: #e6ffed;
          border-left: 3px solid #28a745;
          color: #155724;
        `;
      case 'removed':
        return `
          background-color: #ffecf0;
          border-left: 3px solid #dc3545;
          color: #721c24;
        `;
      case 'header':
        return `
          background-color: #f1f8ff;
          color: #0366d6;
          font-weight: 600;
        `;
      default:
        return `
          background-color: transparent;
          color: #24292e;
        `;
    }
  }}
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionButton = styled.button`
  background: #f6f8fa;
  color: #24292e;
  border: 1px solid #d1d9e0;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  
  &:hover {
    background: #e1e7ed;
  }
  
  &:active {
    background: #d1d9e0;
  }
`;

const WordDiffSpan = styled.span<{ type: 'added' | 'removed' | 'common' }>`
  ${props => {
    switch (props.type) {
      case 'added':
        return `
          background-color: #acf2bd;
          color: #155724;
        `;
      case 'removed':
        return `
          background-color: #fdb8c0;
          color: #721c24;
          text-decoration: line-through;
        `;
      default:
        return '';
    }
  }}
`;

const EmptyState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #656d76;
  font-style: italic;
`;

interface DiffViewerProps {
  diff: DiffResult | null;
  showWordDiff?: boolean;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ diff, showWordDiff = false }) => {
  const diffLines = useMemo(() => {
    if (!diff) return [];
    
    return diff.diffContent.split('\n').map((line, index) => {
      let type: 'added' | 'removed' | 'context' | 'header' = 'context';
      
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
        type = 'header';
      } else if (line.startsWith('+')) {
        type = 'added';
        line = line.substring(1); // Remove the + prefix
      } else if (line.startsWith('-')) {
        type = 'removed';
        line = line.substring(1); // Remove the - prefix
      } else if (line.startsWith(' ')) {
        line = line.substring(1); // Remove the space prefix
      }
      
      return { line, type, key: index };
    });
  }, [diff]);

  const wordDiff = useMemo(() => {
    if (!diff || !showWordDiff) return null;
    return generateWordDiff(diff.originalFile.content, diff.modifiedFile.content);
  }, [diff, showWordDiff]);

  const handleCopyDiff = async () => {
    if (!diff) return;
    
    const success = await copyToClipboard(diff.diffContent);
    if (success) {
      // Could add a toast notification here
      console.log('Diff copied to clipboard');
    }
  };

  const handleDownloadDiff = () => {
    if (!diff) return;
    
    const fileName = `${diff.originalFile.name || 'diff'}.diff`;
    downloadFile(diff.diffContent, fileName, 'text/plain');
  };

  if (!diff) {
    return (
      <DiffContainer>
        <DiffHeader>
          <span>Diff Result</span>
        </DiffHeader>
        <EmptyState>
          Select or create files to see the differences here
        </EmptyState>
      </DiffContainer>
    );
  }

  return (
    <DiffContainer>
      <DiffHeader>
        <span>
          Diff: {diff.originalFile.name} → {diff.modifiedFile.name}
        </span>
        <ButtonGroup>
          <ActionButton onClick={handleCopyDiff}>
            Copy Diff
          </ActionButton>
          <ActionButton onClick={handleDownloadDiff}>
            Download
          </ActionButton>
        </ButtonGroup>
      </DiffHeader>
      
      <DiffContent>
        {showWordDiff && wordDiff ? (
          <div style={{ padding: '12px' }}>
            {wordDiff.map((part, index) => (
              <WordDiffSpan
                key={index}
                type={part.added ? 'added' : part.removed ? 'removed' : 'common'}
              >
                {part.value}
              </WordDiffSpan>
            ))}
          </div>
        ) : (
          diffLines.map(({ line, type, key }) => (
            <DiffLine key={key} type={type}>
              {line}
            </DiffLine>
          ))
        )}
      </DiffContent>
    </DiffContainer>
  );
};