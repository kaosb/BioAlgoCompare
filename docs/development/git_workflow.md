# Flujo de Trabajo Git

Este documento describe el flujo de trabajo GitFlow utilizado en este proyecto para gestionar el desarrollo, las versiones y las contribuciones.

## Estructura de Ramas

### Ramas Principales

- **`main`**: Código en producción, estable y listo para ser utilizado.
- **`develop`**: Rama principal de desarrollo, contiene los últimos cambios que están siendo preparados.

### Ramas de Soporte

- **`feature/*`**: Desarrollo de nuevas funcionalidades. Derivadas de `develop`.
- **`release/*`**: Preparación para una nueva versión. Derivadas de `develop`.
- **`hotfix/*`**: Correcciones urgentes en producción. Derivadas de `main`.
- **`refactor/*`**: Refactorizaciones de código sin nuevas funcionalidades. Derivadas de `develop`.

```
main    ──────────●────────────────●───●──────────────────
                   \               /   /
develop ─────●─────●──────●──────●────●─────────────────
            /     /      /      /
feature/1  ──────●      /      /
                       /      /
feature/2  ────────────●     /
                            /
hotfix/1   ────────────────●
```

## Procesos Detallados

### 1. Desarrollo de Nuevas Funcionalidades

```bash
# Crear rama feature
git checkout develop
git pull origin develop
git checkout -b feature/nombre-caracteristica

# Desarrollar, hacer commits, y al finalizar
git push origin feature/nombre-caracteristica

# Crear Pull Request en GitHub: feature/nombre-caracteristica → develop
```

**Buenas prácticas:**
- Mantener las ramas de características enfocadas y específicas
- Actualizar regularmente desde develop para evitar conflictos grandes
- Escribir tests para validar la nueva funcionalidad

### 2. Preparación de Versiones

```bash
# Crear rama release
git checkout develop
git pull origin develop
git checkout -b release/vX.Y.Z

# Ajustes finales, correcciones, actualización de versiones
git push origin release/vX.Y.Z

# Crear Pull Request en GitHub: release/vX.Y.Z → main
# Después de merge a main, crear PR: release/vX.Y.Z → develop
```

**Políticas de release:**
- No desarrollar nuevas funcionalidades en ramas de release, solo correcciones
- Actualizar el número de versión en el archivo VERSION
- Actualizar toda la documentación relevante

### 3. Correcciones Urgentes

```bash
# Crear rama hotfix
git checkout main
git pull origin main
git checkout -b hotfix/descripcion-problema

# Implementar corrección
git push origin hotfix/descripcion-problema

# Crear Pull Request en GitHub: hotfix/descripcion-problema → main
# Después de merge a main, crear PR: hotfix/descripcion-problema → develop
```

**Consideraciones para hotfixes:**
- Deben ser cambios mínimos y enfocados
- Requieren pruebas exhaustivas para evitar nuevos problemas
- Siempre deben ser incorporados tanto en main como en develop

### 4. Refactorización

```bash
# Crear rama refactor
git checkout develop
git pull origin develop
git checkout -b refactor/descripcion-cambios

# Implementar refactorización
git push origin refactor/descripcion-cambios

# Crear Pull Request en GitHub: refactor/descripcion-cambios → develop
```

## Convenciones de Commit

Seguimos los estándares de [Conventional Commits](https://www.conventionalcommits.org/):

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat:` | Nueva funcionalidad | `feat: agregar algoritmo EGTO` |
| `fix:` | Corrección de errores | `fix: corregir cálculo de fitness en WOA` |
| `docs:` | Cambios en documentación | `docs: actualizar instrucciones de benchmark` |
| `style:` | Cambios de formato que no afectan el código | `style: mejorar formato en base.py` |
| `refactor:` | Restructuración de código sin cambiar comportamiento | `refactor: reorganizar algoritmos` |
| `perf:` | Mejoras de rendimiento | `perf: optimizar cálculo de distancias en VRP` |
| `test:` | Adición o corrección de pruebas | `test: añadir tests para FOA` |
| `chore:` | Tareas de mantenimiento, cambios en el build, etc. | `chore: actualizar .gitignore` |

### Estructura de Mensajes de Commit:

```
<tipo>[alcance opcional]: <descripción>

[cuerpo opcional]

[pie opcional]
```

Ejemplo completo:
```
feat(algorithm): añadir implementación de Enhanced GTO

- Implementar algoritmo EGTO basado en el paper de Hassan (2024)
- Añadir parámetros adaptativos
- Incorporar estrategia de exploración mejorada

Closes #42
```

## Proceso de Pull Request

1. **Creación**: 
   - Incluir descripción detallada del cambio
   - Referenciar issues relacionados (`Closes #123`)
   - Añadir etiquetas relevantes

2. **Revisión**:
   - Solicitar explícitamente revisores
   - Responder a todos los comentarios
   - Resolver todos los hilos de conversación

3. **Verificación**:
   - Asegurar que todas las pruebas pasan
   - Verificar que la documentación está actualizada
   - Confirmar que no hay conflictos de merge

4. **Aprobación**:
   - Requerir al menos una aprobación
   - Obtener aprobación de los revisores asignados

5. **Merge**:
   - Preferir squash para mantener un historial limpio
   - Mantener el mensaje de commit descriptivo y coherente

## Etiquetado de Versiones

Después de cada fusión a `main` desde una rama `release/` o `hotfix/`, crear una etiqueta de versión:

```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Versión X.Y.Z"
git push origin vX.Y.Z
```

### Política de Versionado Semántico:

- **X (Major)**: Cambios incompatibles con versiones anteriores
- **Y (Minor)**: Nuevas funcionalidades manteniendo compatibilidad
- **Z (Patch)**: Correcciones de errores manteniendo compatibilidad

## Estrategia de Organización de Repositorio

### Archivos a excluir del control de versiones:

```
# Logs
*.log
benchmark.log
massive_benchmark.log
analyze_massive.log

# Resultados masivos y temporales
results/massive_*/checkpoints/
results/*_parallel_info.json
results/analysis_*
results/statistical_analysis_*
results/benchmark_*
*.json.gz

# Directorios de backup
backup/
*/backup/
algorithms/backup/
```

### Datos Importantes a Preservar:

Aunque algunos archivos de resultados no se versionan, es crucial preservar:
- `results/massive_1000runs/massive_benchmark_summary.csv`
- `results/statistical_analysis_1000runs/algorithm_comparison.csv`
- Archivos HTML de reportes finales

## Consejos y Buenas Prácticas

1. **Mantener commits pequeños y enfocados**
   - Cada commit debe representar un cambio lógico y coherente
   - Evitar mezclar múltiples cambios no relacionados

2. **Actualizar ramas con regularidad**
   - Hacer pull o rebase desde develop con frecuencia
   - Resolver conflictos temprano para evitar problemas mayores

3. **No hacer push directo a main ni develop**
   - Siempre trabajar en ramas de soporte
   - Utilizar Pull Requests para integrar cambios

4. **Mantener nombres descriptivos para ramas**
   - `feature/enhanced-gto-algorithm`
   - `hotfix/fix-distance-calculation-bug`
   - `refactor/reorganize-algorithm-structure`

5. **Revisar el diff antes de commit**
   - Usar `git diff` o `git diff --staged` para revisar cambios
   - Asegurarse de no incluir cambios accidentales o debug code

6. **Usar mensaje de commit descriptivo**
   - Explicar el qué y el porqué, no solo el cómo
   - Referenciar tickets o issues cuando sea aplicable