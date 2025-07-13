#!/bin/bash
# Script para migrar archivos académicos a rama 'academic'

set -e

echo "=== Migración de Archivos Académicos a Rama 'academic' ==="

# Verificar que estamos en develop
current_branch=$(git branch --show-current)
if [ "$current_branch" != "develop" ]; then
    echo "Error: Debes estar en la rama develop para ejecutar este script"
    exit 1
fi

# Verificar cambios sin commitear
if ! git diff-index --quiet HEAD --; then
    echo "Error: Hay cambios sin commitear. Por favor, commitea o stash antes de continuar."
    exit 1
fi

# Crear rama academic si no existe
if ! git show-ref --quiet refs/heads/academic; then
    echo "Creando rama 'academic'..."
    git checkout -b academic
else
    echo "La rama 'academic' ya existe. Cambiando a ella..."
    git checkout academic
    git merge develop --no-edit
fi

# Crear estructura de directorios
echo "Creando estructura de directorios..."
mkdir -p academic/{papers,scripts,config,docs,results}

# Lista de archivos a migrar
echo "Identificando archivos a migrar..."

# Papers
PAPERS=(
    "docs/papers/paper_ieee"
    "docs/papers/paper_extended"
    "docs/papers/paper_current"
)

# Scripts académicos
SCRIPTS=(
    "scripts/tools/generate_clei_submission.sh"
    "scripts/tools/generate_paper_report.py"
    "scripts/tools/validate_quick_ho.sh"
    "scripts/tools/generate_validation_report.py"
)

# Configuraciones
CONFIGS=(
    "experimental_config.json"
    "config/experimental_standards.json"
)

# Documentación académica
DOCS=(
    "docs/summaries/CLEI_2025_SUBMISSION_READY.md"
    "experimental_results/tesis_validation"
    "CLEI2025_QuickHO_Submission.zip"
    "analyze_preliminary_results.py"
)

# Resultados con referencias académicas
RESULTS=(
    "results/thesis_*"
    "results/THESIS_*"
)

# Copiar archivos
echo "Copiando archivos a directorio academic/..."

for paper in "${PAPERS[@]}"; do
    if [ -e "$paper" ]; then
        cp -r "$paper" "academic/papers/" || true
    fi
done

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        cp "$script" "academic/scripts/" || true
    fi
done

for config in "${CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        cp "$config" "academic/config/" || true
    fi
done

for doc in "${DOCS[@]}"; do
    if [ -e "$doc" ]; then
        cp -r "$doc" "academic/docs/" || true
    fi
done

# Copiar resultados (usando find para patterns)
find results -name "thesis_*" -o -name "THESIS_*" -exec cp -r {} academic/results/ \; 2>/dev/null || true

# Crear README para la rama academic
cat > academic/README.md << 'EOF'
# Archivos Académicos y de Publicación

Este directorio contiene todos los archivos relacionados con publicaciones académicas, conferencias y material personal de investigación.

## Estructura

- `/papers/` - Papers en LaTeX con información de autores
- `/scripts/` - Scripts para generación de sumisiones
- `/config/` - Configuraciones experimentales con referencias académicas
- `/docs/` - Documentación de conferencias y sumisiones
- `/results/` - Resultados experimentales con referencias a tesis

## Uso

Estos archivos están separados de la rama principal para mantener el código base limpio de referencias personales/académicas.

Para trabajar con estos archivos:
```bash
git checkout academic
# Hacer cambios
git add .
git commit -m "Actualizar archivos académicos"
```

## Integración con rama develop

Para usar estos archivos en develop temporalmente:
```bash
git checkout develop
git checkout academic -- academic/scripts/generate_paper_report.py
# Usar el archivo
git rm --cached academic/scripts/generate_paper_report.py
```
EOF

# Agregar archivos a git
echo "Agregando archivos a git..."
git add academic/

# Commit en rama academic
echo "Commiteando en rama academic..."
git commit -m "feat: migrar archivos académicos y personales a rama dedicada

- Papers con información de autores
- Scripts de generación CLEI
- Configuraciones con referencias a tesis
- Documentación de conferencias"

# Volver a develop
echo "Volviendo a rama develop..."
git checkout develop

# Crear .gitignore entries si no existen
echo "Actualizando .gitignore..."
cat >> .gitignore << 'EOF'

# Archivos académicos (mantenidos en rama academic)
academic/
CLEI*.zip
*thesis*
*THESIS*
*tesis*
*TESIS*
EOF

# Eliminar archivos de develop
echo "Eliminando archivos académicos de rama develop..."

# Eliminar papers con cuidado de no borrar otros archivos
git rm -r docs/papers/paper_ieee docs/papers/paper_extended docs/papers/paper_current || true

# Eliminar scripts académicos
for script in "${SCRIPTS[@]}"; do
    git rm "$script" || true
done

# Eliminar otros archivos
git rm experimental_config.json || true
git rm docs/summaries/CLEI_2025_SUBMISSION_READY.md || true
git rm -r experimental_results/tesis_validation || true
git rm CLEI2025_QuickHO_Submission.zip || true
git rm analyze_preliminary_results.py || true

# Eliminar archivos de results con pattern thesis
find results -name "thesis_*" -o -name "THESIS_*" | xargs git rm -r || true

echo "=== Migración Completada ==="
echo ""
echo "Los archivos académicos han sido movidos a la rama 'academic'"
echo "Para acceder a ellos: git checkout academic"
echo ""
echo "IMPORTANTE: Commitea los cambios en develop:"
echo "  git add ."
echo "  git commit -m 'refactor: mover archivos académicos a rama dedicada'"
echo ""