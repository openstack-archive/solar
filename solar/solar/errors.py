class SolarError(Exception):
    pass


class CannotFindID(SolarError):
    pass


class CannotFindExtension(SolarError):
    pass


class ParseError(SolarError):
    pass
