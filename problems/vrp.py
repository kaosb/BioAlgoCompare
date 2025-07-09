"""
Backward compatibility module for VRPProblem.
This module exports the VRPProblemV2 class as VRPProblem for backward compatibility.
"""

from .vrp_v2 import VRPProblemV2 as VRPProblem

__all__ = ['VRPProblem']