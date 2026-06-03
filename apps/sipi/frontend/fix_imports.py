#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix remaining import issues after catalogos → tipologias rename
"""

import os
import re

def fix_file(file_path, replacements):
    """Fix imports in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

base_path = r'C:\Users\admin\dev\sipi-frontend\src\modules'

# Fix files that still reference useTipologiaBase incorrectly
files_to_fix = [
    # Agentes views - change from '/useTipologiaBase' to '/useCatalogoBase'
    (os.path.join(base_path, 'agentes', 'views', 'AdministracionesView.vue'), [
        ("from '../../tipologias/composables/useTipologiaBase'", "from '../../tipologias/composables'"),
    ]),
    (os.path.join(base_path, 'agentes', 'views', 'NotariasView.vue'), [
        ("from '../../tipologias/composables/useTipologiaBase'", "from '../../tipologias/composables'"),
    ]),
    (os.path.join(base_path, 'agentes', 'views', 'RegistrosPropiedadView.vue'), [
        ("from '../../tipologias/composables/useTipologiaBase'", "from '../../tipologias/composables'"),
    ]),
]

print("=== Fixing import paths ===")
for file_path, replacements in files_to_fix:
    if os.path.exists(file_path):
        fix_file(file_path, replacements)
    else:
        print(f"File not found: {file_path}")

print("\n=== Done ===")
