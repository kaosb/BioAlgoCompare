# Release Notes - BioAlgoCompare v2.0

## 🎉 Resumen Ejecutivo

BioAlgoCompare v2.0 representa una evolución mayor del framework, con una arquitectura completamente rediseñada que mejora significativamente la extensibilidad, rendimiento y usabilidad del sistema.

## 🚀 Características Principales

### 1. Nueva Arquitectura v2
- **Sistema MoveContext**: Paso consistente de parámetros entre componentes
- **Validación de Parámetros**: Sistema robusto con mensajes descriptivos
- **Factory Patterns**: Creación estandarizada de objetos
- **Mejor Gestión de Memoria**: Caching de fitness y gestión optimizada

### 2. CLI Unificado
```bash
# Antes (v1)
python run.py --algorithm woa --instance P-n16-k8.vrp

# Ahora (v2)
bioalgocompare run woa P-n16-k8.vrp
```



## 📊 Mejoras de Rendimiento

- **Caching de Fitness**: Evita recálculos innecesarios
- **Paralelización Mejorada**: Mejor distribución de carga
- **Gestión de Memoria**: Reducción de memory leaks en ejecuciones largas
- **Checkpoints**: Para ejecuciones massive (1000 runs)

## 🛠️ Para Desarrolladores

### Validación de Parámetros
```python
from algorithms.validators import ParameterValidator

# En el constructor del algoritmo
self.learning_rate = ParameterValidator.validate_positive_float(
    learning_rate, "learning_rate", min_value=0.0, max_value=1.0
)
```

### Nuevo Sistema de Contexto
```python
def move(self, context: MoveContext):
    # Acceso consistente a parámetros
    alpha = context.get_param("alpha", 0.5)
    best = context.best_individual
    iteration = context.iteration
```

## 📚 Documentación Completa

- `INSTALLATION.md` - Guía de instalación paso a paso
- `QUICKSTART.md` - Tutorial de inicio rápido
- `API.md` - Documentación completa de la API
- `CLI.md` - Referencia de comandos CLI
- `VALIDATION_GUIDE.md` - Guía de validación de parámetros
- `MIGRATION_GUIDE.md` - Migración de v1 a v2

## 🔧 Instalación

```bash
# Clonar repositorio
git clone https://github.com/yourusername/bioalgocompare.git
cd bioalgocompare

# Instalar
pip install -e .

# Verificar
bioalgocompare --version
```

## 💡 Ejemplos de Uso

### Ejecución Simple
```bash
bioalgocompare run woa P-n16-k8.vrp
```

### Benchmark Completo
```bash
bioalgocompare benchmark \
  -a woa,sma,gto,mrfo \
  -i P-n16-k8,P-n19-k2 \
  -r 50
```

### Análisis de Resultados
```bash
bioalgocompare analyze results/benchmark_*.json \
  --format detailed \
  --compare
```

## 🐛 Problemas Corregidos

- Convergencia prematura en varios algoritmos
- Gestión incorrecta de límites del espacio de búsqueda
- Problemas de reproducibilidad con semillas
- Memory leaks en ejecuciones largas
- Conflictos de nombres de archivos
- Importaciones circulares

## ⚡ Cambios Breaking

1. **Imports**: Cambiar de `base` a `base_v2`
2. **CLI**: Usar `bioalgocompare` en lugar de scripts individuales
3. **Parámetros**: Algunos algoritmos requieren validación explícita

## 🔮 Planes Futuros

- [ ] Dashboard web interactivo
- [ ] Sistema de plugins
- [ ] Más tipos de problemas (TSP, Job Shop)
- [ ] API REST
- [ ] Integración con cloud

## 🙏 Agradecimientos

Gracias a todos los investigadores cuyos papers inspiraron estos algoritmos bio-inspirados.

## 📞 Soporte

- Issues: https://github.com/yourusername/bioalgocompare/issues
- Documentación: https://bioalgocompare.readthedocs.io

---

**BioAlgoCompare v2.0** - Optimización bio-inspirada para el siglo XXI 🚀