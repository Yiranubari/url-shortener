class URLShortenerError(Exception):
    pass


class ShortURLNotFoundError(URLShortenerError):
    pass


class ShortCodeAllocationError(URLShortenerError):
    pass

