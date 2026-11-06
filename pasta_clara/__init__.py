"""Pasta Clara: organize cópias, preservando os originais."""
from .core import OrganizationError, Plan, apply_plan, make_plan

__all__ = ['OrganizationError', 'Plan', 'apply_plan', 'make_plan']
__version__ = '1.0.0'
