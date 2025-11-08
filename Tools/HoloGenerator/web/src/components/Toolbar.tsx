import React from 'react';
import styled from 'styled-components';

const ToolbarContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #f6f8fa;
  border-bottom: 1px solid #e1e5e9;
  gap: 16px;
`;

const ToolbarSection = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ToolbarButton = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid;
  font-size: 14px;
  cursor: pointer;
  font-weight: 500;
  
  ${props => props.variant === 'primary' ? `
    background: #0969da;
    color: white;
    border-color: #0969da;
    
    &:hover {
      background: #0860ca;
      border-color: #0860ca;
    }
    
    &:disabled {
      background: #94a3b8;
      border-color: #94a3b8;
      cursor: not-allowed;
    }
  ` : `
    background: #f6f8fa;
    color: #24292e;
    border-color: #d1d9e0;
    
    &:hover {
      background: #e1e7ed;
    }
    
    &:disabled {
      background: #f6f8fa;
      color: #656d76;
      cursor: not-allowed;
    }
  `}
`;

const ModeToggle = styled.label`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #24292e;
  cursor: pointer;
`;

const Checkbox = styled.input`
  margin: 0;
`;

const KeyboardHint = styled.span`
  font-size: 12px;
  color: #656d76;
  background: #f6f8fa;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #e1e5e9;
`;

interface ToolbarProps {
  onDiff: () => void;
  onClear: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onGenerateConfig: () => void;
  canUndo: boolean;
  canRedo: boolean;
  canDiff: boolean;
  showWordDiff: boolean;
  onShowWordDiffChange: (show: boolean) => void;
  diffCount: number;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  onDiff,
  onClear,
  onUndo,
  onRedo,
  onGenerateConfig,
  canUndo,
  canRedo,
  canDiff,
  showWordDiff,
  onShowWordDiffChange,
  diffCount
}) => {
  return (
    <ToolbarContainer>
      <ToolbarSection>
        <ToolbarButton variant="primary" onClick={onDiff} disabled={!canDiff}>
          Compare Files
        </ToolbarButton>
        <ToolbarButton onClick={onClear}>
          Clear All
        </ToolbarButton>
      </ToolbarSection>
      
      <ToolbarSection>
        <ModeToggle>
          <Checkbox
            type="checkbox"
            checked={showWordDiff}
            onChange={(e) => onShowWordDiffChange(e.target.checked)}
          />
          Word-level diff
        </ModeToggle>
      </ToolbarSection>
      
      <ToolbarSection>
        <ToolbarButton onClick={onUndo} disabled={!canUndo}>
          Undo
        </ToolbarButton>
        <KeyboardHint>Ctrl+Z</KeyboardHint>
        
        <ToolbarButton onClick={onRedo} disabled={!canRedo}>
          Redo
        </ToolbarButton>
        <KeyboardHint>Ctrl+Y</KeyboardHint>
      </ToolbarSection>
      
      <ToolbarSection>
        <span style={{ fontSize: '14px', color: '#656d76' }}>
          {diffCount} diffs
        </span>
        <ToolbarButton variant="primary" onClick={onGenerateConfig} disabled={diffCount === 0}>
          Generate changes.ini
        </ToolbarButton>
      </ToolbarSection>
    </ToolbarContainer>
  );
};