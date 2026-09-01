import glob
import os
import re

repo_dir = r"c:\Users\PCSMO\Desktop\biometric system\biometric_attendance\infrastructure\repositories"
files = glob.glob(os.path.join(repo_dir, "*.py"))

def refactor_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Replace __init__ to not save the session
    content = re.sub(
        r"def __init__\(self, session: Session\) -> None:\s+self._session = session",
        r"def __init__(self) -> None:\n        pass",
        content
    )
    
    # Wait, what if the method takes **kwargs? It's fine.
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

for f in files:
    if "__init__" not in f:
        print(f)
