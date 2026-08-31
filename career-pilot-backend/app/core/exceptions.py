class ApplicationError(Exception):
    detail = "Application error"

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class NotFoundError(ApplicationError):
    detail = "Resource not found"


class ConflictError(ApplicationError):
    detail = "Resource already exists"


class UserNotFoundError(NotFoundError):
    detail = "User not found"


class UserAlreadyExistsError(ConflictError):
    detail = "A user with this email already exists"


class CareerProfileNotFoundError(NotFoundError):
    detail = "Career profile not found"


class CareerProfileAlreadyExistsError(ConflictError):
    detail = "This user already has a career profile"


class EducationNotFoundError(NotFoundError):
    detail = "Education not found"


class ExperienceNotFoundError(NotFoundError):
    detail = "Experience not found"


class ProjectNotFoundError(NotFoundError):
    detail = "Project not found"


class SkillNotFoundError(NotFoundError):
    detail = "Skill not found"


class DuplicateSkillError(ConflictError):
    detail = "This skill already exists on the profile"


class AuthenticationError(ApplicationError):
    detail = "Authentication required"


class InvalidCredentialsError(AuthenticationError):
    detail = "Invalid email or password"


class SessionExpiredError(AuthenticationError):
    detail = "Session expired"


class SessionRevokedError(AuthenticationError):
    detail = "Session has been revoked"


class ProfileAccessDeniedError(ApplicationError):
    detail = "You do not have access to this profile resource"
