import ast
import inspect
import sys
from collections import defaultdict

class CodeVisualizer:
    def __init__(self):
        self.steps = []
        self.line_numbers = []
        self.variable_states = []
        self.current_line = 0
        
    def visualize_execution(self, code, execution_env):
        """Generate visualization of code execution steps"""
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Add our custom tracer to the execution environment
            execution_env['__visualizer__'] = self
            execution_env['__trace_line__'] = self.trace_line
            execution_env['__trace_var__'] = self.trace_var
            
            # Instrument the code to add tracing
            instrumented_code = self.instrument_code(code)
            
            # Execute the instrumented code
            exec(instrumented_code, execution_env)
            
            return self.format_steps()
        except Exception as e:
            return [f"Visualization error: {str(e)}"]
    
    def trace_line(self, line_no):
        """Record execution of a line"""
        self.current_line = line_no
        self.steps.append(f"Executing line {line_no}")
        self.line_numbers.append(line_no)
        
    def trace_var(self, var_name, value):
        """Record variable state change"""
        # Format the value for display
        if isinstance(value, (int, float, str, bool)) or value is None:
            formatted_value = repr(value)
        else:
            formatted_value = f"<{type(value).__name__} object at {id(value)}>"
        
        self.steps.append(f"Variable '{var_name}' = {formatted_value}")
        self.variable_states.append((var_name, formatted_value))
    
    def instrument_code(self, code):
        """Add tracing to the code"""
        lines = code.split('\n')
        instrumented_lines = []
        line_no = 1
        
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                # Add line tracing
                instrumented_lines.append(f'__trace_line__({line_no})')
                
                # Add variable assignment tracing
                if '=' in line and not line.strip().startswith('def '):
                    parts = line.split('=')
                    if len(parts) >= 2:
                        var_name = parts[0].strip()
                        # Skip function definitions and complex assignments
                        if not any(c in var_name for c in '([{') and not line.strip().startswith('def '):
                            instrumented_lines.append(f'__trace_var__("{var_name}", {var_name})')
                
                # Add the original line
                instrumented_lines.append(line)
            else:
                # Keep comments and empty lines as is
                instrumented_lines.append(line)
            
            line_no += 1
        
        return '\n'.join(instrumented_lines)
    
    def format_steps(self):
        """Format the execution steps for display"""
        formatted = []
        step_count = 1
        
        for i, step in enumerate(self.steps):
            formatted.append(f"Step {step_count}: {step}")
            step_count += 1
            
            # Add variable states after each line execution
            if "Executing line" in step and i < len(self.line_numbers) - 1:
                line_num = self.line_numbers[i]
                # Find variables that were modified around this line
                for var_name, value in self.variable_states:
                    formatted.append(f"  → {var_name} = {value}")
        
        return formatted