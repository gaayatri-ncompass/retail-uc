"""
Load Module for ETL Pipeline
============================

This module contains all loading-related functionality organized into:
- data_loader: Staging data loading with incremental support
- table_creator: Database table creation and schema management
- dimension_loader: Dimension table loading with incremental updates
- fact_loaders: All fact table loading functionality (sales & inventory)
- loader: Main orchestration and coordination
"""

from .loader import run_loading, load_data_to_warehouse, get_loading_statistics
from .table_creator import create_warehouse_tables
from .dimension_loader import load_all_dimensions
from .fact_loaders import load_fact_sales, load_fact_inventory

__all__ = [
    'run_loading',
    'load_data_to_warehouse',
    'get_loading_statistics',
    'create_warehouse_tables',
    'load_all_dimensions',
    'load_fact_sales',
    'load_fact_inventory'
]

__version__ = "2.1.0"
__author__ = "ETL Pipeline Team"
