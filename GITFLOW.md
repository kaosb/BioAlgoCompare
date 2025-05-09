# Estructura GitFlow para BioAlgoCompare

## Estructura de Ramas

### Ramas Principales

- **`main`**: Código en producción, estable y listo para ser utilizado.
- **`develop`**: Rama principal de desarrollo, contiene los últimos cambios que están siendo preparados.

### Ramas de Soporte

- **`feature/*`**: Desarrollo de nuevas funcionalidades. Derivadas de `develop`.
- **`release/*`**: Preparación para una nueva versión. Derivadas de `develop`.
- **`hotfix/*`**: Correcciones urgentes en producción. Derivadas de `main`.
- **`refactor/*`**: Refactorizaciones de código sin nuevas funcionalidades. Derivadas de `develop`.

## Flujo de Trabajo

### Desarrollo de Nuevas Funcionalidades

```bash
# Crear rama feature
git checkout develop
git pull origin develop
git checkout -b feature/nombre-caracteristica

# Desarrollar, hacer commits, y al finalizar
git push origin feature/nombre-caracteristica

# Crear Pull Request en GitHub: feature/nombre-caracteristica → develop
```

### Preparación de Versiones

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

### Correcciones Urgentes

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

### Refactorización

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

- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de errores
- `docs:` - Cambios en documentación
- `style:` - Cambios de formato que no afectan el código
- `refactor:` - Restructuración de código sin cambiar comportamiento
- `perf:` - Mejoras de rendimiento
- `test:` - Adición o corrección de pruebas
- `chore:` - Tareas de mantenimiento, cambios en el build, etc.

## Proceso de Pull Request

1. Crear PR con descripción detallada
2. Solicitar revisión del equipo
3. Abordar comentarios y sugerencias
4. Obtener aprobación (al menos un revisor)
5. Fusionar (preferiblemente con squash para mantener el historial limpio)

## Etiquetado de Versiones

Después de cada fusión a `main` desde una rama `release/` o `hotfix/`, crear una etiqueta de versión:

```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Versión X.Y.Z"
git push origin vX.Y.Z
```