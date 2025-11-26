"""NCS Debugger - A debugging wrapper around the NCS interpreter.

Provides breakpoint support, step execution, variable inspection, and call stack tracking.
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from pykotor.common.misc import Game
from pykotor.resource.formats.ncs import NCS, NCSInstruction

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter, Stack, StackObject

# Import interpreter at runtime to avoid circular dependencies
try:
    from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter, Stack, StackObject
except ImportError:
    Interpreter = None  # type: ignore[assignment, misc]
    Stack = None  # type: ignore[assignment, misc]
    StackObject = None  # type: ignore[assignment, misc]


class DebuggerState(Enum):
    """Debugger execution states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    FINISHED = "finished"
    ERROR = "error"


class Debugger:
    """Debugger wrapper around NCS Interpreter with breakpoint and step support.
    
    Provides:
    - Breakpoint management (by instruction index)
    - Step over, step into, step out
    - Pause/resume
    - Variable inspection
    - Call stack tracking
    - Watch expressions
    """
    
    def __init__(self, ncs: NCS, game: Game = Game.K1):
        """Initialize the debugger.
        
        Args:
        ----
            ncs: NCS: The compiled NCS script to debug
            game: Game: The game version (K1 or TSL)
        """
        if Interpreter is None:
            raise RuntimeError("NCS Interpreter not available")
        
        self._ncs = ncs
        self._game = game
        self._interpreter: Interpreter | None = None
        self._state = DebuggerState.STOPPED
        
        # Breakpoints: set of instruction indices
        self._breakpoints: set[int] = set()
        
        # Step control
        self._step_mode: str | None = None  # "over", "into", "out"
        self._step_depth: int = 0  # Track call depth for step out
        
        # Call stack: list of (function_name, instruction_index, return_address)
        self._call_stack: list[tuple[str, int, int]] = []
        
        # Execution thread
        self._execution_thread: threading.Thread | None = None
        self._stop_requested = False
        self._pause_requested = False
        
        # Event callbacks
        self.on_breakpoint: Callable[[int], None] | None = None
        self.on_step: Callable[[int], None] | None = None
        self.on_finished: Callable[[], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None
        
        # Variable inspection cache
        self._variable_cache: dict[str, Any] = {}
    
    @property
    def state(self) -> DebuggerState:
        """Get current debugger state."""
        return self._state
    
    @property
    def current_instruction_index(self) -> int:
        """Get current instruction index."""
        if self._interpreter is None:
            return -1
        return getattr(self._interpreter, '_cursor_index', -1)
    
    @property
    def current_instruction(self) -> NCSInstruction | None:
        """Get current instruction."""
        if self._interpreter is None:
            return None
        return getattr(self._interpreter, '_cursor', None)
    
    @property
    def call_stack(self) -> list[tuple[str, int, int]]:
        """Get current call stack."""
        return self._call_stack.copy()
    
    @property
    def breakpoints(self) -> set[int]:
        """Get set of breakpoint instruction indices."""
        return self._breakpoints.copy()
    
    def add_breakpoint(self, instruction_index: int) -> bool:
        """Add a breakpoint at the given instruction index.
        
        Args:
        ----
            instruction_index: int: Instruction index to break at
            
        Returns:
        -------
            bool: True if breakpoint was added, False if already exists
        """
        if 0 <= instruction_index < len(self._ncs.instructions):
            self._breakpoints.add(instruction_index)
            return True
        return False
    
    def remove_breakpoint(self, instruction_index: int) -> bool:
        """Remove a breakpoint at the given instruction index.
        
        Args:
        ----
            instruction_index: int: Instruction index to remove breakpoint from
            
        Returns:
        -------
            bool: True if breakpoint was removed, False if it didn't exist
        """
        if instruction_index in self._breakpoints:
            self._breakpoints.remove(instruction_index)
            return True
        return False
    
    def toggle_breakpoint(self, instruction_index: int) -> bool:
        """Toggle a breakpoint at the given instruction index.
        
        Args:
        ----
            instruction_index: int: Instruction index to toggle
            
        Returns:
        -------
            bool: True if breakpoint is now set, False if removed
        """
        if instruction_index in self._breakpoints:
            self.remove_breakpoint(instruction_index)
            return False
        return self.add_breakpoint(instruction_index)
    
    def clear_breakpoints(self):
        """Clear all breakpoints."""
        self._breakpoints.clear()
    
    def start(self, interpreter: Interpreter | None = None):
        """Start debugging execution.
        
        Args:
        ----
            interpreter: Interpreter | None: Pre-configured interpreter to use (for test runs with mocks).
                         If None, creates a new interpreter.
        """
        if self._state == DebuggerState.RUNNING:
            return
        
        self._state = DebuggerState.RUNNING
        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = None
        
        # Use provided interpreter or create new one
        if interpreter is not None:
            self._interpreter = interpreter
        else:
            # Create interpreter
            self._interpreter = Interpreter(self._ncs, self._game)
        
        # Start execution in a separate thread
        self._execution_thread = threading.Thread(target=self._run_execution, daemon=True)
        self._execution_thread.start()
    
    def stop(self):
        """Stop debugging execution."""
        self._stop_requested = True
        self._pause_requested = False
        self._state = DebuggerState.STOPPED
        
        if self._execution_thread and self._execution_thread.is_alive():
            # Wait for thread to finish (with timeout)
            self._execution_thread.join(timeout=1.0)
        
        self._interpreter = None
        self._call_stack.clear()
        self._variable_cache.clear()
    
    def pause(self):
        """Pause execution at next instruction."""
        if self._state == DebuggerState.RUNNING:
            self._pause_requested = True
    
    def resume(self):
        """Resume execution."""
        if self._state == DebuggerState.PAUSED:
            self._state = DebuggerState.RUNNING
            self._pause_requested = False
            self._step_mode = None
    
    def step_over(self):
        """Execute one instruction (step over function calls)."""
        if self._state in (DebuggerState.PAUSED, DebuggerState.STOPPED):
            self._step_mode = "over"
            self._state = DebuggerState.STEPPING
            self._pause_requested = False
    
    def step_into(self):
        """Execute one instruction (step into function calls)."""
        if self._state in (DebuggerState.PAUSED, DebuggerState.STOPPED):
            self._step_mode = "into"
            self._state = DebuggerState.STEPPING
            self._pause_requested = False
    
    def step_out(self):
        """Step out of current function."""
        if self._state in (DebuggerState.PAUSED, DebuggerState.STOPPED):
            if self._call_stack:
                self._step_mode = "out"
                self._step_depth = len(self._call_stack)
                self._state = DebuggerState.STEPPING
                self._pause_requested = False
    
    def get_variables(self) -> dict[str, Any]:
        """Get current variable values from stack.
        
        Returns:
        -------
            dict: Variable name -> value mapping
        """
        if self._interpreter is None:
            return {}
        
        variables: dict[str, Any] = {}
        stack = getattr(self._interpreter, '_stack', None)
        
        if stack is None:
            return variables
        
        # Try to extract variable information from stack
        # This is a simplified version - full implementation would need
        # to track variable names and their stack positions
        try:
            stack_state = stack.state()
            if isinstance(stack_state, list):
                # StackObject list
                for i, obj in enumerate(stack_state):
                    var_name = f"stack[{i}]"
                    variables[var_name] = {
                        "type": obj.data_type.name if hasattr(obj, 'data_type') else "unknown",
                        "value": obj.value if hasattr(obj, 'value') else str(obj)
                    }
        except Exception:
            pass
        
        return variables
    
    def evaluate_watch(self, expression: str) -> Any:
        """Evaluate a watch expression.
        
        Supports simple expressions like:
        - Variable names (looked up in current scope)
        - Literal values (int, float, string)
        - Simple arithmetic operations
        - Stack access (stack[0], stack[-1], etc.)
        
        Args:
        ----
            expression: str: Expression to evaluate
            
        Returns:
        -------
            Any: Evaluation result or error message string
        """
        if self._interpreter is None:
            return "Debugger not initialized"
        
        expression = expression.strip()
        if not expression:
            return "Empty expression"
        
        # Get stack for evaluation
        stack = getattr(self._interpreter, '_stack', None)
        if stack is None:
            return "Stack not available"
        
        try:
            # Try to evaluate as a simple expression
            # First, check if it's a stack access
            if expression.startswith("stack[") and expression.endswith("]"):
                # Extract index
                index_str = expression[6:-1]
                try:
                    index = int(index_str)
                    stack_state = stack.state()
                    if isinstance(stack_state, list):
                        # StackObject list
                        if 0 <= index < len(stack_state):
                            obj = stack_state[index]
                            if hasattr(obj, 'value'):
                                return {
                                    "type": obj.data_type.name if hasattr(obj, 'data_type') else "unknown",
                                    "value": obj.value
                                }
                        elif index < 0 and abs(index) <= len(stack_state):
                            # Negative index from end
                            obj = stack_state[index]
                            if hasattr(obj, 'value'):
                                return {
                                    "type": obj.data_type.name if hasattr(obj, 'data_type') else "unknown",
                                    "value": obj.value
                                }
                    return f"Stack index {index} out of range"
                except ValueError:
                    return f"Invalid stack index: {index_str}"
            
            # Try to evaluate as a literal value
            try:
                # Try integer
                value = int(expression)
                return {"type": "INT", "value": value}
            except ValueError:
                try:
                    # Try float
                    value = float(expression)
                    return {"type": "FLOAT", "value": value}
                except ValueError:
                    # Try string literal
                    if (expression.startswith('"') and expression.endswith('"')) or \
                       (expression.startswith("'") and expression.endswith("'")):
                        return {"type": "STRING", "value": expression[1:-1]}
            
            # Try simple arithmetic
            # Look for operators
            if '+' in expression or '-' in expression or '*' in expression or '/' in expression:
                # Simple arithmetic evaluation
                try:
                    # Use Python's eval for simple expressions (safe in this context)
                    result = eval(expression, {"__builtins__": {}}, {})
                    if isinstance(result, (int, float)):
                        return {"type": "INT" if isinstance(result, int) else "FLOAT", "value": result}
                    return str(result)
                except Exception as e:
                    return f"Evaluation error: {str(e)}"
            
            # Try to look up as variable name (simplified - would need symbol table)
            # For now, return a message
            return f"Variable '{expression}' lookup not yet fully implemented"
            
        except Exception as e:
            return f"Evaluation error: {str(e)}"
    
    def _run_execution(self):
        """Run execution in a separate thread with breakpoint/step support."""
        if self._interpreter is None:
            return
        
        try:
            # Modified run loop that checks for breakpoints and step mode
            while not self._stop_requested and self._interpreter._cursor is not None:
                current_index = self._interpreter._cursor_index
                
                # Check for breakpoint
                if current_index in self._breakpoints:
                    self._state = DebuggerState.PAUSED
                    if self.on_breakpoint:
                        self.on_breakpoint(current_index)
                    # Wait until resumed
                    while self._state == DebuggerState.PAUSED and not self._stop_requested:
                        threading.Event().wait(0.1)
                    if self._stop_requested:
                        break
                
                # Check for pause request
                if self._pause_requested:
                    self._state = DebuggerState.PAUSED
                    if self.on_step:
                        self.on_step(current_index)
                    while self._state == DebuggerState.PAUSED and not self._stop_requested:
                        threading.Event().wait(0.1)
                    if self._stop_requested:
                        break
                
                # Execute one instruction
                self._execute_one_instruction()
                
                # Handle step mode
                if self._step_mode == "over":
                    self._state = DebuggerState.PAUSED
                    self._step_mode = None
                    if self.on_step:
                        self.on_step(self._interpreter._cursor_index)
                    # Wait until resumed
                    while self._state == DebuggerState.PAUSED and not self._stop_requested:
                        threading.Event().wait(0.1)
                    if self._stop_requested:
                        break
                elif self._step_mode == "into":
                    self._state = DebuggerState.PAUSED
                    self._step_mode = None
                    if self.on_step:
                        self.on_step(self._interpreter._cursor_index)
                    # Wait until resumed
                    while self._state == DebuggerState.PAUSED and not self._stop_requested:
                        threading.Event().wait(0.1)
                    if self._stop_requested:
                        break
                elif self._step_mode == "out":
                    # Continue until we return to previous call depth
                    current_depth = len(self._call_stack)
                    if current_depth < self._step_depth:
                        self._state = DebuggerState.PAUSED
                        self._step_mode = None
                        if self.on_step:
                            self.on_step(self._interpreter._cursor_index)
                        # Wait until resumed
                        while self._state == DebuggerState.PAUSED and not self._stop_requested:
                            threading.Event().wait(0.1)
                        if self._stop_requested:
                            break
            
            # Execution finished
            if not self._stop_requested:
                self._state = DebuggerState.FINISHED
                if self.on_finished:
                    self.on_finished()
        
        except Exception as e:
            self._state = DebuggerState.ERROR
            if self.on_error:
                self.on_error(e)
    
    def _execute_one_instruction(self):
        """Execute a single instruction using the interpreter's step_execute() method.
        
        This properly executes one instruction at a time for debugging, using the
        interpreter's step_execute() method that was extracted from run().
        """
        if self._interpreter is None:
            return
        
        # Use the interpreter's step_execute() method for proper step-by-step execution
        self._interpreter.step_execute()

