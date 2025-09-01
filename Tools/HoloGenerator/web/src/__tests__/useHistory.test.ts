import { renderHook, act } from '@testing-library/react';
import { useHistory } from '../hooks/useHistory';
import { DiffResult, FileContent } from '../types';

describe('useHistory', () => {
  const createMockDiff = (id: string, content: string = 'test'): DiffResult => ({
    id,
    originalFile: { name: `original_${id}.txt`, content, type: 'text' },
    modifiedFile: { name: `modified_${id}.txt`, content: `${content}_modified`, type: 'text' },
    diffContent: `diff for ${id}`,
    timestamp: new Date()
  });

  it('should initialize with empty history', () => {
    const { result } = renderHook(() => useHistory());
    
    expect(result.current.history).toEqual([]);
    expect(result.current.currentDiff).toBeNull();
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(false);
  });

  it('should add diffs to history', () => {
    const { result } = renderHook(() => useHistory());
    const diff1 = createMockDiff('1');
    const diff2 = createMockDiff('2');
    
    act(() => {
      result.current.addDiff(diff1);
    });
    
    expect(result.current.history).toHaveLength(1);
    expect(result.current.currentDiff).toBe(diff1);
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(false);
    
    act(() => {
      result.current.addDiff(diff2);
    });
    
    expect(result.current.history).toHaveLength(2);
    expect(result.current.currentDiff).toBe(diff2);
  });

  it('should handle undo operations', () => {
    const { result } = renderHook(() => useHistory());
    const diff1 = createMockDiff('1');
    const diff2 = createMockDiff('2');
    
    act(() => {
      result.current.addDiff(diff1);
      result.current.addDiff(diff2);
    });
    
    // Should be at diff2
    expect(result.current.currentDiff).toBe(diff2);
    expect(result.current.canUndo).toBe(true);
    
    act(() => {
      result.current.undo();
    });
    
    // Should be at diff1
    expect(result.current.currentDiff).toBe(diff1);
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(true);
    
    act(() => {
      result.current.undo();
    });
    
    // Should be at beginning
    expect(result.current.currentDiff).toBeNull();
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(true);
  });

  it('should handle redo operations', () => {
    const { result } = renderHook(() => useHistory());
    const diff1 = createMockDiff('1');
    const diff2 = createMockDiff('2');
    
    act(() => {
      result.current.addDiff(diff1);
      result.current.addDiff(diff2);
    });
    
    // Undo twice
    act(() => {
      result.current.undo();
      result.current.undo();
    });
    
    expect(result.current.currentDiff).toBeNull();
    expect(result.current.canRedo).toBe(true);
    
    act(() => {
      result.current.redo();
    });
    
    expect(result.current.currentDiff).toBe(diff1);
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(true);
    
    act(() => {
      result.current.redo();
    });
    
    expect(result.current.currentDiff).toBe(diff2);
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(false);
  });

  it('should clear future history when adding diff after undo', () => {
    const { result } = renderHook(() => useHistory());
    const diff1 = createMockDiff('1');
    const diff2 = createMockDiff('2');
    const diff3 = createMockDiff('3');
    
    act(() => {
      result.current.addDiff(diff1);
      result.current.addDiff(diff2);
    });
    
    // Undo once
    act(() => {
      result.current.undo();
    });
    
    expect(result.current.currentDiff).toBe(diff1);
    expect(result.current.canRedo).toBe(true);
    
    // Add new diff - should clear future history
    act(() => {
      result.current.addDiff(diff3);
    });
    
    expect(result.current.history).toHaveLength(2);
    expect(result.current.history[0]).toBe(diff1);
    expect(result.current.history[1]).toBe(diff3);
    expect(result.current.currentDiff).toBe(diff3);
    expect(result.current.canRedo).toBe(false);
  });

  it('should limit history size', () => {
    const { result } = renderHook(() => useHistory());
    
    // Add more than MAX_HISTORY_SIZE (50) diffs
    act(() => {
      for (let i = 0; i < 55; i++) {
        result.current.addDiff(createMockDiff(`diff_${i}`));
      }
    });
    
    // History should be limited to 50
    expect(result.current.history.length).toBeLessThanOrEqual(50);
    
    // Should still have the most recent diffs
    const lastDiff = result.current.history[result.current.history.length - 1];
    expect(lastDiff.id).toBe('diff_54');
  });

  it('should handle edge cases for undo/redo', () => {
    const { result } = renderHook(() => useHistory());
    
    // Try undo/redo with empty history
    act(() => {
      result.current.undo();
      result.current.redo();
    });
    
    expect(result.current.currentDiff).toBeNull();
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(false);
    
    // Add one diff and try excessive undo/redo
    const diff = createMockDiff('test');
    act(() => {
      result.current.addDiff(diff);
    });
    
    // Multiple undos should not go below -1
    act(() => {
      result.current.undo();
      result.current.undo();
      result.current.undo();
    });
    
    expect(result.current.currentDiff).toBeNull();
    
    // Multiple redos should not exceed history length
    act(() => {
      result.current.redo();
      result.current.redo();
      result.current.redo();
    });
    
    expect(result.current.currentDiff).toBe(diff);
  });

  it('should return correct history subset based on current index', () => {
    const { result } = renderHook(() => useHistory());
    const diff1 = createMockDiff('1');
    const diff2 = createMockDiff('2');
    const diff3 = createMockDiff('3');
    
    act(() => {
      result.current.addDiff(diff1);
      result.current.addDiff(diff2);
      result.current.addDiff(diff3);
    });
    
    // Full history
    expect(result.current.history).toHaveLength(3);
    
    // Undo once
    act(() => {
      result.current.undo();
    });
    
    // History should only include items up to current index
    expect(result.current.history).toHaveLength(2);
    expect(result.current.history).toEqual([diff1, diff2]);
    
    // Undo again
    act(() => {
      result.current.undo();
    });
    
    expect(result.current.history).toHaveLength(1);
    expect(result.current.history).toEqual([diff1]);
  });
});