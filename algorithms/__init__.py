from .sho import SHO
from .apo import APO
from .egto import EGTO
from .fsa import FSA
from .foa import FOA
from .woa import WOA
from .hho import HHO
from .mrfo import MRFO
from .sma import SMA
from .gto import GTO
from .ewa import EWA
from .aha import AHA
from .rro import RRO
from .gvoa import GVOA
from .smo import SMO
from .opa import OPA

# Definir todos los algoritmos en un diccionario
ALGORITHMS = {
    "sho": SHO,
    "apo": APO,
    "egto": EGTO,
    "fsa": FSA,
    "foa": FOA,
    "woa": WOA,
    "hho": HHO,
    "mrfo": MRFO,
    "sma": SMA,
    "gto": GTO,
    "ewa": EWA,
    "aha": AHA,
    "rro": RRO,
    "gvoa": GVOA,
    "smo": SMO,
    "opa": OPA,
}