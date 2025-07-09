"""
Tests unitarios para validación de parámetros en todos los algoritmos v2.
"""

import pytest
import os
import tempfile
from algorithms.validators import ValidationError
from problems.vrp_v2 import VRPProblemV2

# Crear problema de prueba
@pytest.fixture
def test_problem():
    """Crea un problema VRP simple para pruebas"""
    # Crear archivo temporal VRP
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vrp', delete=False) as f:
        f.write("""NAME : test
COMMENT : Test instance
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 0
3 20 0
4 30 0
5 40 0
DEMAND_SECTION
1 0
2 10
3 20
4 15
5 25
DEPOT_SECTION
1
-1
EOF""")
        temp_file = f.name
    
    problem = VRPProblem(temp_file)
    os.unlink(temp_file)
    return problem


class TestMRFOValidation:
    """Tests para validación de parámetros en MRFO v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.mrfo_v2 import MRFOV2
        
        # Valores por defecto
        algo = MRFOV2(test_problem)
        assert algo.spiral_factor == 2.0
        assert algo.somersault_prob == 0.3
        
        # Valores personalizados válidos
        algo = MRFOV2(test_problem, spiral_factor=1.5, somersault_prob=0.5)
        assert algo.spiral_factor == 1.5
        assert algo.somersault_prob == 0.5
        
        # Valores en los límites
        algo = MRFOV2(test_problem, spiral_factor=1.0, somersault_prob=0.0)
        assert algo.spiral_factor == 1.0
        assert algo.somersault_prob == 0.0
        
        algo = MRFOV2(test_problem, spiral_factor=3.0, somersault_prob=1.0)
        assert algo.spiral_factor == 3.0
        assert algo.somersault_prob == 1.0
    
    def test_invalid_spiral_factor(self, test_problem):
        """Test con spiral_factor inválido."""
        from algorithms.mrfo_v2 import MRFOV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="spiral_factor debe ser >= 1.0"):
            MRFOV2(test_problem, spiral_factor=0.5)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="spiral_factor debe ser <= 3.0"):
            MRFOV2(test_problem, spiral_factor=4.0)
        
        # Valor negativo
        with pytest.raises(ValidationError, match="spiral_factor debe ser >= 1.0"):
            MRFOV2(test_problem, spiral_factor=-1.0)
    
    def test_invalid_somersault_prob(self, test_problem):
        """Test con somersault_prob inválido."""
        from algorithms.mrfo_v2 import MRFOV2
        
        # Valor negativo
        with pytest.raises(ValidationError, match="somersault_prob debe ser >= 0.0"):
            MRFOV2(test_problem, somersault_prob=-0.1)
        
        # Valor mayor a 1
        with pytest.raises(ValidationError, match="somersault_prob debe ser <= 1.0"):
            MRFOV2(test_problem, somersault_prob=1.5)


class TestAHAValidation:
    """Tests para validación de parámetros en AHA v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.aha_v2 import AHAV2
        
        # Valor por defecto
        algo = AHAV2(test_problem)
        assert algo.step_size == 0.1
        
        # Valores personalizados válidos
        algo = AHAV2(test_problem, step_size=0.3)
        assert algo.step_size == 0.3
        
        # Valores en los límites
        algo = AHAV2(test_problem, step_size=0.01)
        assert algo.step_size == 0.01
        
        algo = AHAV2(test_problem, step_size=0.5)
        assert algo.step_size == 0.5
    
    def test_invalid_step_size(self, test_problem):
        """Test con step_size inválido."""
        from algorithms.aha_v2 import AHAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="step_size debe ser >= 0.01"):
            AHAV2(test_problem, step_size=0.005)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="step_size debe ser <= 0.5"):
            AHAV2(test_problem, step_size=0.6)


