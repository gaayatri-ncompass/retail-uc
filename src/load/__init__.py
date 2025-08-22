"""
Load Module for ETL Pipeline - Cleaned & Simplified
===================================================

This module contains essential loading functionality:
- data_loader: Staging data loading with incremental support
- table_creator: Database table creation and schema management  
- dimension_loader: Dimension table loading (optimized)
- simplified_fact_loaders: Pure fact table loading (sales & inventory)
- loader: Main orchestration and coordination

All unused files have been removed for better maintainability.
"""

from .loader import run_loading, load_data_to_warehouse, get_loading_statistics
from .table_creator import create_warehouse_tables
from .dimension_loader import load_all_dimensions
from .simplified_fact_loaders import load_fact_sales, load_fact_inventory

__all__ = [
    'run_loading',
    'load_data_to_warehouse',
    'get_loading_statistics',
    'create_warehouse_tables',
    'load_all_dimensions',
    'load_fact_sales',
    'load_fact_inventory'
]

__version__ = "3.0.0"
__author__ = "ETL Pipeline Team"
__status__ = "Clean & Optimized"
