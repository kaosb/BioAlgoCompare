"""
Test de validación de parámetros para SMA v2.
"""

import pytest
from algorithms.sma_v2 import SMAV2
from algorithms.validators import ValidationError
from problems.vrp import VRPProblem


class TestSMAV2Validation:
    """Tests de validación de parámetros para SMA v2."""
    
    @pytest.fixture
    def vrp_problem(self, tmp_path):
        """Fixture que proporciona un problema VRP de prueba."""
        # Crear un archivo VRP temporal mínimo
        vrp_file = tmp_path / "test.vrp"
        vrp_content = """NAME : test
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 10
3 20 20
4 30 30
5 40 40
DEMAND_SECTION
1 0
2 10
3 20
4 30
5 40
DEPOT_SECTION
1
-1
EOF"""
        vrp_file.write_text(vrp_content)
        return VRPProblem(str(vrp_file))
    
    def test_valid_parameters(self, vrp_problem):
        """Test con parámetros válidos."""
        # Parámetros válidos
        algo = SMAV2(
            problem=vrp_problem,
            population_size=20,
            max_iterations=50,
            seed=42,
            z=0.5
        )
        
        assert algo.population_size == 20
        assert algo.max_iterations == 50
        assert algo.seed == 42
        assert algo.z == 0.5
    
    def test_invalid_z_parameter(self, vrp_problem):
        """Test con parámetro z inválido."""
        # z debe estar entre 0 y 1
        with pytest.raises(ValidationError, match="z debe ser <= 1.0"):
            SMAV2(
                problem=vrp_problem,
                z=1.5  # Valor inválido
            )
        
        # z debe ser positivo
        with pytest.raises(ValidationError, match="z debe ser >= 0.0"):
            SMAV2(
                problem=vrp_problem,
                z=-0.1  # Valor negativo
            )
    
    def test_invalid_population_size(self, vrp_problem):
        """Test con tamaño de población inválido."""
        with pytest.raises(ValidationError, match="population_size debe ser >= 2"):
            SMAV2(
                problem=vrp_problem,
                population_size=1  # Muy pequeño
            )
        
        with pytest.raises(ValidationError, match="population_size debe ser un número entero"):
            SMAV2(
                problem=vrp_problem,
                population_size="veinte"  # No es un número
            )
    
    def test_invalid_iterations(self, vrp_problem):
        """Test con número de iteraciones inválido."""
        with pytest.raises(ValidationError, match="max_iterations debe ser >= 1"):
            SMAV2(
                problem=vrp_problem,
                max_iterations=0  # Cero iteraciones
            )
    
    def test_string_to_number_conversion(self, vrp_problem):
        """Test que los strings numéricos se convierten correctamente."""
        algo = SMAV2(
            problem=vrp_problem,
            population_size="30",  # String que se puede convertir
            max_iterations="100",
            z="0.03"
        )
        
        assert algo.population_size == 30
        assert algo.max_iterations == 100
        assert algo.z == 0.03
    
    def test_warnings_for_small_values(self, vrp_problem, recwarn):
        """Test que se generan warnings para valores pequeños."""
        # Población pequeña genera warning
        algo = SMAV2(
            problem=vrp_problem,
            population_size=5,  # Muy pequeño, debería generar warning
            max_iterations=20
        )
        
        assert len(recwarn) == 1
        assert "population_size=5 es muy pequeño" in str(recwarn[0].message)
    
    def test_default_values(self, vrp_problem):
        """Test que los valores por defecto son correctos."""
        algo = SMAV2(problem=vrp_problem)
        
        assert algo.population_size == 30
        assert algo.max_iterations == 100
        assert algo.z == 0.03
        assert algo.seed is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])