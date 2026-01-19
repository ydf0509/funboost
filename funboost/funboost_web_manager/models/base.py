# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
Base module for SQLAlchemy ORM models.

This module provides the declarative base class and common imports used by all model modules.
All model classes should inherit from the Base class defined here.

Exports:
    - Base: SQLAlchemy declarative base class
    - Common SQLAlchemy types and utilities
    - Common Python types for type hints
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Set

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

# SQLAlchemy declarative base - all models inherit from this
Base = declarative_base()
