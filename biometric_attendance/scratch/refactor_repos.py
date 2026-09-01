import os
import glob
import ast

repo_dir = r"c:\Users\PCSMO\Desktop\biometric system\biometric_attendance\infrastructure\repositories"
files = glob.glob(os.path.join(repo_dir, "*.py"))

for file_path in files:
    if "__init__" in file_path:
        continue

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    lines = source.splitlines()

    # We need to process from bottom to top so line numbers don't shift
    methods_to_rewrite = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name == "__init__":
                        methods_to_rewrite.append((item, "init"))
                    elif not item.name.startswith("_"):
                        methods_to_rewrite.append((item, "method"))

    methods_to_rewrite.sort(key=lambda x: x[0].lineno, reverse=True)

    for item, mtype in methods_to_rewrite:
        start_line = item.lineno - 1
        # Find end line
        end_line = item.end_lineno
        
        if mtype == "init":
            # Just replace self._session = session with pass
            for i in range(start_line, end_line):
                if "self._session = session" in lines[i]:
                    lines[i] = lines[i].replace("self._session = session", "pass")
                if "session: Session" in lines[i]:
                    lines[i] = lines[i].replace("session: Session", "")
        elif mtype == "method":
            # Add with get_session() as session: at the start of the body
            body_start = item.body[0].lineno - 1
            
            # Indent the body
            for i in range(body_start, end_line):
                lines[i] = "    " + lines[i]
                lines[i] = lines[i].replace("self._session", "session")
            
            # Insert the context manager
            indent = " " * item.body[0].col_offset
            lines.insert(body_start, indent + "with get_session() as session:")
            lines.insert(body_start, indent + "from biometric_attendance.infrastructure.data.database import get_session")

    new_source = "\n".join(lines) + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_source)

print("Refactored all repositories.")
