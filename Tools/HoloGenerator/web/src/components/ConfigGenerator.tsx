import React from 'react';
import styled from 'styled-components';
import { GeneratedConfig } from '../types';
import { copyToClipboard, downloadFile } from '../utils/fileUtils';

const ConfigContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
`;

const ConfigHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f6f8fa;
  border-bottom: 1px solid #e1e5e9;
  font-size: 14px;
  font-weight: 600;
`;

const ConfigContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 13px;
  line-height: 1.45;
  background: #f8f9fa;
`;

const ConfigSection = styled.div`
  margin-bottom: 16px;
`;

const SectionHeader = styled.div`
  color: #0366d6;
  font-weight: 600;
  margin-bottom: 8px;
`;

const ConfigLine = styled.div`
  color: #24292e;
  margin-left: 16px;
  margin-bottom: 2px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionButton = styled.button`
  background: #0969da;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  
  &:hover {
    background: #0860ca;
  }
  
  &:active {
    background: #0757ba;
  }
`;

const SecondaryButton = styled(ActionButton)`
  background: #f6f8fa;
  color: #24292e;
  border: 1px solid #d1d9e0;
  
  &:hover {
    background: #e1e7ed;
  }
  
  &:active {
    background: #d1d9e0;
  }
`;

const EmptyState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #656d76;
  font-style: italic;
  text-align: center;
  padding: 20px;
`;

const StatsText = styled.span`
  font-size: 12px;
  color: #656d76;
`;

interface ConfigGeneratorProps {
  config: GeneratedConfig | null;
  onGenerateConfig: () => void;
  isGenerating?: boolean;
}

export const ConfigGenerator: React.FC<ConfigGeneratorProps> = ({
  config,
  onGenerateConfig,
  isGenerating = false
}) => {
  const handleCopyConfig = async () => {
    if (!config) return;
    
    const success = await copyToClipboard(config.content);
    if (success) {
      console.log('Configuration copied to clipboard');
    }
  };

  const handleDownloadConfig = () => {
    if (!config) return;
    
    downloadFile(config.content, 'changes.ini', 'text/plain');
  };

  if (!config) {
    return (
      <ConfigContainer>
        <ConfigHeader>
          <span>Generated changes.ini</span>
          <ActionButton onClick={onGenerateConfig} disabled={isGenerating}>
            {isGenerating ? 'Generating...' : 'Generate Config'}
          </ActionButton>
        </ConfigHeader>
        <EmptyState>
          <div>
            No configuration generated yet.
            <br />
            <br />
            Add some file diffs above and click "Generate Config" to create a changes.ini file 
            compatible with HoloPatcher.
          </div>
        </EmptyState>
      </ConfigContainer>
    );
  }

  const lineCount = config.content.split('\n').length;
  const sectionCount = config.sections.length;

  return (
    <ConfigContainer>
      <ConfigHeader>
        <div>
          <span>Generated changes.ini</span>
          <StatsText style={{ marginLeft: '12px' }}>
            {sectionCount} sections, {lineCount} lines
          </StatsText>
        </div>
        <ButtonGroup>
          <SecondaryButton onClick={handleCopyConfig}>
            Copy Code
          </SecondaryButton>
          <ActionButton onClick={handleDownloadConfig}>
            Download
          </ActionButton>
          <SecondaryButton onClick={onGenerateConfig} disabled={isGenerating}>
            Regenerate
          </SecondaryButton>
        </ButtonGroup>
      </ConfigHeader>
      
      <ConfigContent>
        {config.sections.map((section, index) => (
          <ConfigSection key={index}>
            <SectionHeader>[{section.name}]</SectionHeader>
            {Object.entries(section.entries).map(([key, value], entryIndex) => (
              <ConfigLine key={entryIndex}>
                {key}={value}
              </ConfigLine>
            ))}
          </ConfigSection>
        ))}
      </ConfigContent>
    </ConfigContainer>
  );
};