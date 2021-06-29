import json


class IllegalHttpMethod(Exception):
    """Exception raised when a request method is not supported by the api"""
    pass


class WikiRate4PyException(Exception):
    """Base exception for wikirate4py"""
    pass


class HTTPException(WikiRate4PyException):
    """Exception raised when an HTTP request fails"""

    def __init__(self, response):
        self.response = response

        self.api_errors = []
        self.api_codes = []
        self.api_messages = []

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            super().__init__(f"{response.status_code} {response.reason}")
        else:
            errors = response_json.get("errors", {})
            error_text = "\t"
            for k, v in errors.items():
                error_text += k + ": " + str(v)

            super().__init__(
                f"{response.status_code} {response.reason}{error_text}"
            )


class BadRequestException(HTTPException):
    """Exception raised for a 400 HTTP status code"""
    pass


class UnauthorizedException(HTTPException):
    """Exception raised for a 401 HTTP status code"""
    pass


class ForbiddenException(HTTPException):
    """Exception raised for a 403 HTTP status code"""
    pass


class NotFoundException(HTTPException):
    """Exception raised for a 404 HTTP status code"""
    pass


class TooManyRequestsException(HTTPException):
    """Exception raised for a 429 HTTP status code"""
    pass


class WikiRateServerErrorException(HTTPException):
    """Exception raised for a 5xx HTTP status code"""
    pass
