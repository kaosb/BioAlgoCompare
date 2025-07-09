import pytest
import numpy as np
from problems.vrp_v2 import VRPProblemV2, PENALTY_CAP, PENALTY_MISSING
import os

# Ruta al directorio de datos de prueba
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")


@pytest.fixture
def vrp_problem():
    """Fixture que proporciona una instancia de problema VRP."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    return VRPProblem(instance_path)


def test_missing_clients_penalty(vrp_problem):
    """Test que la penalización por clientes faltantes se calcula correctamente."""
    # Crear rutas con clientes faltantes
    missing_routes = [
        [0, 1, 2, 0],  # Solo tiene clientes 1 y 2
        [0, 3, 4, 0],  # Solo tiene clientes 3 y 4
    ]  # Faltan clientes 5-15

    # Evaluar rutas con detalle
    _, penalties, error_messages = vrp_problem.evaluate_routes_detailed(missing_routes)

    # Calcular manualmente el número de clientes faltantes
    missing_clients = set(range(1, vrp_problem.dimension)) - {1, 2, 3, 4}
    expected_penalty = len(missing_clients) * PENALTY_MISSING

    # Verificar que la penalización por clientes faltantes es correcta
    assert penalties["missing"] == expected_penalty

    # Verificar que se generó un mensaje de error
    assert any("Nodos faltantes" in msg for msg in error_messages)

    # Verificar que el mensaje contiene los clientes faltantes
    msg = next(msg for msg in error_messages if "Nodos faltantes" in msg)
    for client in missing_clients:
        assert str(client) in msg


def test_overload_penalty(vrp_problem):
    """Test que la penalización por exceso de capacidad se calcula correctamente."""
    # Determinar el cliente con mayor demanda
    high_demand_clients = sorted(
        range(1, vrp_problem.dimension),
        key=lambda x: vrp_problem.demands[x],
        reverse=True,
    )

    # Crear una ruta que exceda la capacidad
    route = [0]
    total_demand = 0

    # Seguir agregando clientes hasta exceder la capacidad
    for client in high_demand_clients:
        route.append(client)
        total_demand += vrp_problem.demands[client]
        # Cuando tengamos suficiente demanda para exceder claramente la capacidad
        if total_demand > vrp_problem.capacity * 1.5:
            break

    route.append(0)  # Cerrar la ruta

    # Evaluar la ruta
    _, penalties, error_messages = vrp_problem.evaluate_routes_detailed([route])

    # Calcular el exceso y la penalización esperada
    excess = total_demand - vrp_problem.capacity
    expected_penalty = excess * PENALTY_CAP

    # Verificar que la penalización por exceso de capacidad es correcta
    assert penalties["capacity"] == expected_penalty

    # Verificar que se generó un mensaje de error
    assert any("excede capacidad" in msg for msg in error_messages)


def test_duplicate_detection(vrp_problem):
    """Test que la detección de nodos duplicados funciona correctamente."""
    # Crear rutas con nodos duplicados
    duplicate_routes = [
        [0, 1, 2, 3, 0],
        [0, 4, 5, 2, 0],  # Cliente 2 duplicado
        [0, 6, 3, 7, 0],  # Cliente 3 duplicado
    ]

    # Verificar factibilidad y mensajes de error
    is_feasible, error_messages = vrp_problem.routes_are_feasible(duplicate_routes)

    # La solución no debe ser factible
    assert not is_feasible

    # Debe haber un mensaje de error sobre nodos duplicados
    assert any("duplicados" in msg for msg in error_messages)

    # Verificar que el mensaje contiene los nodos duplicados
    duplicate_msg = next(msg for msg in error_messages if "duplicados" in msg)
    assert "2" in duplicate_msg
    assert "3" in duplicate_msg

    # Evaluar con penalizaciones detalladas
    _, penalties, eval_messages = vrp_problem.evaluate_routes_detailed(duplicate_routes)

    # Debe haber una penalización por duplicados
    assert penalties["duplicate"] > 0

    # La penalización debe ser proporcional al número de duplicados
    duplicates = {2: 2, 3: 2}  # Nodos 2 y 3 aparecen dos veces cada uno
    expected_penalty = sum(count - 1 for count in duplicates.values()) * PENALTY_MISSING
    assert penalties["duplicate"] == expected_penalty


def test_routes_are_feasible_return_format(vrp_problem):
    """Test que routes_are_feasible devuelve una tupla (bool, list[str])."""
    # Generar rutas factibles
    routes = vrp_problem.random_routes()

    # Verificar formato de retorno
    result = vrp_problem.routes_are_feasible(routes)

    # Debe ser una tupla de dos elementos
    assert isinstance(result, tuple)
    assert len(result) == 2

    # El primer elemento debe ser un booleano
    assert isinstance(result[0], bool)

    # El segundo elemento debe ser una lista de strings
    assert isinstance(result[1], list)
    assert all(isinstance(msg, str) for msg in result[1])

    # Para una solución factible, la lista de errores debe estar vacía
    assert result[0] is True
    assert len(result[1]) == 0

    # Crear una solución infactible
    infeasible_routes = [
        [0, 1, 2, 0],  # Faltan la mayoría de los clientes
    ]

    # Verificar formato de retorno para solución infactible
    result = vrp_problem.routes_are_feasible(infeasible_routes)

    # El primer elemento debe ser False
    assert result[0] is False

    # El segundo elemento debe ser una lista no vacía de strings
    assert len(result[1]) > 0


def test_evaluate_routes_detailed(vrp_problem):
    """Test que evaluate_routes_detailed devuelve los componentes correctos."""
    # Generar rutas aleatorias
    routes = vrp_problem.random_routes()

    # Evaluar con detalles
    result = vrp_problem.evaluate_routes_detailed(routes)

    # Debe ser una tupla de tres elementos
    assert isinstance(result, tuple)
    assert len(result) == 3

    # Los componentes deben tener los tipos correctos
    distance, penalties, errors = result

    # Distancia debe ser un número
    assert isinstance(distance, (int, float))
    assert distance > 0

    # Penalties debe ser un diccionario con las claves correctas
    assert isinstance(penalties, dict)
    assert "capacity" in penalties
    assert "missing" in penalties
    assert "duplicate" in penalties

    # Errores debe ser una lista de strings
    assert isinstance(errors, list)

    # Para una solución factible, las penalizaciones y errores deben ser cero/vacíos
    assert all(p == 0 for p in penalties.values())
    assert len(errors) == 0
