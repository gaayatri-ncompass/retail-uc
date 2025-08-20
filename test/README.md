# Bad Data Testing Suite - Usage Guide

This guide explains how to use the bad data testing tools to validate your ETL pipeline's data quality handling.

## Test Files Overview

### 1. `simple_bad_data_test.py` ⭐ (Recommended)

**Purpose**: Quick validation that your pipeline properly rejects bad data
**Runtime**: ~30 seconds
**Use When**: Regular testing, CI/CD integration

**What it tests**:

- Missing required fields (empty IDs)
- Invalid data formats (bad emails, non-numeric prices)
- Foreign key violations (non-existent references)
- Data type mismatches

**How to run**:

```bash
python test\simple_bad_data_test.py
```

### 2. `test_bad_data_generator.py`

**Purpose**: Comprehensive bad data generation with detailed scenarios
**Runtime**: ~2-3 minutes
**Use When**: Thorough testing, quality audits

**What it tests**:

- All validation rules
- Edge cases and boundary conditions
- Multiple data quality dimensions
- Complex rejection scenarios

**How to run**:

```bash
python test\test_bad_data_generator.py
```

### 3. `test_data_quality.py`

**Purpose**: Scenario-based testing for specific data quality rules
**Runtime**: ~1-2 minutes
**Use When**: Testing specific validation logic

**What it tests**:

- Categorized data quality scenarios
- Specific validation rule testing
- Business rule compliance

**How to run**:

```bash
python test\test_data_quality.py
```

### 4. `quick_bad_data_test.py`

**Purpose**: Lightweight version with minimal dependencies
**Runtime**: ~20 seconds
**Use When**: Quick checks, debugging

### 5. `run_bad_data_tests.py`

**Purpose**: Interactive menu for running different tests
**Runtime**: Variable
**Use When**: Interactive testing sessions

## Quick Start Guide

### Step 1: Run the Basic Test

```bash
# Navigate to your project directory
cd "C:\Users\Deva Sahithiyan\Desktop\RetailSales_UseCase - Copy"

# Run the simple test
python test\simple_bad_data_test.py
```

### Step 2: Review Results

After the test completes, check:

- **Console output**: Shows how many files were rejected
- **rejected_data folder**: Contains CSV files with rejected records
- **Logs**: Detailed information about validation failures

### Step 3: Analyze Rejected Data

```bash
# View rejected data files
dir rejected_data\*.csv

# Check recent log files
dir logs\etl_app_*.log
```

## Expected Test Results

### ✅ Good Results (Pipeline Working Correctly)

- New rejected data files are created
- Console shows "SUCCESS: Bad data was properly rejected!"
- Rejected files contain detailed rejection reasons
- Original data is restored automatically

### ⚠️ Warning Signs (May Need Investigation)

- No rejected files created despite bad data
- Missing rejection reasons in CSV files
- ETL process fails completely
- Data not restored after test

## Interpreting Rejection Files

### File Naming Convention

- `{table_name}_rejected_{timestamp}.csv`
- Example: `factsales_rejected_20250820_095018.csv`

### Key Columns in Rejected Files

- **rejection_reason**: Why the record was rejected
- **rejection_timestamp**: When it was rejected
- **additional_info**: Detailed context (for complex failures)
- **Original columns**: All original data for investigation

### Common Rejection Reasons

1. **"Missing dimension keys"**: Foreign key violations
2. **"Database insertion failed"**: Data type/constraint violations
3. **"Data validation failed"**: Format/business rule violations

## Test Safety Features

### Automatic Backup & Restore

- ✅ Original data is automatically backed up before testing
- ✅ Data is restored even if test fails
- ✅ Backup files are automatically cleaned up

### Non-Destructive Testing

- ✅ Tests use temporary data
- ✅ No permanent changes to your data
- ✅ Can be run multiple times safely

## Integration with Your Workflow

### Regular Testing

```bash
# Add to your daily routine
python test\simple_bad_data_test.py
```

### Before Deployments

```bash
# Run comprehensive tests
python test\test_bad_data_generator.py
```

### CI/CD Integration

```bash
# Add to your build pipeline
python test\simple_bad_data_test.py
if [ $? -eq 0 ]; then
    echo "Data quality tests passed"
else
    echo "Data quality tests failed"
    exit 1
fi
```

## Customizing Tests

### Adding New Bad Data Scenarios

Edit `simple_bad_data_test.py` in the `create_bad_test_data()` function:

```python
# Add new bad data scenario
bad_customers.append({
    'customer_id': 'CUSTOM_TEST',
    'customer_name': 'Custom Bad Data',
    'email': 'your-custom-bad-email-format',
    # ... other fields
})
```

### Modifying Validation Rules

Update validation schemas in `src/utils/validator.py`:

```python
# Add new validation rule
customer_schema = {
    "customer_id": {"type": "string", "required": True},
    "age": {"type": "integer", "min": 0, "max": 120},  # New rule
    # ... existing rules
}
```

## Troubleshooting

### Test Won't Run

1. Check Python environment is activated
2. Ensure you're in the project root directory
3. Verify all dependencies are installed

### No Rejected Files Created

1. Check if validation is enabled in your pipeline
2. Verify rejected_data folder exists and is writable
3. Review console output for error messages

### ETL Fails During Test

1. Check database connectivity
2. Verify staging and warehouse databases exist
3. Review log files for detailed error messages

## Best Practices

### 1. Run Tests Regularly

- Before code changes
- After validation rule updates
- During quality audits

### 2. Monitor Rejection Rates

- Track rejection percentages over time
- Set alerts for high rejection rates
- Investigate unusual patterns

### 3. Document Findings

- Keep notes on rejection patterns
- Update validation rules based on findings
- Share results with data stakeholders

### 4. Automate Where Possible

- Include in CI/CD pipelines
- Schedule regular quality checks
- Automate rejection rate monitoring

## Support

For issues or questions:

1. Check the console output and log files
2. Review the BAD_DATA_TEST_RESULTS.md file
3. Examine rejected data CSV files for patterns
4. Verify your validation rules are working as expected

Remember: The goal is to ensure your pipeline gracefully handles bad data while maintaining detailed audit trails for investigation and remediation.
