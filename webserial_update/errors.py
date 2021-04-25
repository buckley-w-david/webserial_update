class WebserialUpdateError(Exception):
    pass

class EqualChapterError(WebserialUpdateError):
    pass

class NoChaptersFoundError(WebserialUpdateError):
    pass

class LocalAheadOfRemoteError(WebserialUpdateError):
    pass
