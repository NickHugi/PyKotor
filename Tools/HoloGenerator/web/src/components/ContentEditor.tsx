import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { FileContent } from '../types';
import { detectFileType } from '../utils/diffUtils';
import { readFileAsText, validateFileName } from '../utils/fileUtils';

const EditorContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
`;

const EditorHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f6f8fa;
  border-bottom: 1px solid #e1e5e9;
  font-size: 14px;
  font-weight: 600;
`;

const FileNameInput = styled.input`
  border: 1px solid #d1d9e0;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  min-width: 120px;
  max-width: 200px;
`;

const FileUploadButton = styled.button`
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
`;

const TextArea = styled.textarea`
  flex: 1;
  border: none;
  padding: 12px;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 13px;
  line-height: 1.45;
  resize: none;
  outline: none;
  background: #ffffff;
  
  &::placeholder {
    color: #656d76;
  }
`;

const HiddenFileInput = styled.input`
  display: none;
`;

interface ContentEditorProps {
  title: string;
  fileContent: FileContent | null;
  onContentChange: (content: FileContent) => void;
  placeholder: string;
}

export const ContentEditor: React.FC<ContentEditorProps> = ({
  title,
  fileContent,
  onContentChange,
  placeholder
}) => {
  const [fileName, setFileName] = useState(fileContent?.name || '');
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleContentChange = useCallback((newContent: string) => {
    const finalFileName = fileName.trim() || 'unnamed.txt';
    const fileType = detectFileType(finalFileName, newContent);
    
    onContentChange({
      name: finalFileName,
      content: newContent,
      type: fileType
    });
  }, [fileName, onContentChange]);

  const handleFileNameChange = useCallback((newFileName: string) => {
    setFileName(newFileName);
    if (fileContent && validateFileName(newFileName)) {
      const fileType = detectFileType(newFileName, fileContent.content);
      onContentChange({
        ...fileContent,
        name: newFileName,
        type: fileType
      });
    }
  }, [fileContent, onContentChange]);

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await readFileAsText(file);
      const fileType = detectFileType(file.name, content);
      
      setFileName(file.name);
      onContentChange({
        name: file.name,
        content,
        type: fileType
      });
    } catch (error) {
      console.error('Error reading file:', error);
      alert('Error reading file. Please try again.');
    }
    
    // Reset the input
    event.target.value = '';
  }, [onContentChange]);

  const triggerFileUpload = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <EditorContainer>
      <EditorHeader>
        <span>{title}</span>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <FileNameInput
            type="text"
            value={fileName}
            onChange={(e) => handleFileNameChange(e.target.value)}
            placeholder="filename.ext"
          />
          <FileUploadButton onClick={triggerFileUpload}>
            Upload File
          </FileUploadButton>
        </div>
      </EditorHeader>
      
      <TextArea
        value={fileContent?.content || ''}
        onChange={(e) => handleContentChange(e.target.value)}
        placeholder={placeholder}
      />
      
      <HiddenFileInput
        ref={fileInputRef}
        type="file"
        accept=".gff,.utc,.uti,.dlg,.are,.git,.ifo,.jrl,.2da,.tlk,.ssf,.lip,.ini,.txt"
        onChange={handleFileUpload}
      />
    </EditorContainer>
  );
};