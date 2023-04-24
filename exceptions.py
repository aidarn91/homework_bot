class SendMessageException(Exception):
    """Ошибка отправки сообщения."""

    pass


class SendMessageError(Exception):
    """Кастомная ошибка при отказе сервера в обслуживании."""

    pass


class EndpointUnexpectedStatusError(Exception):
    """Кастомная ошибка при неожидаемом статусе запроса к эндпоинту."""

    pass


class GetAPIAnswerException(Exception):

    pass


class TheAnswerIsNot200Error(Exception):
    """Ответ сервера не равен 200."""

    pass


class RequestExceptionError(Exception):
    """Ошибка запроса."""

    pass