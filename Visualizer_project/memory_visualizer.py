import ast
import sys
from collections import defaultdict

class MemoryVisualizer:
    def __init__(self):
        self.memory_snapshots = []
        self.current_snapshot = {}
    
    def visualize_memory(self, code, execution_env):
        """Visualize memory usage during code execution"""
        try:
            # Instrument the code to track memory changes
            instrumented_code = self._instrument_code(code)
            
            # Add memory tracking to execution environment
            execution_env['__memory_tracker__'] = self
            execution_env['__record_memory__'] = self.record_memory
            
            # Execute the instrumented code
            exec(instrumented_code, execution_env)
            
            return self.format_memory_snapshots()
        except Exception as e:
            return [f"Memory visualization error: {str(e)}"]
    
    def record_memory(self, var_name, value):
        """Record a memory snapshot for a variable"""
        # Get memory address
        mem_address = id(value)
        
        # Get type information
        var_type = type(value).__name__
        
        # Get size approximation
        try:
            var_size = sys.getsizeof(value)
        except:
            var_size = "unknown"
        
        # Format value for display
        if isinstance(value, (int, float, str, bool)) or value is None:
            formatted_value = repr(value)
        else:
            formatted_value = f"<{var_type} object>"
        
        # Record the snapshot
        self.current_snapshot[var_name] = {
            'address': mem_address,
            'type': var_type,
            'size': var_size,
            'value': formatted_value
        }
    
    def take_snapshot(self, line_no):
        """Take a memory snapshot at a specific line"""
        snapshot = {
            'line': line_no,
            'variables': dict(self.current_snapshot)
        }
        self.memory_snapshots.append(snapshot)
    
    def _instrument_code(self, code):
        """Instrument code to track memory usage"""
        lines = code.split('\n')
        instrumented_lines = []
        line_no = 1
        
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                # Add memory snapshot before executing the line
                instrumented_lines.append(f'__memory_tracker__.take_snapshot({line_no})')
                
                # Add variable assignment tracking
                if '=' in line and not line.strip().startswith('def '):
                    parts = line.split('=')
                    if len(parts) >= 2:
                        var_name = parts[0].strip()
                        # Skip function definitions and complex assignments
                        if not any(c in var_name for c in '([{') and not line.strip().startswith('def '):
                            instrumented_lines.append(f'__record_memory__("{var_name}", {var_name})')
                
                # Add the original line
                instrumented_lines.append(line)
            else:
                # Keep comments and empty lines as is
                instrumented_lines.append(line)
            
            line_no += 1
        
        # Add final snapshot
        instrumented_lines.append(f'__memory_tracker__.take_snapshot({line_no})')
        
        return '\n'.join(instrumented_lines)
    
    def format_memory_snapshots(self):
        """Format memory snapshots for display"""
        formatted = []
        
        for i, snapshot in enumerate(self.memory_snapshots):
            formatted.append(f"Snapshot at line {snapshot['line']}:")
            
            if not snapshot['variables']:
                formatted.append("  No variables in memory")
                continue
            
            for var_name, var_info in snapshot['variables'].items():
                formatted.append(f"  {var_name}: {var_info['value']} "
                               f"(type: {var_info['type']}, "
                               f"size: {var_info['size']}, "
                               f"address: {hex(var_info['address'])})")
            
            formatted.append("")  # Empty line between snapshots
        
        return formatted