# Retail Sales ETL Pipeline

Extract, Transform, Load (ETL) pipeline for retail sales data with incremental loading capabilities and automated data generation.

## Project Structure

```
RetailSales_UseCase/
├── data/                          # Source CSV files
│   ├── customers.csv
│   ├── products.csv
│   ├── stores.csv
│   ├── sales.csv
│   ├── inventory.csv
│   └── suppliers.csv
├── src/                           # Source code
│   ├── extract/                   # Data extraction module
│   │   └── extractor.py
│   ├── transform/                 # Data transformation module
│   │   └── transformer.py
│   ├── load/                      # Data loading module
│   │   └── loader.py
│   ├── analytics/                 # Analytics and reporting
│   │   └── analytics.py
│   └── utils/                     # Utility modules
│       ├── config.py
│       ├── db_connector.py
│       ├── exceptions.py
│       └── validator.py
├── fake_data_generator/           # Node.js data generator
│   ├── index.js
│   └── package.json
├── tests/                         # Test scripts
├── main.py                        # Main ETL orchestrator
├── reset_tables.py                # Database reset utility
├── run_scheduler.py               # Scheduled ETL execution
└── README.md                      # This file
```

## Architecture

### Data Flow

1. **Extract** → CSV files to staging database
2. **Transform** → Data cleaning and star schema creation
3. **Load** → Staging to data warehouse with incremental loading

### Database Design

- **Staging Database**: Raw data from CSV files
- **Data Warehouse**: Star schema with dimension and fact tables

#### Dimension Tables

- `dimcustomer` - Customer information
- `dimproduct` - Product catalog
- `dimstore` - Store locations
- `dimsupplier` - Supplier details
- `dimdate` - Date dimension
- `dimpromotion` - Promotion information

#### Fact Tables

- `factsales` - Sales transactions
- `factinventorysnapshot` - Inventory levels

## Key Implemented Features

- **Incremental Loading**: Only processes new data on subsequent runs
- **Data Validation**: Comprehensive validation using Cerberus
- **Error Handling**: Robust exception handling and logging
- **Star Schema**: Optimized data warehouse design
- **Automated Data Generation**: Continuous fake data creation for testing
- **Batch Processing**: Efficient data loading in configurable batches

## Getting Started

### 1. Database Initialization

Reset and create all tables:

```bash
python reset_tables.py
```

### 2. Create Date Dimension

Generate the comprehensive date dimension (1990-2040):

```bash
python create_date_dimension.py
```

### 3. Run Initial ETL Load

Execute the full ETL pipeline:

```bash
python main.py
```

### 4. Generate New Data

Start continuous data generation:

```bash
cd fake_data_generator
node index.js
```

## Usage Examples

### Manual ETL Execution

```bash
# Initialize database and create tables
python reset_tables.py

# Create comprehensive date dimension (1990-2040)
python create_date_dimension.py

# Run complete ETL pipeline
python main.py

# Run with scheduling (every 10 seconds)
python run_scheduler.py
```

### Data Generation

```bash
cd fake_data_generator
node index.js

# The generator creates:
# - New customers, products, stores
# - Sales transactions
# - Inventory updates
```

### Analytics Queries

Run predefined analytics queries:

```bash
cd src/analytics
python analytics.py
```
