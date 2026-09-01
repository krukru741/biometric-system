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

    has_changes = False
    for item, mtype in methods_to_rewrite:
        has_changes = True
        start_line = item.lineno - 1
        end_line = item.end_lineno
        
        if mtype == "init":
            for i in range(start_line, end_line):
                if "session: Session" in lines[i]:
                    lines[i] = lines[i].replace("session: Session", "session: Session | None = None")
        elif mtype == "method":
            body_start = item.body[0].lineno - 1
            
            # Indent the body
            for i in range(body_start, end_line):
                lines[i] = "    " + lines[i]
                lines[i] = lines[i].replace("self._session", "session")
            
            # Insert the context manager
            indent = " " * item.body[0].col_offset
            lines.insert(body_start, indent + "with auto_session(self._session) as session:")

    if has_changes:
        # Add import at the top
        for i, line in enumerate(lines):
            if line.startswith("import") or line.startswith("from "):
                lines.insert(i, "from biometric_attendance.infrastructure.data.database import auto_session")
                break
                
        new_source = "\n".join(lines) + "\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_source)

print("Refactored all repositories for Middle Ground.")
