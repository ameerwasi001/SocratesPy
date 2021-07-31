import ast
import astunparse
import visitors

with open("testFile.py", "r") as f:
    content = f.read()
    my_tree = ast.parse(content)
    new_tree = visitors.SelectiveVistor().initialize("nodes", "Solver").visit(my_tree)

with open("testFileModified.py", "w") as f:
    content = astunparse.unparse(new_tree)
    f.write(content)