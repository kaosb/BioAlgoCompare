
## Checklist de Migración para WOA

### Archivos generados:
- [x] algorithms/woa_v2.py
- [x] tests/test_woa_v2_migration.py

### Tareas completadas:

1. **Revisar imports**
   - [x] Verificar que todos los imports necesarios estén incluidos
   - [x] Eliminar imports no utilizados

2. **Clase Individual (WhaleV2)**
   - [x] Revisar atributos especiales en __init__ (no tiene especiales)
   - [x] Implementar initialize() correctamente
   - [x] Migrar lógica de move() usando MoveContext
   - [x] Verificar que se invalida fitness cuando cambia posición

3. **Clase Algorithm (WOAV2)**
   - [x] Agregar parámetros específicos del algoritmo (no requiere)
   - [x] Implementar _create_move_context() con parámetros necesarios
   - [x] Verificar _should_sort_population() (no ordena)
   - [x] Completar summary() con información específica

4. **Tests**
   - [x] Verificar que test_initialization_compatibility pasa
   - [x] Verificar que test_individual_creation pasa
   - [x] Verificar que test_reproducibility pasa
   - [x] Agregar tests específicos del algoritmo (tests básicos OK)

5. **Documentación**
   - [x] Agregar docstrings descriptivos
   - [x] Incluir referencias bibliográficas
   - [x] Documentar particularidades del algoritmo

6. **Validación final**
   - [x] Ejecutar todos los tests (3/3 pasando)
   - [x] Comparar rendimiento con v1 (v2 obtiene mejor fitness)
   - [x] Verificar convergencia en problemas de prueba

### Parámetros originales de move():
best_whale, a, a2, leader_type

### Notas:
- Los parámetros ahora vienen en el MoveContext
- Usar context.get_param() para parámetros específicos
- Siempre invalidar fitness después de modificar position
