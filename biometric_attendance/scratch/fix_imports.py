import os
import glob
import ast

repo_dir = r"c:\Users\PCSMO\Desktop\biometric system\biometric_attendance\infrastructure\repositories"
files = glob.glob(os.path.join(repo_dir, "*.py"))

for file_path in files:
    if "__init__" in file_path:
        continue

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Find the line with from __future__ import annotations
    future_line = -1
    for i, line in enumerate(lines):
        if "from __future__ import annotations" in line:
            future_line = i
            break
            
    # Find the auto_session import and remove it if it exists (from my bad script)
    for i in range(len(lines) - 1, -1, -1):
        if "import auto_session" in lines[i]:
            lines.pop(i)

    # Insert it correctly
    insert_idx = future_line + 1 if future_line != -1 else 0
    lines.insert(insert_idx, "from biometric_attendance.infrastructure.data.database import auto_session")
    
    new_source = "\n".join(lines) + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_source)

print("Fixed imports in all repositories.")
