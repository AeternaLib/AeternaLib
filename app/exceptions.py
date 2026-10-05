class AeternaError(Exception):
    """Excepción base del dominio."""
    status_code = 400
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ValidationError(AeternaError): pass            # datos incompletos
class NotFoundError(AeternaError): status_code = 404
class BookNotAvailableError(AeternaError): status_code = 409
class LoanNotFoundError(NotFoundError): pass
class LoanAlreadyReturnedError(AeternaError): status_code = 409