class TestFGOValidation:
    """Tests para validación de parámetros en FGO v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.fgo_v2 import FGOV2
        
        # Valor por defecto
        algo = FGOV2(test_problem)
        assert algo.MPb_ratio == 0.1
        
        # Valores personalizados válidos
        algo = FGOV2(test_problem, MPb_ratio=0.15)
        assert algo.MPb_ratio == 0.15
    
    def test_invalid_MPb_ratio(self, test_problem):
        """Test con MPb_ratio inválido."""
        from algorithms.fgo_v2 import FGOV2
        
        # Valor negativo
        with pytest.raises(ValidationError, match="MPb_ratio debe ser >= 0.0"):
            FGOV2(test_problem, MPb_ratio=-0.1)
        
        # Valor mayor a 1
        with pytest.raises(ValidationError, match="MPb_ratio debe ser <= 1.0"):
            FGOV2(test_problem, MPb_ratio=1.5)
    
    def test_warning_for_suboptimal_values(self, test_problem, recwarn):
        """Test que se genera warning para valores subóptimos."""
        from algorithms.fgo_v2 import FGOV2
        
        # Valor muy bajo
        algo = FGOV2(test_problem, MPb_ratio=0.02)
        assert len(recwarn) == 1
        assert "fuera del rango recomendado" in str(recwarn[0].message)
        
        # Valor muy alto
        recwarn.clear()
        algo = FGOV2(test_problem, MPb_ratio=0.3)
        assert len(recwarn) == 1
        assert "fuera del rango recomendado" in str(recwarn[0].message)


class TestAPOValidation:
    """Tests para validación de parámetros en APO v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.apo_v2 import APOV2
        
        # Valores por defecto
        algo = APOV2(test_problem)
        assert algo.pf_max == 0.1
        assert algo.npairs == 1
        
        # Valores personalizados válidos
        algo = APOV2(test_problem, pf_max=0.2, npairs=2)
        assert algo.pf_max == 0.2
        assert algo.npairs == 2
    
    def test_invalid_pf_max(self, test_problem):
        """Test con pf_max inválido."""
        from algorithms.apo_v2 import APOV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="pf_max debe ser >= 0.05"):
            APOV2(test_problem, pf_max=0.03)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="pf_max debe ser <= 0.3"):
            APOV2(test_problem, pf_max=0.4)
    
    def test_invalid_npairs(self, test_problem):
        """Test con npairs inválido."""
        from algorithms.apo_v2 import APOV2
        
        # Valor cero
        with pytest.raises(ValidationError, match="npairs debe ser >= 1"):
            APOV2(test_problem, npairs=0)
        
        # Valor negativo
        with pytest.raises(ValidationError, match="npairs debe ser >= 1"):
            APOV2(test_problem, npairs=-1)
    
    def test_warning_for_high_npairs(self, test_problem, recwarn):
        """Test que se genera warning para npairs alto."""
        from algorithms.apo_v2 import APOV2
        
        algo = APOV2(test_problem, npairs=5)
        assert len(recwarn) == 1
        assert "npairs=5 es alto" in str(recwarn[0].message)


