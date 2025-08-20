"""
Load Module for ETL Pipeline
============================

This module contains all loading-related functionality organized into:
- table_creator: Database table creation and schema management
- dimension_loader: Dimension table loading with incremental updates
- fact_sales_loader: Sales fact table loading with validation
- fact_inventory_loader: Inventory fact table loading with validation
- loader: Main orchestration and coordination
"""

from .loader import run_loading, load_data_to_warehouse, get_loading_statistics, validate_warehouse_integrity
from .table_creator import create_warehouse_tables
from .dimension_loader import load_all_dimensions
from .fact_sales_loader import load_fact_sales
from .fact_inventory_loader import load_fact_inventory

__all__ = [
    'run_loading',
    'load_data_to_warehouse',
    'get_loading_statistics',
    'validate_warehouse_integrity',
    'create_warehouse_tables',
    'load_all_dimensions',
    'load_fact_sales',
    'load_fact_inventory'
]

__version__ = "2.0.0"
__author__ = "ETL Pipeline Team"
