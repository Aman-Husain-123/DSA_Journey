import time
import ast
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, jsonify, send_file
import sys
from functools import wraps
import platform
import psutil
import os
from datetime import datetime
import json
from visualizer import CodeVisualizer
from tree_visualizer import TreeVisualizer
from memory_visualizer import MemoryVisualizer

app = Flask(__name__)

# Create saved_code directory if it doesn't exist
if not os.path.exists('saved_code'):
    os.makedirs('saved_code')

# Safe execution environment with essential built-ins
safe_builtins = {
    'print': print,
    'len': len,
    'range': range,
    'list': list,
    'dict': dict,
    'set': set,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'sum': sum,
    'min': min,
    'max': max,
    'abs': abs,
    'round': round,
    'zip': zip,
    'enumerate': enumerate
}

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    return wrapper

def get_memory_usage():
    """Get current memory usage in MB, cross-platform"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Bytes to MB

def measure_memory(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_memory = get_memory_usage()
        result = func(*args, **kwargs)
        end_memory = get_memory_usage()
        return result, end_memory - start_memory
    return wrapper

def analyze_complexity(code):
    """Analyze time and space complexity of Python code with improved accuracy"""
    try:
        tree = ast.parse(code)
        analysis = {
            'time_complexity': 'O(1)',
            'space_complexity': 'O(1)',
            'issues': [],
            'recommendations': []
        }
        
        # Track loop nesting and recursive calls
        loop_stack = []
        max_loop_depth = 0
        recursive_calls = 0
        data_structures = {}
        function_calls = {}
        
        # Get function names
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        # Analyze the AST
        for node in ast.walk(tree):
            # Track loops and their nesting
            if isinstance(node, (ast.For, ast.While)):
                loop_stack.append(node)
                max_loop_depth = max(max_loop_depth, len(loop_stack))
            elif isinstance(node, ast.Call):
                # Check for recursive calls
                if isinstance(node.func, ast.Name) and node.func.id in function_names:
                    recursive_calls += 1
                
                # Track function calls for complexity analysis
                func_name = "unknown"
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                function_calls[func_name] = function_calls.get(func_name, 0) + 1
            
            # Count data structure usage
            if isinstance(node, ast.List):
                data_structures['list'] = data_structures.get('list', 0) + 1
            elif isinstance(node, ast.Dict):
                data_structures['dict'] = data_structures.get('dict', 0) + 1
            elif isinstance(node, ast.Set):
                data_structures['set'] = data_structures.get('set', 0) + 1
            elif isinstance(node, ast.ListComp):
                data_structures['list'] = data_structures.get('list', 0) + 1
            elif isinstance(node, ast.DictComp):
                data_structures['dict'] = data_structures.get('dict', 0) + 1
            elif isinstance(node, ast.SetComp):
                data_structures['set'] = data_structures.get('set', 0) + 1
        
        # Determine time complexity based on analysis
        if recursive_calls > 0:
            analysis['time_complexity'] = 'O(2^n)'  # Exponential for recursion
            analysis['issues'].append('Recursive calls may lead to exponential time complexity')
            analysis['recommendations'].append('Consider using iterative approaches or memoization')
        elif max_loop_depth > 1:
            analysis['time_complexity'] = f'O(n^{max_loop_depth})'
            analysis['issues'].append(f'Nested loops (depth {max_loop_depth}) can lead to polynomial time complexity')
            analysis['recommendations'].append('Consider optimizing with more efficient algorithms')
        elif max_loop_depth == 1:
            analysis['time_complexity'] = 'O(n)'
        else:
            analysis['time_complexity'] = 'O(1)'
        
        # Check for specific function calls that affect complexity
        for func, count in function_calls.items():
            if func in ['sort', 'sorted']:
                analysis['time_complexity'] = 'O(n log n)' if analysis['time_complexity'] == 'O(1)' else analysis['time_complexity'] + ' + O(n log n)'
                analysis['issues'].append(f'Using {func} adds O(n log n) time complexity')
        
        # Determine space complexity
        total_structures = sum(data_structures.values())
        if total_structures > 3:
            analysis['space_complexity'] = 'O(n)'
            analysis['issues'].append('Multiple data structures may increase space complexity')
            analysis['recommendations'].append('Consider reusing data structures or streaming data')
        elif 'list' in data_structures or 'dict' in data_structures or 'set' in data_structures:
            analysis['space_complexity'] = 'O(n)'
        else:
            analysis['space_complexity'] = 'O(1)'
        
        return analysis
    except Exception as e:
        return {
            'time_complexity': 'Unknown',
            'space_complexity': 'Unknown',
            'issues': [f'Analysis error: {str(e)}'],
            'recommendations': ['Check syntax errors']
        }

def generate_optimization_recommendations(analysis, exec_time, memory_used):
    """Generate recommendations based on code analysis and performance metrics"""
    recommendations = analysis['recommendations']
    
    if exec_time > 1.0:
        recommendations.append("Your code is running slowly. Consider optimizing algorithms.")
    elif exec_time > 0.1:
        recommendations.append("Performance is acceptable but could be improved.")
    
    if memory_used > 10.0:
        recommendations.append("High memory usage detected. Consider using generators or streaming.")
    elif memory_used > 1.0:
        recommendations.append("Memory usage is moderate. Could be optimized for large inputs.")
    
    return recommendations

def create_performance_plot(time_data, memory_data):
    """Create a performance visualization plot"""
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    plt.bar(['Execution Time'], [time_data], color='blue')
    plt.ylabel('Seconds')
    plt.title('Execution Time')
    
    plt.subplot(1, 2, 2)
    plt.bar(['Memory Used'], [memory_data], color='green')
    plt.ylabel('MB')
    plt.title('Memory Usage')
    
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode the image to base64
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return image_base64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_code():
    data = request.json
    code = data.get('code', '')
    
    # Create a safe execution environment
    local_vars = {}
    output_capture = io.StringIO()
    
    # Add output capture to builtins
    execution_env = safe_builtins.copy()
    execution_env['print'] = lambda *args, **kwargs: print(*args, **kwargs, file=output_capture)
    
    try:
        # Measure execution time
        exec_wrapped = measure_time(exec)
        result, exec_time = exec_wrapped(code, execution_env, local_vars)
        
        # Measure memory usage
        mem_wrapped = measure_memory(exec)
        result, memory_used = mem_wrapped(code, execution_env, local_vars)
        
        # Get captured output
        output = output_capture.getvalue()
        
        # Analyze code complexity
        complexity_analysis = analyze_complexity(code)
        
        # Generate recommendations
        recommendations = generate_optimization_recommendations(
            complexity_analysis, exec_time, memory_used
        )
        
        # Create performance visualization
        plot_image = create_performance_plot(exec_time, memory_used)
        
        # Generate execution visualization
        visualizer = CodeVisualizer()
        execution_steps = visualizer.visualize_execution(code, execution_env.copy())
        
        # Generate AST tree visualization
        tree_visualizer = TreeVisualizer()
        ast_tree = tree_visualizer.generate_ast_tree(code)
        
        # Generate memory visualization
        memory_visualizer = MemoryVisualizer()
        memory_map = memory_visualizer.visualize_memory(code, execution_env.copy())
        
        return jsonify({
            'success': True,
            'execution_time': round(exec_time, 4),
            'memory_used': round(memory_used, 2),
            'time_complexity': complexity_analysis['time_complexity'],
            'space_complexity': complexity_analysis['space_complexity'],
            'issues': complexity_analysis['issues'],
            'recommendations': recommendations,
            'performance_plot': plot_image,
            'output': output,
            'execution_steps': execution_steps,
            'ast_tree': ast_tree,
            'memory_map': memory_map
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'execution_time': 0,
            'memory_used': 0,
            'time_complexity': 'Unknown',
            'space_complexity': 'Unknown',
            'issues': [f'Execution error: {str(e)}'],
            'recommendations': ['Fix runtime errors in your code'],
            'performance_plot': None,
            'output': None,
            'execution_steps': [],
            'ast_tree': [],
            'memory_map': []
        })
    finally:
        output_capture.close()

@app.route('/save_code', methods=['POST'])
def save_code():
    data = request.json
    code = data.get('code', '')
    filename = data.get('filename', '')
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"python_code_{timestamp}.py"
    elif not filename.endswith('.py'):
        filename += '.py'
    
    try:
        # Save code to file
        filepath = os.path.join('saved_code', filename)
        with open(filepath, 'w') as f:
            f.write(code)
        
        return jsonify({
            'success': True,
            'message': f'Code saved successfully as {filename}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving file: {str(e)}'
        })

@app.route('/save_report', methods=['POST'])
def save_report():
    data = request.json
    code = data.get('code', '')
    analysis_data = data.get('analysis_data', {})
    filename = data.get('filename', '')
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"code_analysis_{timestamp}.txt"
    elif not filename.endswith('.txt'):
        filename += '.txt'
    
    try:
        # Create a comprehensive report
        report = f"Code Analysis Report\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "CODE:\n"
        report += "=" * 50 + "\n"
        report += code + "\n\n"
        
        report += "PERFORMANCE METRICS:\n"
        report += "=" * 50 + "\n"
        report += f"Execution Time: {analysis_data.get('execution_time', 0)} seconds\n"
        report += f"Memory Used: {analysis_data.get('memory_used', 0)} MB\n"
        report += f"Time Complexity: {analysis_data.get('time_complexity', 'Unknown')}\n"
        report += f"Space Complexity: {analysis_data.get('space_complexity', 'Unknown')}\n\n"
        
        if analysis_data.get('issues'):
            report += "ISSUES:\n"
            report += "=" * 50 + "\n"
            for issue in analysis_data.get('issues', []):
                report += f"- {issue}\n"
            report += "\n"
        
        if analysis_data.get('recommendations'):
            report += "RECOMMENDATIONS:\n"
            report += "=" * 50 + "\n"
            for rec in analysis_data.get('recommendations', []):
                report += f"- {rec}\n"
            report += "\n"
        
        if analysis_data.get('output'):
            report += "PROGRAM OUTPUT:\n"
            report += "=" * 50 + "\n"
            report += analysis_data.get('output', '') + "\n\n"
        
        if analysis_data.get('execution_steps'):
            report += "EXECUTION STEPS:\n"
            report += "=" * 50 + "\n"
            for step in analysis_data.get('execution_steps', []):
                report += f"{step}\n"
            report += "\n"
        
        # Save report to file
        filepath = os.path.join('saved_code', filename)
        with open(filepath, 'w') as f:
            f.write(report)
        
        return jsonify({
            'success': True,
            'message': f'Report saved successfully as {filename}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving report: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True)