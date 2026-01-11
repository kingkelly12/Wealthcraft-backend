#!/usr/bin/env python3
"""
Fix Python 3.10+ union syntax to Python 3.8 compatible Optional syntax
"""
import re
import os

schema_dir = "/home/kelly_koome/Devops/wealthcraft-legacy-sim/my_flask_app/app/schemas"

# Pattern to match: type | None
pattern = r'(\w+):\s+(\w+)\s+\|\s+None'
replacement = r'\1: Optional[\2]'

files_to_fix = [
    "chat_schema.py",
    "balance_schema.py",
    "job_schema.py",
    "loan_schema.py",
    "life_event_schema.py",
    "education_schema.py",
    "rental_schema.py"
]

for filename in files_to_fix:
    filepath = os.path.join(schema_dir, filename)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if Optional is already imported
    if 'from typing import Optional' not in content:
        # Add Optional import
        if 'from typing import' in content:
            # Add to existing typing import
            content = re.sub(
                r'from typing import (.*)',
                r'from typing import \1, Optional',
                content
            )
        else:
            # Add new typing import after other imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from pydantic') or line.startswith('from decimal'):
                    lines.insert(i + 1, 'from typing import Optional')
                    break
            content = '\n'.join(lines)
    
    # Replace type | None with Optional[type]
    content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filename}")

print("\n🎉 All schema files fixed!")
