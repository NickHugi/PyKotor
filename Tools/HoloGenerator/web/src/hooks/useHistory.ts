import { useState, useCallback } from 'react';
import { HistoryState, DiffResult } from '../types';

const MAX_HISTORY_SIZE = 50;

export const useHistory = () => {
  const [history, setHistory] = useState<HistoryState>({
    diffs: [],
    currentIndex: -1
  });

  const addDiff = useCallback((diff: DiffResult) => {
    setHistory(prev => {
      const newDiffs = [...prev.diffs];
      
      // If we're not at the end, remove future history
      if (prev.currentIndex < prev.diffs.length - 1) {
        newDiffs.splice(prev.currentIndex + 1);
      }
      
      // Add new diff
      newDiffs.push(diff);
      
      // Limit history size
      if (newDiffs.length > MAX_HISTORY_SIZE) {
        newDiffs.shift();
      }
      
      return {
        diffs: newDiffs,
        currentIndex: newDiffs.length - 1
      };
    });
  }, []);

  const undo = useCallback(() => {
    setHistory(prev => ({
      ...prev,
      currentIndex: Math.max(-1, prev.currentIndex - 1)
    }));
  }, []);

  const redo = useCallback(() => {
    setHistory(prev => ({
      ...prev,
      currentIndex: Math.min(prev.diffs.length - 1, prev.currentIndex + 1)
    }));
  }, []);

  const canUndo = history.currentIndex > -1;
  const canRedo = history.currentIndex < history.diffs.length - 1;
  
  const currentDiff = history.currentIndex >= 0 ? history.diffs[history.currentIndex] : null;
  const allDiffs = history.diffs.slice(0, history.currentIndex + 1);

  return {
    history: allDiffs,
    currentDiff,
    addDiff,
    undo,
    redo,
    canUndo,
    canRedo
  };
};