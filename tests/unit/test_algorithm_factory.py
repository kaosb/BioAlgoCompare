"""
Tests para el módulo algorithm_factory.
Cubre todas las funciones del factory de algoritmos.
"""
import pytest
from unittest.mock import Mock
from utils.algorithm_factory import (
    ALGORITHMS,
    create_algorithm,
    get_algorithm_info,
    list_algorithms,
    get_algorithm_by_year,
    get_algorithm_class,
)
from algorithms.base import MetaheuristicAlgorithm


class TestAlgorithmFactory:
    """Tests para las funciones del algorithm factory."""

    @pytest.fixture
    def mock_problem(self):
        """Mock de un problema para los tests."""
        problem = Mock()
        problem.dimension = 10
        problem.lower_bound = 0
        problem.upper_bound = 1
        problem.get_dimension.return_value = 10
        problem.evaluate.return_value = 1.0
        return problem

    def test_algorithms_registry_structure(self):
        """Test que verifica la estructura del registro ALGORITHMS."""
        assert isinstance(ALGORITHMS, dict)
        assert len(ALGORITHMS) > 0
        
        # Verificar estructura de cada entrada
        for name, (algo_class, full_name, year) in ALGORITHMS.items():
            assert isinstance(name, str)
            assert issubclass(algo_class, MetaheuristicAlgorithm)
            assert isinstance(full_name, str)
            assert isinstance(year, int)
            assert 1970 <= year <= 2030  # Rango razonable de años (incluye GA de 1975)

    def test_create_algorithm_valid(self, mock_problem):
        """Test crear algoritmo con nombre válido."""
        # Test con algoritmo principal
        algo = create_algorithm("ho", mock_problem, population_size=20, iterations=50, seed=42)
        assert algo is not None
        assert algo.population_size == 20
        assert hasattr(algo, 'max_iterations')
        assert algo.seed == 42

    def test_create_algorithm_with_kwargs(self, mock_problem):
        """Test crear algoritmo con parámetros adicionales."""
        # Algunos algoritmos pueden tener parámetros específicos
        algo = create_algorithm(
            "sho", 
            mock_problem, 
            population_size=30, 
            iterations=100,
            custom_param=0.5  # Parámetro adicional
        )
        assert algo is not None
        assert algo.population_size == 30

    def test_create_algorithm_case_insensitive(self, mock_problem):
        """Test que el nombre del algoritmo no es sensible a mayúsculas."""
        algo1 = create_algorithm("HO", mock_problem)
        algo2 = create_algorithm("ho", mock_problem)
        algo3 = create_algorithm("Ho", mock_problem)
        
        assert type(algo1) == type(algo2) == type(algo3)

    def test_create_algorithm_invalid_name(self, mock_problem):
        """Test crear algoritmo con nombre inválido."""
        with pytest.raises(ValueError) as excinfo:
            create_algorithm("invalid_algo", mock_problem)
        
        assert "Unknown algorithm: 'invalid_algo'" in str(excinfo.value)
        assert "Available algorithms:" in str(excinfo.value)

    def test_create_algorithm_alias(self, mock_problem):
        """Test crear algoritmo usando alias."""
        # HOA es alias de SHO
        algo_hoa = create_algorithm("hoa", mock_problem)
        algo_sho = create_algorithm("sho", mock_problem)
        assert type(algo_hoa) == type(algo_sho)

    def test_fgo_is_separate_from_fsa(self, mock_problem):
        """Test que FGO y FSA son algoritmos distintos."""
        algo_fgo = create_algorithm("fgo", mock_problem)
        algo_fsa = create_algorithm("fsa", mock_problem)
        assert type(algo_fgo) != type(algo_fsa)

    def test_get_algorithm_info_valid(self):
        """Test obtener información de algoritmo válido."""
        info = get_algorithm_info("ho")
        
        assert info["name"] == "ho"
        assert info["full_name"] == "Hippopotamus Optimization"
        assert info["year"] == 2024
        assert info["class"].__name__ == "HO"
        assert info["module"] == "algorithms.ho"
        assert info["is_alias"] is False

    def test_get_algorithm_info_alias(self):
        """Test obtener información de alias."""
        info = get_algorithm_info("hoa")
        assert info["is_alias"] is True
        assert "HOA alias" in info["full_name"]

    def test_get_algorithm_info_fgo(self):
        """Test obtener información de FGO (algoritmo primario)."""
        info = get_algorithm_info("fgo")
        assert info["is_alias"] is False
        assert info["full_name"] == "Flamingo Optimization Algorithm"
        assert info["year"] == 2021

    def test_get_algorithm_info_invalid(self):
        """Test obtener información de algoritmo inválido."""
        with pytest.raises(ValueError) as excinfo:
            get_algorithm_info("invalid_algo")
        
        assert "Unknown algorithm: 'invalid_algo'" in str(excinfo.value)

    def test_list_algorithms_without_aliases(self):
        """Test listar algoritmos sin incluir aliases."""
        algos = list_algorithms(include_aliases=False)

        assert isinstance(algos, dict)
        assert "hoa" not in algos
        assert "fgo" in algos  # FGO is a primary algorithm, not an alias
        assert "ho" in algos
        assert "sho" in algos

        # Verificar estructura de cada entrada
        for name, info in algos.items():
            assert "full_name" in info
            assert "year" in info
            assert "class_name" in info
            assert "is_alias" in info

    def test_list_algorithms_with_aliases(self):
        """Test listar algoritmos incluyendo aliases."""
        algos = list_algorithms(include_aliases=True)

        assert "hoa" in algos
        assert "fgo" in algos
        assert algos["hoa"]["is_alias"] is True
        assert algos["fgo"]["is_alias"] is False  # FGO is primary, not alias

    def test_list_algorithms_count(self):
        """Test contar algoritmos únicos."""
        algos_no_alias = list_algorithms(include_aliases=False)
        algos_with_alias = list_algorithms(include_aliases=True)

        # 22 algoritmos primarios (19 bioinspirados + FGO + 2 clásicos)
        assert len(algos_no_alias) == 22
        # Con aliases debe haber 23 (22 + 1 alias HOA)
        assert len(algos_with_alias) == 23

    def test_get_algorithm_by_year_single(self):
        """Test obtener algoritmos de un año específico."""
        algos_2024 = get_algorithm_by_year(2024)
        
        assert "ho" in algos_2024
        assert "apo" in algos_2024
        assert "egto" in algos_2024
        assert "foa" in algos_2024
        
        # Verificar que no incluye aliases
        assert "hoa" not in algos_2024

    def test_get_algorithm_by_year_range(self):
        """Test obtener algoritmos en rango de años."""
        algos_2020_2021 = get_algorithm_by_year(2020, 2021)
        
        assert "mrfo" in algos_2020_2021  # 2020
        assert "sma" in algos_2020_2021   # 2020
        assert "gto" in algos_2020_2021   # 2021
        assert "fsa" in algos_2020_2021   # 2021
        assert "opa" in algos_2020_2021   # 2021
        
        # No debe incluir años fuera del rango
        assert "ho" not in algos_2020_2021    # 2024
        assert "woa" not in algos_2020_2021   # 2016

    def test_get_algorithm_by_year_empty(self):
        """Test obtener algoritmos de año sin algoritmos."""
        algos_2000 = get_algorithm_by_year(2000)
        assert len(algos_2000) == 0

    def test_get_algorithm_class_valid(self):
        """Test obtener clase de algoritmo válido."""
        ho_class = get_algorithm_class("ho")
        assert ho_class.__name__ == "HO"
        assert issubclass(ho_class, MetaheuristicAlgorithm)
        
        # Test con mayúsculas
        ho_class2 = get_algorithm_class("HO")
        assert ho_class == ho_class2

    def test_get_algorithm_class_alias(self):
        """Test obtener clase de algoritmo por alias."""
        hoa_class = get_algorithm_class("hoa")
        sho_class = get_algorithm_class("sho")
        assert hoa_class == sho_class

    def test_get_algorithm_class_invalid(self):
        """Test obtener clase de algoritmo inválido."""
        with pytest.raises(ValueError) as excinfo:
            get_algorithm_class("invalid_algo")
        
        assert "Unknown algorithm: 'invalid_algo'" in str(excinfo.value)

    def test_all_algorithms_can_be_created(self, mock_problem):
        """Test que todos los algoritmos registrados pueden ser creados."""
        for name in ALGORITHMS.keys():
            try:
                algo = create_algorithm(name, mock_problem, population_size=10, iterations=5)
                assert algo is not None
                assert isinstance(algo, MetaheuristicAlgorithm)
            except Exception as e:
                pytest.fail(f"Failed to create algorithm '{name}': {e}")

    def test_algorithm_years_consistency(self):
        """Test que los años de los algoritmos son consistentes."""
        # Verificar que los aliases tienen el mismo año que el original
        sho_info = get_algorithm_info("sho")
        hoa_info = get_algorithm_info("hoa")
        assert sho_info["year"] == hoa_info["year"]
        
        fsa_info = get_algorithm_info("fsa")
        fgo_info = get_algorithm_info("fgo")
        assert fsa_info["year"] == fgo_info["year"]

    def test_algorithm_registry_completeness(self):
        """Test que todos los algoritmos importados están en el registro."""
        import algorithms
        import os
        
        # Obtener todos los archivos .py en el directorio algorithms
        algo_dir = os.path.dirname(algorithms.__file__)
        algo_files = [f[:-3] for f in os.listdir(algo_dir) 
                      if f.endswith('.py') and not f.startswith('_') and f != 'base.py']
        
        # Verificar que cada archivo tiene una entrada en ALGORITHMS
        # (excepto los que son solo aliases)
        registered_classes = {algo_class.__name__.lower() for _, (algo_class, _, _) in ALGORITHMS.items()}
        
        for algo_file in algo_files:
            if algo_file not in ['hoa', 'fgo']:  # Excepto aliases que no tienen archivo propio
                assert algo_file in registered_classes or algo_file in ALGORITHMS, \
                    f"Algorithm file '{algo_file}.py' not registered in ALGORITHMS"