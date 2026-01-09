import ast
import json

class TreeVisualizer:
    def __init__(self):
        self.node_id = 0
    
    def generate_ast_tree(self, code):
        """Generate a tree representation of the AST"""
        try:
            tree = ast.parse(code)
            ast_tree = self._parse_ast_node(tree)
            return ast_tree
        except Exception as e:
            return [f"AST parsing error: {str(e)}"]
    
    def _parse_ast_node(self, node, depth=0):
        """Recursively parse AST node into a tree structure"""
        if not isinstance(node, ast.AST):
            return {
                'id': self.node_id,
                'type': 'Literal',
                'value': str(node),
                'depth': depth,
                'children': []
            }
        
        self.node_id += 1
        node_id = self.node_id
        
        node_info = {
            'id': node_id,
            'type': type(node).__name__,
            'depth': depth,
            'children': []
        }
        
        # Add line number if available
        if hasattr(node, 'lineno') and node.lineno:
            node_info['lineno'] = node.lineno
        
        # Add specific attributes based on node type
        if isinstance(node, ast.Name):
            node_info['name'] = node.id
        elif isinstance(node, ast.FunctionDef):
            node_info['name'] = node.name
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                node_info['func'] = node.func.id
        elif isinstance(node, ast.Assign):
            if len(node.targets) > 0 and isinstance(node.targets[0], ast.Name):
                node_info['target'] = node.targets[0].id
        elif isinstance(node, ast.Constant):
            node_info['value'] = repr(node.value)
        
        # Recursively process child nodes
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        child_node = self._parse_ast_node(item, depth + 1)
                        child_node['field'] = field
                        node_info['children'].append(child_node)
            elif isinstance(value, ast.AST):
                child_node = self._parse_ast_node(value, depth + 1)
                child_node['field'] = field
                node_info['children'].append(child_node)
        
        return node_info
    
    def format_ast_tree(self, ast_tree):
        """Format the AST tree for display"""
        formatted = []
        self._format_node(ast_tree, formatted, 0)
        return formatted
    
    def _format_node(self, node, formatted, indent_level):
        """Recursively format a node for display"""
        indent = "  " * indent_level
        
        if node['type'] == 'Literal':
            formatted.append(f"{indent}└── {node['value']}")
            return
        
        node_line = f"{indent}└── {node['type']}"
        
        # Add specific info based on node type
        if 'name' in node:
            node_line += f" ({node['name']})"
        elif 'func' in node:
            node_line += f" (call: {node['func']})"
        elif 'target' in node:
            node_line += f" (assign to: {node['target']})"
        elif 'value' in node:
            node_line += f" (value: {node['value']})"
        
        # Add line number if available
        if 'lineno' in node:
            node_line += f" [line {node['lineno']}]"
        
        formatted.append(node_line)
        
        # Process children
        for child in node['children']:
            self._format_node(child, formatted, indent_level + 1)