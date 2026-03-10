import httpx


class EventsProviderError(Exception):
    """Родительский класс для event provider ошибок"""


class EventsProviderAuthError(EventsProviderError):
    """
    Не авторизован 401, то есть отсутствует
     или предоставлен не верный API key
    """


class EventsProviderNotFoundError(EventsProviderError):
    """Не найден 404"""


class EventsProviderSeatUnavailableError(EventsProviderError):
    """Место уже занято 400"""


def raise_for_status(response: httpx.Response) -> None:
    """
    Проверяет статус HTTP-ответа и бросает соответствующее исключение.
    response: HTTP-ответ от Events Provider API.
    Raises:
        EventsProviderAuthError: При HTTP 401.
        EventsProviderNotFoundError: При HTTP 404.
        EventsProviderSeatUnavailableError: При HTTP 400 с сообщением 'already sold'.
        EventsProviderError: При HTTP 400 с другой причиной или HTTP 5xx.
    """

    if response.status_code == 401:
        raise EventsProviderAuthError("Отсутствует либо неверный API key")
    if response.status_code == 404:
        raise EventsProviderNotFoundError("Данные не найдены")
    if response.status_code == 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        if "already sold" in str(detail):
            raise EventsProviderSeatUnavailableError(str(detail))
        raise EventsProviderError(f"Не корректный запрос: {detail}")
    if response.status_code >= 500:
        raise EventsProviderError(
            f"Ошибка внутри сервера {response.status_code}: {response.text[:200]}"
        )
    response.raise_for_status()
