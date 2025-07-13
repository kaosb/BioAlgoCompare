#!/bin/bash
# Script para configurar protección de ramas tesis/academic

echo "🔒 Configurando protección de ramas para BioAlgoCompare"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar que estamos en el directorio correcto
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: No se encontró directorio .git${NC}"
    echo "Ejecuta este script desde la raíz del repositorio"
    exit 1
fi

# Función para verificar hook
check_hook() {
    local hook_name=$1
    local hook_path=".git/hooks/$hook_name"
    
    if [ -f "$hook_path" ] && [ -x "$hook_path" ]; then
        # Verificar si tiene nuestras protecciones
        if grep -q "tesis\|academic" "$hook_path"; then
            echo -e "${GREEN}✓${NC} Hook $hook_name configurado correctamente"
            return 0
        else
            echo -e "${YELLOW}⚠${NC}  Hook $hook_name existe pero no tiene protecciones de ramas"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Hook $hook_name no encontrado o no ejecutable"
        return 1
    fi
}

# Verificar hooks
echo "Verificando hooks de Git..."
echo ""

hooks_ok=true

check_hook "pre-commit" || hooks_ok=false
check_hook "post-checkout" || hooks_ok=false
check_hook "pre-merge-commit" || hooks_ok=false
check_hook "pre-push" || hooks_ok=false

echo ""

# Verificar ramas
echo "Verificando ramas..."
echo ""

# Verificar rama tesis
if git show-ref --quiet refs/heads/tesis; then
    echo -e "${GREEN}✓${NC} Rama 'tesis' existe"
else
    echo -e "${YELLOW}⚠${NC}  Rama 'tesis' no existe"
fi

# Verificar rama academic
if git show-ref --quiet refs/heads/academic; then
    echo -e "${GREEN}✓${NC} Rama 'academic' existe"
else
    echo -e "${YELLOW}⚠${NC}  Rama 'academic' no existe"
fi

echo ""

# Resumen de protecciones
echo "📋 Resumen de Protecciones:"
echo ""
echo "1. ${GREEN}pre-commit${NC}: Previene commits de archivos tesis/academic en ramas incorrectas"
echo "2. ${GREEN}post-checkout${NC}: Muestra advertencias al cambiar de rama"
echo "3. ${GREEN}pre-merge-commit${NC}: Previene merge de ramas tesis/academic a develop/main"
echo "4. ${GREEN}pre-push${NC}: Advierte antes de pushear ramas con información sensible"
echo ""

if [ "$hooks_ok" = true ]; then
    echo -e "${GREEN}✅ Todas las protecciones están activas${NC}"
else
    echo -e "${YELLOW}⚠️  Algunas protecciones no están configuradas${NC}"
    echo ""
    echo "Para instalar las protecciones faltantes:"
    echo "1. Revisa los hooks en .git/hooks/"
    echo "2. Asegúrate de que tengan permisos de ejecución (chmod +x)"
    echo "3. Verifica que contengan las validaciones para tesis/academic"
fi

echo ""
echo "🔍 Para probar las protecciones:"
echo "  - Intenta commitear un archivo /tesis/ en develop"
echo "  - Intenta hacer merge de academic a develop"
echo "  - Cambia entre ramas y observa los mensajes"
echo ""