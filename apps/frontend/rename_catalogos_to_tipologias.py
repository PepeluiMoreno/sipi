#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para renombrar completamente 'catalogos' a 'tipologias' en todo el proyecto
"""

import os
import shutil
import re

def rename_file(old_path, new_path):
    """Renombra un archivo si existe"""
    if os.path.exists(old_path):
        print(f"Renombrando archivo: {old_path} -> {new_path}")
        shutil.move(old_path, new_path)
        return True
    return False

def rename_directory(old_path, new_path):
    """Renombra un directorio si existe"""
    if os.path.exists(old_path):
        print(f"Renombrando directorio: {old_path} -> {new_path}")
        shutil.move(old_path, new_path)
        return True
    return False

def replace_in_file(file_path, replacements):
    """Reemplaza múltiples patrones en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Actualizado: {file_path}")
            return True
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
    return False

def main():
    base_path = r'C:\Users\admin\dev\sipi-frontend\src'

    # 1. Renombrar archivos específicos
    print("\n=== Renombrando archivos ===")
    rename_file(
        os.path.join(base_path, 'modules', 'catalogos', 'views', 'ConfigCatalogos.vue'),
        os.path.join(base_path, 'modules', 'catalogos', 'views', 'ConfigTipologias.vue')
    )

    # 2. Definir reemplazos de texto
    replacements = [
        # Paths y rutas
        ('/config/catalogos', '/config/tipologias'),
        ("'/config/catalogos'", "'/config/tipologias'"),
        ('"/config/catalogos"', '"/config/tipologias"'),
        ('/modules/catalogos/', '/modules/tipologias/'),
        ("'../../catalogos/", "'../../tipologias/"),
        ('"../../catalogos/', '"../../tipologias/'),
        ("'/src/modules/catalogos/", "'/src/modules/tipologias/"),
        ('"/src/modules/catalogos/', '"/src/modules/tipologias/'),

        # Nombres de componentes
        ('ConfigCatalogos', 'ConfigTipologias'),

        # Variables y constantes
        ('catalogoSeleccionado', 'tipologiaSeleccionada'),
        ('nombresCatalogos', 'nombresTipologias'),
        ('descripcionesCatalogos', 'descripcionesTipologias'),
        ('catalogos', 'tipologias'),
        ('Catalogos', 'Tipologias'),

        # Textos en español (UI)
        ('Configuración de Catálogos', 'Configuración de Tipologías'),
        ('Gestión de Catálogos', 'Gestión de Tipologías'),
        ('Gestione los catálogos del sistema', 'Gestione las tipologías del sistema'),
        ('Catálogos del Sistema', 'Tipologías del Sistema'),
        ('Catálogos disponibles', 'Tipologías disponibles'),
        ('Seleccione un catálogo', 'Seleccione una tipología'),
        ('catálogo', 'tipología'),
        ('catálogos', 'tipologías'),
        ('Catálogo', 'Tipología'),
        ('Catálogos', 'Tipologías'),
        ('del catálogo', 'de la tipología'),
        ('los catálogos', 'las tipologías'),

        # Comentarios
        ('// src/modules/catalogos/', '// src/modules/tipologias/'),
        ('Wrapper para Catálogos', 'Wrapper para Tipologías'),
        ('lógica específica de catálogos', 'lógica específica de tipologías'),
        ('Nombres legibles para los catálogos', 'Nombres legibles para las tipologías'),
        ('Nombres legibles y descripciones para los catálogos', 'Nombres legibles y descripciones para las tipologías'),

        # Composables
        ('useCatalogo', 'useTipologia'),
    ]

    # 3. Actualizar archivos
    print("\n=== Actualizando contenido de archivos ===")
    files_to_update = [
        # Router
        os.path.join(base_path, 'modules', 'core', 'router', 'index.js'),

        # Layout
        os.path.join(base_path, 'modules', 'core', 'layouts', 'DashboardLayout.vue'),

        # Vistas de catalogos (ahora tipologias)
        os.path.join(base_path, 'modules', 'catalogos', 'views', 'ConfigTipologias.vue'),

        # Componentes de catalogos
        os.path.join(base_path, 'modules', 'catalogos', 'components', 'Config.vue'),
        os.path.join(base_path, 'modules', 'catalogos', 'components', 'ConfigCatalogs.vue'),
        os.path.join(base_path, 'modules', 'catalogos', 'components', 'CatalogoManager.vue'),

        # Composables
        os.path.join(base_path, 'modules', 'catalogos', 'composables', 'index.js'),
        os.path.join(base_path, 'modules', 'catalogos', 'composables', 'useCatalogoBase.js'),
        os.path.join(base_path, 'modules', 'catalogos', 'composables', 'useCatalogoGenerico.js'),
        os.path.join(base_path, 'modules', 'catalogos', 'composables', 'useCatalogoBaseStrawchemy.js'),

        # Agentes que importan useCatalogoBase
        os.path.join(base_path, 'modules', 'agentes', 'views', 'AdministracionesView.vue'),
        os.path.join(base_path, 'modules', 'agentes', 'views', 'NotariasView.vue'),
        os.path.join(base_path, 'modules', 'agentes', 'views', 'RegistrosPropiedadView.vue'),

        # GraphQL
        os.path.join(base_path, 'modules', 'documentos', 'graphql', 'localidadQueries.js'),
    ]

    for file_path in files_to_update:
        if os.path.exists(file_path):
            replace_in_file(file_path, replacements)
        else:
            print(f"Archivo no encontrado: {file_path}")

    # 4. Renombrar directorio (al final para no romper paths)
    print("\n=== Renombrando directorio principal ===")
    rename_directory(
        os.path.join(base_path, 'modules', 'catalogos'),
        os.path.join(base_path, 'modules', 'tipologias')
    )

    print("\n=== Proceso completado ===")
    print("NOTA: Puede que necesites actualizar imports manualmente en algunos archivos")
    print("      Revisa especialmente los archivos en modules/tipologias/")

if __name__ == '__main__':
    main()
