import { useHotkeys } from 'react-hotkeys-hook';

interface KeyboardShortcutsOptions {
  onUndo?: () => void;
  onRedo?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
}

export const useKeyboardShortcuts = (options: KeyboardShortcutsOptions = {}) => {
  const { onUndo, onRedo, canUndo = false, canRedo = false } = options;

  useHotkeys('ctrl+z', () => {
    if (canUndo && onUndo) {
      onUndo();
    }
  }, [canUndo, onUndo]);

  useHotkeys('ctrl+y', () => {
    if (canRedo && onRedo) {
      onRedo();
    }
  }, [canRedo, onRedo]);

  useHotkeys('ctrl+shift+z', () => {
    if (canRedo && onRedo) {
      onRedo();
    }
  }, [canRedo, onRedo]);

  return { onUndo, onRedo, canUndo, canRedo };
};