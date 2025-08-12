class ETLError(Exception):

    def __init__(self, message, error_code=None, component=None):
        self.message = message
        self.error_code = error_code
        self.component = component
        super().__init__(self.message)

    def __str__(self):
        error_msg = f"ETL Error: {self.message}"
        if self.component:
            error_msg = f"[{self.component}] {error_msg}"
        if self.error_code:
            error_msg = f"{error_msg} (Code: {self.error_code})"
        return error_msg


class ExtractionError(ETLError):

    def __init__(self, message, error_code=None):
        super().__init__(message, error_code, "EXTRACTION")


class TransformationError(ETLError):

    def __init__(self, message, error_code=None):
        super().__init__(message, error_code, "TRANSFORMATION")


class LoadingError(ETLError):

    def __init__(self, message, error_code=None):
        super().__init__(message, error_code, "LOADING")


class DatabaseError(ETLError):

    def __init__(self, message, error_code=None):
        super().__init__(message, error_code, "DATABASE")
