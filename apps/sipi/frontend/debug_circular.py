# debug_circular.py
import sys

print("=== DIAGNÓSTICO DE IMPORTACIÓN ===\n")

# Paso 1: Verificar que Base está limpio
print("1. Importando Base...")
from db.registry importAppBase
print(f"   Tablas en metadata: {list(AppBase.metadata.tables.keys())}")

# Paso 2: Importar Users
print("\n2. Importando Users...")
from models.users import Usuario
print(f"   Tablas: {list(AppBase.metadata.tables.keys())}")

# Paso 3: Importar Tipologías
print("\n3. Importando Tipologías...")
from models.tipografia import TipoVia
print(f"   Tablas: {list(AppBase.metadata.tables.keys())}")

# Paso 4: Importar Geografía (verificar que se registre correctamente)
print("\n4. Importando Geografía...")
from models.geografia import Provincia
print(f"   Tablas: {list(AppBase.metadata.tables.keys())}")

if 'provincias' not in AppBase.metadata.tables:
    print("   ❌ ERROR CRÍTICO: provincias no se registró!")
    sys.exit(1)
else:
    print("   ✅ provincias registrada correctamente")

# Paso 5: Verificar qué pasa al importar actores_base
print("\n5. Importando actores_base...")
try:
    from models.actores_base import PersonaMixin
    print(f"   Tablas: {list(AppBase.metadata.tables.keys())}")
    if 'provincias' not in AppBase.metadata.tables:
        print("   ❌ ERROR: provincias desapareció al importar actores_base!")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Paso 6: Verificar notarios
print("\n6. Importando notarios...")
try:
    from models.notarios import Notaria
    print(f"   Tablas: {list(AppBase.metadata.tables.keys())}")
    if 'provincias' not in AppBase.metadata.tables:
        print("   ❌ ERROR: provincias desapareció al importar notarios!")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Paso 7: Finalmente administraciones
print("\n7. Importando administraciones...")
try:
    from models.administraciones import Administracion
    print(f"   Tablas: {list(AppBase.metadata.tables.keys())}")
    print("   ✅ ÉXITO!")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()