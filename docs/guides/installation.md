# Guía de Instalación

Esta guía proporciona instrucciones detalladas para instalar BioAlgoCompare y todas sus dependencias.

## Requisitos del Sistema

Antes de comenzar, asegúrese de tener instalados los siguientes componentes:

- **Python 3.8+** (recomendado 3.10 o superior)
- **Git** (para clonar el repositorio)
- **pip** (gestor de paquetes de Python, incluido en instalaciones recientes de Python)
- **Entorno virtual** (opcional pero recomendado, como venv o conda)

## Dependencias Principales

BioAlgoCompare depende de las siguientes bibliotecas de Python:

- **NumPy**: Para cálculos numéricos y operaciones con matrices
- **Pandas**: Para gestión y análisis de datos
- **Matplotlib**: Para visualización y generación de gráficos
- **Click**: Para la interfaz de línea de comandos
- **SciPy**: Para análisis estadístico y funciones científicas
- **tqdm**: Para barras de progreso durante ejecuciones largas

## Instalación Estándar

Siga estos pasos para una instalación estándar:

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/kaosb/BioAlgoCompare.git
   cd BioAlgoCompare
   ```

2. **Crear un entorno virtual** (opcional pero recomendado):
   ```bash
   # Usando venv (integrado en Python 3.3+)
   python -m venv venv
   
   # Activar el entorno virtual
   # En Linux/macOS:
   source venv/bin/activate
   
   # En Windows:
   venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verificar la instalación**:
   ```bash
   # Ejecutar una prueba simple
   python scripts/run.py --algorithm ewa --instance P-n16-k8 --iterations 10 --no-visualize
   ```

## Instalación en Modo Desarrollo

Si planea contribuir al proyecto o realizar modificaciones en el código, es recomendable instalar en modo desarrollo:

```bash
pip install -e .
```

Esto instalará el paquete en modo editable, permitiendo que los cambios en el código fuente se reflejen inmediatamente sin necesidad de reinstalar.

## Instalación Global del Comando `bioalgo`

Para instalar el comando `bioalgo` globalmente y poder usarlo desde cualquier directorio:

```bash
pip install .
```

## Solución de Problemas Comunes

### Conflictos de Dependencias

Si encuentra conflictos de dependencias, intente:

```bash
pip install -r requirements.txt --force-reinstall
```

### Problemas con Matplotlib en macOS

Si tiene problemas con la visualización en macOS:

```bash
echo "backend: TkAgg" > ~/.matplotlib/matplotlibrc
```

### Errores de Importación

Si encuentra errores de importación, verifique que está ejecutando desde el directorio raíz del proyecto o que ha instalado el paquete correctamente.

## Estructura de Directorios Post-Instalación

Después de la instalación, la estructura de directorios debería verse así:

```
BioAlgoCompare/
├── algorithms/                # Implementaciones de algoritmos
├── data/                     # Datos e instancias de prueba
│   └── vrp/                  # Instancias VRP
├── docs/                     # Documentación
├── problems/                 # Implementaciones de problemas
├── results/                  # Directorio para resultados generados
├── scripts/                  # Scripts ejecutables
├── utils/                    # Utilidades y herramientas
├── .gitignore                # Archivos ignorados por git
├── LICENSE                   # Licencia del proyecto
├── README.md                 # Documentación general
├── requirements.txt          # Requisitos de instalación
├── run.py                    # Script principal de ejecución
└── setup.py                  # Configuración de instalación
```

## Siguientes Pasos

Una vez completada la instalación, consulte:

- [Referencia de Comandos](../COMMAND_REFERENCE.md) para instrucciones completas de uso
- [Guía de Benchmarking](benchmarking.md) para ejecutar experimentos rigurosos

## Referencias Adicionales

- [Documentación Oficial de Python](https://www.python.org/doc/)
- [Guía de Pip](https://pip.pypa.io/en/stable/user_guide/)
- [Guía de Entornos Virtuales](https://docs.python.org/3/tutorial/venv.html)