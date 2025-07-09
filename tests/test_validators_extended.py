"""
Tests extendidos para validaciones específicas de algoritmos agregadas recientemente.
"""

import pytest
from algorithms.validators import (
    ValidationError,
    ParameterValidator,
    validate_algorithm_specific_params
)


class TestExtendedAlgorithmSpecificParams:
    """Tests para parámetros específicos de algoritmos con validación extendida."""
    
    def test_mrfo_params(self):
        """Test parámetros específicos de MRFO."""
        # Valores válidos
        params = {"spiral_factor": 2.0, "somersault_prob": 0.3}
        validated = validate_algorithm_specific_params("mrfo", params)
        assert validated["spiral_factor"] == 2.0
        assert validated["somersault_prob"] == 0.3
        
        # spiral_factor fuera de rango
        params = {"spiral_factor": 0.5}
        with pytest.raises(ValidationError, match="spiral_factor debe ser >= 1.0"):
            validate_algorithm_specific_params("mrfo", params)
        
        params = {"spiral_factor": 4.0}
        with pytest.raises(ValidationError, match="spiral_factor debe ser <= 3.0"):
            validate_algorithm_specific_params("mrfo", params)
        
        # somersault_prob inválida
        params = {"somersault_prob": 1.5}
        with pytest.raises(ValidationError, match="somersault_prob debe ser <= 1.0"):
            validate_algorithm_specific_params("mrfo", params)
    
    def test_aha_params(self):
        """Test parámetros específicos de AHA."""
        # Valores válidos
        params = {"step_size": 0.2}
        validated = validate_algorithm_specific_params("aha", params)
        assert validated["step_size"] == 0.2
        
        # step_size fuera de rango
        params = {"step_size": 0.005}
        with pytest.raises(ValidationError, match="step_size debe ser >= 0.01"):
            validate_algorithm_specific_params("aha", params)
        
        params = {"step_size": 0.6}
        with pytest.raises(ValidationError, match="step_size debe ser <= 0.5"):
            validate_algorithm_specific_params("aha", params)
    
    def test_fgo_params(self):
        """Test parámetros específicos de FGO."""
        # Valores válidos
        params = {"MPb_ratio": 0.15}
        validated = validate_algorithm_specific_params("fgo", params)
        assert validated["MPb_ratio"] == 0.15
        
        # MPb_ratio inválida
        params = {"MPb_ratio": -0.1}
        with pytest.raises(ValidationError, match="MPb_ratio debe ser >= 0.0"):
            validate_algorithm_specific_params("fgo", params)
        
        params = {"MPb_ratio": 1.5}
        with pytest.raises(ValidationError, match="MPb_ratio debe ser <= 1.0"):
            validate_algorithm_specific_params("fgo", params)
    
    def test_apo_params(self):
        """Test parámetros específicos de APO."""
        # Valores válidos
        params = {"pf_max": 0.2, "npairs": 2}
        validated = validate_algorithm_specific_params("apo", params)
        assert validated["pf_max"] == 0.2
        assert validated["npairs"] == 2
        
        # pf_max fuera de rango
        params = {"pf_max": 0.03}
        with pytest.raises(ValidationError, match="pf_max debe ser >= 0.05"):
            validate_algorithm_specific_params("apo", params)
        
        params = {"pf_max": 0.4}
        with pytest.raises(ValidationError, match="pf_max debe ser <= 0.3"):
            validate_algorithm_specific_params("apo", params)
        
        # npairs inválido
        params = {"npairs": 0}
        with pytest.raises(ValidationError, match="npairs debe ser >= 1"):
            validate_algorithm_specific_params("apo", params)
    
    def test_gvoa_params(self):
        """Test parámetros específicos de GVOA."""
        # Valores válidos
        params = {"elite_ratio": 0.25, "r": 0.3}
        validated = validate_algorithm_specific_params("gvoa", params)
        assert validated["elite_ratio"] == 0.25
        assert validated["r"] == 0.3
        
        # elite_ratio fuera de rango
        params = {"elite_ratio": 0.05}
        with pytest.raises(ValidationError, match="elite_ratio debe ser >= 0.1"):
            validate_algorithm_specific_params("gvoa", params)
        
        params = {"elite_ratio": 0.4}
        with pytest.raises(ValidationError, match="elite_ratio debe ser <= 0.33"):
            validate_algorithm_specific_params("gvoa", params)
        
        # r fuera de rango
        params = {"r": 0.05}
        with pytest.raises(ValidationError, match="r debe ser >= 0.1"):
            validate_algorithm_specific_params("gvoa", params)
        
        params = {"r": 0.6}
        with pytest.raises(ValidationError, match="r debe ser <= 0.5"):
            validate_algorithm_specific_params("gvoa", params)
    
    def test_ewa_params(self):
        """Test parámetros específicos de EWA."""
        # Valores válidos
        params = {"alpha": 0.7, "beta": 0.3, "gamma": 0.95}
        validated = validate_algorithm_specific_params("ewa", params)
        assert validated["alpha"] == 0.7
        assert validated["beta"] == 0.3
        assert validated["gamma"] == 0.95
        
        # alpha fuera de rango
        params = {"alpha": 0.4}
        with pytest.raises(ValidationError, match="alpha debe ser >= 0.5"):
            validate_algorithm_specific_params("ewa", params)
        
        params = {"alpha": 1.0}
        with pytest.raises(ValidationError, match="alpha debe ser <= 0.9"):
            validate_algorithm_specific_params("ewa", params)
        
        # beta fuera de rango
        params = {"beta": 0.05}
        with pytest.raises(ValidationError, match="beta debe ser >= 0.1"):
            validate_algorithm_specific_params("ewa", params)
        
        params = {"beta": 0.6}
        with pytest.raises(ValidationError, match="beta debe ser <= 0.5"):
            validate_algorithm_specific_params("ewa", params)
        
        # gamma fuera de rango
        params = {"gamma": 0.8}
        with pytest.raises(ValidationError, match="gamma debe ser >= 0.9"):
            validate_algorithm_specific_params("ewa", params)
        
        params = {"gamma": 1.0}
        with pytest.raises(ValidationError, match="gamma debe ser <= 0.999"):
            validate_algorithm_specific_params("ewa", params)
    
    def test_egto_params(self):
        """Test parámetros específicos de EGTO."""
        # Valores válidos
        params = {"P": 0.5, "CF": 0.5, "FADs": 0.2}
        validated = validate_algorithm_specific_params("egto", params)
        assert validated["P"] == 0.5
        assert validated["CF"] == 0.5
        assert validated["FADs"] == 0.2
        
        # P fuera de rango
        params = {"P": 0.2}
        with pytest.raises(ValidationError, match="P debe ser >= 0.3"):
            validate_algorithm_specific_params("egto", params)
        
        params = {"P": 0.8}
        with pytest.raises(ValidationError, match="P debe ser <= 0.7"):
            validate_algorithm_specific_params("egto", params)
        
        # CF fuera de rango
        params = {"CF": 0.2}
        with pytest.raises(ValidationError, match="CF debe ser >= 0.3"):
            validate_algorithm_specific_params("egto", params)
        
        params = {"CF": 0.8}
        with pytest.raises(ValidationError, match="CF debe ser <= 0.7"):
            validate_algorithm_specific_params("egto", params)
        
        # FADs inválido
        params = {"FADs": -0.1}
        with pytest.raises(ValidationError, match="FADs debe ser >= 0.0"):
            validate_algorithm_specific_params("egto", params)
        
        params = {"FADs": 1.5}
        with pytest.raises(ValidationError, match="FADs debe ser <= 1.0"):
            validate_algorithm_specific_params("egto", params)
    
    def test_fsa_params(self):
        """Test parámetros específicos de FSA."""
        # Valores válidos
        params = {"MPb_ratio": 0.15}
        validated = validate_algorithm_specific_params("fsa", params)
        assert validated["MPb_ratio"] == 0.15
        
        # MPb_ratio fuera de rango
        params = {"MPb_ratio": 0.03}
        with pytest.raises(ValidationError, match="MPb_ratio debe ser >= 0.05"):
            validate_algorithm_specific_params("fsa", params)
        
        params = {"MPb_ratio": 0.3}
        with pytest.raises(ValidationError, match="MPb_ratio debe ser <= 0.2"):
            validate_algorithm_specific_params("fsa", params)
    
    def test_smo_params_updated(self):
        """Test parámetros actualizados de SMO."""
        # Valores válidos
        params = {"k": 5, "mu": 0.4}
        validated = validate_algorithm_specific_params("smo", params)
        assert validated["k"] == 5
        assert validated["mu"] == 0.4
        
        # k debe ser >= 3
        params = {"k": 2}
        with pytest.raises(ValidationError, match="k debe ser >= 3"):
            validate_algorithm_specific_params("smo", params)
        
        # mu debe ser probabilidad
        params = {"mu": 1.5}
        with pytest.raises(ValidationError, match="mu debe ser <= 1.0"):
            validate_algorithm_specific_params("smo", params)
    
    def test_partial_params(self):
        """Test validación de parámetros parciales."""
        # Solo algunos parámetros
        params = {"alpha": 0.7}
        validated = validate_algorithm_specific_params("ewa", params)
        assert validated["alpha"] == 0.7
        assert "beta" not in validated
        assert "gamma" not in validated
        
        # Sin parámetros
        params = {}
        validated = validate_algorithm_specific_params("mrfo", params)
        assert validated == {}
    
    def test_unknown_params_ignored(self):
        """Test que parámetros desconocidos son ignorados."""
        params = {"spiral_factor": 2.0, "unknown_param": 123}
        validated = validate_algorithm_specific_params("mrfo", params)
        assert validated["spiral_factor"] == 2.0
        assert "unknown_param" not in validated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])