from cerberus import Validator
import pandas as pd

class DataValidator:
    def __init__(self, schema):
        self.schema = schema
        self.validator = Validator(schema)
        self.invalid_rows = []

    def validate(self,df):
        self.invalid_rows.clear()
        results = df.apply(self.validate_row, axis = 1)
        for idx, result in results.items():
            if not result[0]:
                self.invalid_rows.append({
                    'row_index': idx,
                    'errors': result[1]
                })
        return results

    def validate_row(self, row):
        is_valid = self.validator.validate(row.to_dict())
        return is_valid, self.validator.errors.copy() if not is_valid else None

    def summary(self):
        total = len(self.invalid_rows)
        print(f"Found {total} invalid row{'s' if total != 1 else ''}.")
        for entry in self.invalid_rows:
            print(f"\nRow {entry['row_index']} has the following issues:")
            for field, issue in entry['errors'].items():
                print(f"  - Field '{field}': {issue}")

    def has_errors(self):
        return len(self.invalid_rows) > 0
    
    def get_error_dataframe(self):
        return pd.DataFrame(self.invalid_rows, columns=['row_index', 'errors'])
