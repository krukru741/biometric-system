import re

path = r'c:\Users\PCSMO\Desktop\biometric system\biometric_attendance\app\views\workforce\employees_view.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace QFormLayout implicit labels with explicit QLabels having FormLabel objectName
def repl(m):
    text = m.group(1)
    widget = m.group(2)
    return f'''lbl = QLabel("{text}")\n        lbl.setObjectName("FormLabel")\n        form_layout.addRow(lbl, {widget})'''

content = re.sub(r'form_layout\.addRow\("([^"]+)",\s*([^)]+)\)', repl, content)

# Also apply it to the section headers like QLabel("<b>Personal Information</b>")
def header_repl(m):
    text = m.group(1)
    return f'''header = QLabel("{text}")\n        header.setObjectName("FormLabel")\n        form_layout.addRow(header)'''

content = re.sub(r'form_layout\.addRow\(QLabel\("([^"]+)"\)\)', header_repl, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
