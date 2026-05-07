"""Application layer exceptions."""


class ApplicationError(Exception):
    """Base application error."""
    pass


class UserNotFoundError(ApplicationError):
    """User not found."""
    pass


class ServiceNotFoundError(ApplicationError):
    """Service not found."""
    pass


class AppointmentNotFoundError(ApplicationError):
    """Appointment not found."""
    pass


class AppointmentConflictError(ApplicationError):
    """Appointment time conflict."""
    pass


class InvalidAppointmentTimeError(ApplicationError):
    """Invalid appointment time."""
    pass


class BarberNotAvailableError(ApplicationError):
    """Barber is not available at requested time."""
    pass


class ServiceDurationMismatchError(ApplicationError):
    """Service duration doesn't fit in requested slot."""
    pass


class TimeOffConflictError(ApplicationError):
    """Requested time conflicts with barber's time-off."""
    pass


class UnauthorizedError(ApplicationError):
    """User not authorized for this action."""
    pass


class DuplicateEmailError(ApplicationError):
    """Email already registered."""
    pass


class InvalidCredentialsError(ApplicationError):
    """Invalid login credentials."""
    pass
