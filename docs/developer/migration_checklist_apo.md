
## Checklist de Migración para APO

### Archivos generados:
- [ ] algorithms/APO_v2.py
- [ ] tests/test_APO_v2_migration.py

### Tareas pendientes:

1. **Revisar imports**
   - [ ] Verificar que todos los imports necesarios estén incluidos
   - [ ] Eliminar imports no utilizados

2. **Clase Individual (ProtozoaV2)**
   - [ ] Revisar atributos especiales en __init__
   - [ ] Implementar initialize() correctamente
   - [ ] Migrar lógica de move() usando MoveContext
   - [ ] Verificar que se invalida fitness cuando cambia posición

3. **Clase Algorithm (APOV2)**
   - [ ] Agregar parámetros específicos del algoritmo
   - [ ] Implementar _create_move_context() con parámetros necesarios
   - [ ] Verificar _should_sort_population()
   - [ ] Completar summary() con información específica

4. **Tests**
   - [ ] Verificar que test_initialization_compatibility pasa
   - [ ] Verificar que test_individual_creation pasa
   - [ ] Verificar que test_reproducibility pasa
   - [ ] Agregar tests específicos del algoritmo

5. **Documentación**
   - [ ] Agregar docstrings descriptivos
   - [ ] Incluir referencias bibliográficas
   - [ ] Documentar particularidades del algoritmo

6. **Validación final**
   - [ ] Ejecutar todos los tests
   - [ ] Comparar rendimiento con v1
   - [ ] Verificar convergencia en problemas de prueba

### Parámetros originales de move():
population, iteration, max_iterations, pf_max, npairs

### Notas:
- Los parámetros ahora vienen en el MoveContext
- Usar context.get_param() para parámetros específicos
- Siempre invalidar fitness después de modificar position
