from typing import ClassVar


class AppError(Exception):
    status_code: ClassVar[int] = 500

    def __init__(self, detail: str = "An unexpected error occurred") -> None:
        self.detail = detail
        super().__init__(detail)


class NoteNotFoundError(AppError):
    status_code = 404

    def __init__(self, note_id: str) -> None:
        super().__init__(f"Note '{note_id}' not found")


class NoteExpiredError(AppError):
    status_code = 410

    def __init__(self, note_id: str) -> None:
        super().__init__(f"Note '{note_id}' has expired")


class InvalidPasswordError(AppError):
    status_code = 401

    def __init__(self) -> None:
        super().__init__("Invalid password")


class NotAuthorizedError(AppError):
    status_code = 401

    def __init__(self, detail: str = "Not authorized") -> None:
        super().__init__(detail)


class ForbiddenError(AppError):
    status_code = 403

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail)
