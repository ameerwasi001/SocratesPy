from sys import argv
import ast
import astunparse
import visitors

if len(argv) != 3: 
    raise IOError(f"Expected two arguments formatted like [filename] [input file's name] [output file's name] but got {len(argv)} arguments")

file_to_open = argv[1]
file_to_write = argv[2]

with open(file_to_open, "r") as f:
    content = f.read()
    new_tree = visitors.create_knowledgebase("nodes", "KnowledgeBase", content)

with open(file_to_write, "w") as f:
    content = astunparse.unparse(new_tree)
    f.write(content)