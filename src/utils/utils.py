from fastapi import Request


def fix_scheme(url: str) -> str:
    """
    Заменяет схему postgres:// или postgresql:// на postgresql+asyncpg://
    для совместимости с asyncpg-драйвером SQLAlchemy.

    Args: url: Строка подключения к БД.

    Returns:Строка подключения с корректной схемой.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix) :]
    return url


def build_pagination_urls(
    request: Request, page: int, page_size: int, total: int
) -> tuple[str | None, str | None]:
    """
    Вычисляет URL следующей и предыдущей страницы для пагинации.
    Args:
        request: Текущий HTTP-запрос (нужен для base_url и query params).
        page: Текущий номер страницы.
        page_size: Размер страницы.
        total: Общее количество записей.
    Returns:
        Кортеж (next_url, prev_url), каждый элемент — строка или None.
    """
    base_url = str(request.base_url).rstrip("/")
    params = dict(request.query_params)

    def build_url(p: int) -> str:
        params["page"] = str(p)
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}/api/events?{qs}"

    next_url = build_url(page + 1) if page * page_size < total else None
    prev_url = build_url(page - 1) if page > 1 else None
    return next_url, prev_url