class TestSMOValidation:
    """Tests para validación de parámetros en SMO v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.smo_v2 import SMOV2
        
        # Valores por defecto (k se auto-calcula)
        algo = SMOV2(test_problem, population_size=30)
        assert algo.k == min(10, 30 // 3)  # 10
        assert algo.mu == 0.3
        
        # Valores personalizados válidos
        algo = SMOV2(test_problem, population_size=30, k=5, mu=0.4)
        assert algo.k == 5
        assert algo.mu == 0.4
    
    def test_invalid_k(self, test_problem):
        """Test con k inválido."""
        from algorithms.smo_v2 import SMOV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="k debe ser >= 3"):
            SMOV2(test_problem, k=2)
        
        # Valor muy alto respecto a population_size
        with pytest.raises(ValidationError, match="k debe ser <= population_size//2"):
            SMOV2(test_problem, population_size=20, k=11)
    
    def test_invalid_mu(self, test_problem):
        """Test con mu inválido."""
        from algorithms.smo_v2 import SMOV2
        
        # Valor negativo
        with pytest.raises(ValidationError, match="mu debe ser >= 0.0"):
            SMOV2(test_problem, mu=-0.1)
        
        # Valor mayor a 1
        with pytest.raises(ValidationError, match="mu debe ser <= 1.0"):
            SMOV2(test_problem, mu=1.5)


class TestGVOAValidation:
    """Tests para validación de parámetros en GVOA v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.gvoa_v2 import GVOAV2
        
        # Valores por defecto
        algo = GVOAV2(test_problem)
        assert algo.elite_ratio == 0.2
        assert algo.r == 0.2
        
        # Valores personalizados válidos
        algo = GVOAV2(test_problem, elite_ratio=0.25, r=0.3)
        assert algo.elite_ratio == 0.25
        assert algo.r == 0.3
    
    def test_invalid_elite_ratio(self, test_problem):
        """Test con elite_ratio inválido."""
        from algorithms.gvoa_v2 import GVOAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="elite_ratio debe ser >= 0.1"):
            GVOAV2(test_problem, elite_ratio=0.05)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="elite_ratio debe ser <= 0.33"):
            GVOAV2(test_problem, elite_ratio=0.4)
    
    def test_invalid_r(self, test_problem):
        """Test con r inválido."""
        from algorithms.gvoa_v2 import GVOAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="r debe ser >= 0.1"):
            GVOAV2(test_problem, r=0.05)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="r debe ser <= 0.5"):
            GVOAV2(test_problem, r=0.6)


class TestEWAValidation:
    """Tests para validación de parámetros en EWA v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.ewa_v2 import EWAV2
        
        # Valores por defecto
        algo = EWAV2(test_problem)
        assert algo.alpha == 0.8
        assert algo.beta == 0.2
        assert algo.gamma == 0.99
        
        # Valores personalizados válidos
        algo = EWAV2(test_problem, alpha=0.7, beta=0.3, gamma=0.95)
        assert algo.alpha == 0.7
        assert algo.beta == 0.3
        assert algo.gamma == 0.95
    
    def test_invalid_alpha(self, test_problem):
        """Test con alpha inválido."""
        from algorithms.ewa_v2 import EWAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="alpha debe ser >= 0.5"):
            EWAV2(test_problem, alpha=0.4)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="alpha debe ser <= 0.9"):
            EWAV2(test_problem, alpha=1.0)
    
    def test_invalid_beta(self, test_problem):
        """Test con beta inválido."""
        from algorithms.ewa_v2 import EWAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="beta debe ser >= 0.1"):
            EWAV2(test_problem, beta=0.05)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="beta debe ser <= 0.5"):
            EWAV2(test_problem, beta=0.6)
    
    def test_invalid_gamma(self, test_problem):
        """Test con gamma inválido."""
        from algorithms.ewa_v2 import EWAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="gamma debe ser >= 0.9"):
            EWAV2(test_problem, gamma=0.8)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="gamma debe ser <= 0.999"):
            EWAV2(test_problem, gamma=1.0)
    
    def test_warning_for_alpha_beta_sum(self, test_problem, recwarn):
        """Test que se genera warning si alpha + beta > 1.0."""
        from algorithms.ewa_v2 import EWAV2
        
        algo = EWAV2(test_problem, alpha=0.7, beta=0.4)
        assert len(recwarn) == 1
        assert "alpha + beta = 1.1 > 1.0" in str(recwarn[0].message)


class TestEGTOValidation:
    """Tests para validación de parámetros en EGTO v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.egto_v2 import EGTOV2
        
        # Valores por defecto
        algo = EGTOV2(test_problem)
        assert algo.P == 0.5
        assert algo.CF == 0.5
        assert algo.FADs == 0.2
        
        # Valores personalizados válidos
        algo = EGTOV2(test_problem, P=0.6, CF=0.4, FADs=0.1)
        assert algo.P == 0.6
        assert algo.CF == 0.4
        assert algo.FADs == 0.1
    
    def test_invalid_P(self, test_problem):
        """Test con P inválido."""
        from algorithms.egto_v2 import EGTOV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="P debe ser >= 0.3"):
            EGTOV2(test_problem, P=0.2)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="P debe ser <= 0.7"):
            EGTOV2(test_problem, P=0.8)
    
    def test_invalid_CF(self, test_problem):
        """Test con CF inválido."""
        from algorithms.egto_v2 import EGTOV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="CF debe ser >= 0.3"):
            EGTOV2(test_problem, CF=0.2)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="CF debe ser <= 0.7"):
            EGTOV2(test_problem, CF=0.8)
    
    def test_invalid_FADs(self, test_problem):
        """Test con FADs inválido."""
        from algorithms.egto_v2 import EGTOV2
        
        # Valor negativo
        with pytest.raises(ValidationError, match="FADs debe ser >= 0.0"):
            EGTOV2(test_problem, FADs=-0.1)
        
        # Valor mayor a 1
        with pytest.raises(ValidationError, match="FADs debe ser <= 1.0"):
            EGTOV2(test_problem, FADs=1.5)
    
    def test_warning_for_high_FADs(self, test_problem, recwarn):
        """Test que se genera warning para FADs alto."""
        from algorithms.egto_v2 import EGTOV2
        
        algo = EGTOV2(test_problem, FADs=0.5)
        assert len(recwarn) == 1
        assert "FADs=0.5 es alto" in str(recwarn[0].message)


