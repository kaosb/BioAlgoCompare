# Guía de Contribución

¡Gracias por tu interés en contribuir a BioAlgoCompare! Esta guía proporciona toda la información necesaria para que puedas contribuir eficazmente al proyecto.

## Índice
1. [Cómo Empezar](#cómo-empezar)
2. [Flujo de Trabajo para Contribuciones](#flujo-de-trabajo-para-contribuciones)
3. [Estándares de Código](#estándares-de-código)
4. [Documentación](#documentación)
5. [Tests](#tests)
6. [Implementación de Nuevos Algoritmos](#implementación-de-nuevos-algoritmos)
7. [Contribuciones a la Documentación](#contribuciones-a-la-documentación)

## Cómo Empezar

### Requisitos Previos
- Python 3.8+
- Git
- Un editor de código (recomendamos VSCode o PyCharm)

### Configuración Inicial
1. **Fork** del repositorio en GitHub
2. **Clonar** tu fork localmente:
   ```bash
   git clone https://github.com/TU_USUARIO/BioAlgoCompare.git
   cd BioAlgoCompare
   ```
3. **Configurar el upstream**:
   ```bash
   git remote add upstream https://github.com/kaosb/BioAlgoCompare.git
   ```
4. **Instalar dependencias en modo desarrollo**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -e .
   ```

## Flujo de Trabajo para Contribuciones

Seguimos el modelo GitFlow para gestionar las contribuciones. Para más detalles, consulta la [documentación de GitFlow](git_workflow.md).

1. **Sincronizar con el repositorio upstream**:
   ```bash
   git checkout develop
   git pull upstream develop
   ```

2. **Crear una rama para tu contribución**:
   ```bash
   # Para nuevas funcionalidades
   git checkout -b feature/nombre-descriptivo

   # Para correcciones
   git checkout -b fix/nombre-descriptivo

   # Para documentación
   git checkout -b docs/nombre-descriptivo

   # Para refactorización
   git checkout -b refactor/nombre-descriptivo
   ```

3. **Realizar cambios, hacer commit y push**:
   ```bash
   git add .
   git commit -m "tipo: descripción concisa"
   git push origin tu-rama
   ```

4. **Crear un Pull Request** desde tu rama a `develop` en el repositorio principal.

## Estándares de Código

### Estilo de Código

Seguimos [PEP 8](https://www.python.org/dev/peps/pep-0008/) con algunas modificaciones:

- **Indentación**: 4 espacios (no tabuladores)
- **Longitud máxima de línea**: 100 caracteres
- **Nombres de variables**: snake_case para variables y funciones, CamelCase para clases
- **Documentación**: Docstrings estilo NumPy para todas las funciones y clases

### Herramientas de Formato

Utilizamos:
- **flake8** para verificación de estilo
- **black** para formateo automático
- **isort** para ordenar imports

Puedes ejecutar estas herramientas con:
```bash
# Formatear código
black .

# Ordenar imports
isort .

# Verificar estilo
flake8 .
```

## Documentación

Toda contribución debe incluir documentación adecuada:

1. **Docstrings** para todas las funciones, clases y métodos
2. **Comentarios** para secciones complejas de código
3. **Actualización de la documentación de usuario** si es necesario

### Formato de Docstrings

Utilizamos el formato NumPy para docstrings:

```python
def funcion_ejemplo(parametro1, parametro2):
    """
    Breve descripción de la función.

    Descripción más detallada si es necesario.

    Parameters
    ----------
    parametro1 : tipo
        Descripción del parámetro1
    parametro2 : tipo
        Descripción del parámetro2

    Returns
    -------
    tipo
        Descripción del valor de retorno

    Examples
    --------
    >>> funcion_ejemplo(1, 2)
    3
    """
```

## Tests

Es altamente recomendado añadir tests para cualquier nueva funcionalidad o corrección:

1. Ubicar los tests en el directorio `tests/`
2. Seguir la convención de nombres `test_*.py`
3. Utilizar pytest para ejecutar los tests:
   ```bash
   pytest tests/
   ```

## Implementación de Nuevos Algoritmos

Para añadir un nuevo algoritmo metaheurístico:

1. **Crear un nuevo archivo** en el directorio `algorithms/` con el nombre del algoritmo en minúsculas (ej: `nuevo_algoritmo.py`)
2. **Subclase de MetaheuristicAlgorithm**:
   ```python
   from algorithms.base import MetaheuristicAlgorithm, Solution

   class NuevoAlgoritmo(MetaheuristicAlgorithm):
       def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
           super().__init__(problem, population_size, max_iterations, seed)
           # Parámetros específicos del algoritmo

       def initialize(self):
           # Implementación de la inicialización

       def execute(self):
           # Implementación del algoritmo
           return best_solution
   ```
3. **Actualizar los archivos auxiliares**:
   - Añadir importación en `run.py`
   - Añadir a la lista de algoritmos disponibles
   - Crear documentación en `docs/algorithms/individual/nuevo_algoritmo.md`

4. **Añadir tests** para el nuevo algoritmo en `tests/test_nuevo_algoritmo.py`

5. **Documentar el algoritmo**:
   - Pseudocódigo en `docs/algorithms/pseudocode.md`
   - Descripción, inspiración biológica y referencias
   - Parámetros específicos y recomendaciones de uso

## Contribuciones a la Documentación

Para contribuir a la documentación:

1. **Editar archivos existentes** o crear nuevos en el directorio `docs/`
2. **Seguir la estructura** de carpetas actual:
   - `docs/guides/` para guías de usuario
   - `docs/algorithms/` para documentación de algoritmos
   - `docs/analysis/` para informes de análisis
   - `docs/development/` para guías de desarrollo
   - `docs/technical/` para documentación técnica

3. **Usar Markdown** con formato consistente:
   - Encabezados jerárquicos (# para título principal, ## para secciones, etc.)
   - Listas con guiones (-)
   - Bloques de código con ```python para código Python
   - Tablas donde sea apropiado

## Proceso de Revisión

Tu Pull Request será revisado considerando:

1. **Funcionalidad**: ¿Los cambios funcionan como se espera?
2. **Calidad del código**: ¿Cumple con los estándares de estilo?
3. **Tests**: ¿Incluye tests adecuados?
4. **Documentación**: ¿Está correctamente documentado?

Un revisor puede solicitar cambios antes de aprobar tu PR. Esto es parte normal del proceso de colaboración.

## Preguntas Frecuentes

### ¿Cómo puedo saber si mi contribución es relevante?

Revisa los issues abiertos o crea uno nuevo para discutir tu propuesta antes de comenzar el trabajo.

### ¿Hay alguna convención de nombrado específica?

Sí, consulta la sección de Estándares de Código y la documentación existente para mantener la coherencia.

### ¿Puedo contribuir con un algoritmo que no está publicado formalmente?

Preferimos algoritmos publicados en revistas o conferencias académicas. Si tienes un algoritmo nuevo, discútelo previamente en un issue.

---

¡Gracias por contribuir a BioAlgoCompare! Si tienes preguntas adicionales, no dudes en abrir un issue o contactar a los mantenedores.
