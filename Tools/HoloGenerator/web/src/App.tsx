import React, { useState, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import SplitPane from 'react-split-pane';

import { ContentEditor } from './components/ContentEditor';
import { DiffViewer } from './components/DiffViewer';
import { ConfigGenerator } from './components/ConfigGenerator';
import { Toolbar } from './components/Toolbar';

import { useHistory } from './hooks/useHistory';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

import { FileContent, DiffResult, GeneratedConfig } from './types';
import { createDiffResult, generateChangesIni } from './utils/diffUtils';

const AppContainer = styled.div`
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
`;

const Header = styled.header`
  background: #24292e;
  color: white;
  padding: 16px 24px;
  text-align: center;
`;

const Title = styled.h1`
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 16px;
  opacity: 0.8;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const EditorSection = styled.div`
  flex: 1;
  min-height: 0;
`;

const ConfigSection = styled.div`
  height: 300px;
  border-top: 1px solid #e1e5e9;
`;

const StyledSplitPane = styled(SplitPane)`
  > .Pane1 {
    overflow: hidden;
  }
  > .Pane2 {
    overflow: hidden;
  }
  
  .Resizer {
    background: #e1e5e9;
    opacity: 0.5;
    z-index: 1;
    box-sizing: border-box;
    background-clip: padding-box;
  }
  
  .Resizer:hover {
    transition: all 0.2s ease;
    opacity: 1;
  }
  
  .Resizer.horizontal {
    height: 11px;
    margin: -5px 0;
    border-top: 5px solid rgba(255, 255, 255, 0);
    border-bottom: 5px solid rgba(255, 255, 255, 0);
    cursor: row-resize;
    width: 100%;
  }
  
  .Resizer.vertical {
    width: 11px;
    margin: 0 -5px;
    border-left: 5px solid rgba(255, 255, 255, 0);
    border-right: 5px solid rgba(255, 255, 255, 0);
    cursor: col-resize;
  }
`;

export const App: React.FC = () => {
  const [originalFile, setOriginalFile] = useState<FileContent | null>(null);
  const [modifiedFile, setModifiedFile] = useState<FileContent | null>(null);
  const [showWordDiff, setShowWordDiff] = useState(false);
  const [generatedConfig, setGeneratedConfig] = useState<GeneratedConfig | null>(null);
  const [isGeneratingConfig, setIsGeneratingConfig] = useState(false);

  const { 
    history, 
    currentDiff, 
    addDiff, 
    undo, 
    redo, 
    canUndo, 
    canRedo 
  } = useHistory();

  // Set up keyboard shortcuts
  useKeyboardShortcuts({
    onUndo: undo,
    onRedo: redo,
    canUndo,
    canRedo
  });

  const canDiff = useMemo(() => {
    return originalFile?.content && modifiedFile?.content && 
           originalFile.content.trim() !== modifiedFile.content.trim();
  }, [originalFile, modifiedFile]);

  const handleDiff = useCallback(() => {
    if (!originalFile || !modifiedFile || !canDiff) return;

    const diffResult = createDiffResult(originalFile, modifiedFile);
    addDiff(diffResult);
  }, [originalFile, modifiedFile, canDiff, addDiff]);

  const handleClear = useCallback(() => {
    setOriginalFile(null);
    setModifiedFile(null);
    setGeneratedConfig(null);
  }, []);

  const handleGenerateConfig = useCallback(async () => {
    if (history.length === 0) return;

    setIsGeneratingConfig(true);
    try {
      // Simulate some processing time for better UX
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const config = generateChangesIni(history);
      setGeneratedConfig(config);
    } catch (error) {
      console.error('Error generating configuration:', error);
      alert('Error generating configuration. Please try again.');
    } finally {
      setIsGeneratingConfig(false);
    }
  }, [history]);

  return (
    <AppContainer>
      <Header>
        <Title>HoloGenerator</Title>
        <Subtitle>KOTOR Configuration Generator for HoloPatcher</Subtitle>
      </Header>
      
      <MainContent>
        <Toolbar
          onDiff={handleDiff}
          onClear={handleClear}
          onUndo={undo}
          onRedo={redo}
          onGenerateConfig={handleGenerateConfig}
          canUndo={canUndo}
          canRedo={canRedo}
          canDiff={canDiff}
          showWordDiff={showWordDiff}
          onShowWordDiffChange={setShowWordDiff}
          diffCount={history.length}
        />
        
        <StyledSplitPane split="horizontal" defaultSize="70%">
          <EditorSection>
            <StyledSplitPane split="vertical" defaultSize="33%">
              <ContentEditor
                title="Original File"
                fileContent={originalFile}
                onContentChange={setOriginalFile}
                placeholder="Paste or upload your original file content here..."
              />
              
              <StyledSplitPane split="vertical" defaultSize="50%">
                <ContentEditor
                  title="Modified File"
                  fileContent={modifiedFile}
                  onContentChange={setModifiedFile}
                  placeholder="Paste or upload your modified file content here..."
                />
                
                <DiffViewer 
                  diff={currentDiff} 
                  showWordDiff={showWordDiff}
                />
              </StyledSplitPane>
            </StyledSplitPane>
          </EditorSection>
          
          <ConfigSection>
            <ConfigGenerator
              config={generatedConfig}
              onGenerateConfig={handleGenerateConfig}
              isGenerating={isGeneratingConfig}
            />
          </ConfigSection>
        </StyledSplitPane>
      </MainContent>
    </AppContainer>
  );
};