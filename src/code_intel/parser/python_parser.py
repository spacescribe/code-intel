import ast
import os


class CallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)

        self.generic_visit(node)


def get_python_files(repo_path: str):
    python_files = []

    if os.path.isfile(repo_path) and repo_path.endswith(".py"):
        return [repo_path]

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files


def parse_repo(repo_path: str):
    results = []
    python_files = get_python_files(repo_path)

    for file_path in python_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                visitor = CallVisitor()
                visitor.visit(node)

                function_data = {
                    "file": file_path,
                    "function_name": node.name,
                    "source": ast.get_source_segment(content, node),
                    "calls": visitor.calls,
                }

                results.append(function_data)

    return results