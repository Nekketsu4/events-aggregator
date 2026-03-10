class EventError(Exception):
    """Родительский класс для ошибок event"""


class EventNotFoundError(EventError):
    """404 Событие не найдено"""

    pass


class EventNotPublishedError(EventError):
    """400 Событие не опубликовано"""

    pass


class RegistrationDeadlinePassedError(EventError):
    """400 Истек срок регистрации места на событие"""

    pass


class SeatUnavailableError(EventError):
    """400 Место недоступно"""

    pass


class TicketNotFoundError(EventError):
    """404 Билет не найден"""

    pass


class EventAlreadyPassedError(EventError):
    """400 Событие уже прошло"""

    pass