class TestFSAValidation:
    """Tests para validación de parámetros en FSA v2."""
    
    def test_valid_parameters(self, test_problem):
        """Test con parámetros válidos."""
        from algorithms.fsa_v2 import FSAV2
        
        # Valor por defecto
        algo = FSAV2(test_problem)
        assert algo.MPb_ratio == 0.1
        
        # Valores personalizados válidos
        algo = FSAV2(test_problem, MPb_ratio=0.15)
        assert algo.MPb_ratio == 0.15
        
        # Valores en los límites
        algo = FSAV2(test_problem, MPb_ratio=0.05)
        assert algo.MPb_ratio == 0.05
        
        algo = FSAV2(test_problem, MPb_ratio=0.2)
        assert algo.MPb_ratio == 0.2
    
    def test_invalid_MPb_ratio(self, test_problem):
        """Test con MPb_ratio inválido."""
        from algorithms.fsa_v2 import FSAV2
        
        # Valor muy bajo
        with pytest.raises(ValidationError, match="MPb_ratio debe ser >= 0.05"):
            FSAV2(test_problem, MPb_ratio=0.03)
        
        # Valor muy alto
        with pytest.raises(ValidationError, match="MPb_ratio debe ser <= 0.2"):
            FSAV2(test_problem, MPb_ratio=0.3)


class TestBaseAlgorithmsValidation:
    """Tests para validación en algoritmos base."""
    
    def test_sma_z_parameter(self, test_problem):
        """Test parámetro z en SMA v2."""
        from algorithms.sma_v2 import SMAV2
        
        # Valor por defecto
        algo = SMAV2(test_problem)
        assert algo.z == 0.03
        
        # Valores válidos
        algo = SMAV2(test_problem, z=0.5)
        assert algo.z == 0.5
        
        # Valor inválido
        with pytest.raises(ValidationError, match="z debe ser <= 1.0"):
            SMAV2(test_problem, z=1.5)
    
    def test_gto_parameters(self, test_problem):
        """Test parámetros p y beta en GTO v2."""
        from algorithms.gto_v2 import GTOV2
        
        # Valores por defecto
        algo = GTOV2(test_problem)
        assert algo.p == 0.03
        assert algo.beta == 3.0
        
        # Valores válidos
        algo = GTOV2(test_problem, p=0.5, beta=2.0)
        assert algo.p == 0.5
        assert algo.beta == 2.0
        
        # Valores inválidos
        with pytest.raises(ValidationError, match="p debe ser <= 1.0"):
            GTOV2(test_problem, p=1.5)
        
        with pytest.raises(ValidationError, match="beta debe ser > 0.0"):
            GTOV2(test_problem, beta=-1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])