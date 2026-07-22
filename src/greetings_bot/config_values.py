from typing import Mapping, Optional


class ConfigurationError(ValueError):
    pass


def integer_value(
    environ: Mapping[str, str],
    name: str,
    default: int,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    try:
        value = int(environ.get(name, str(default)))
    except ValueError as error:
        raise ConfigurationError("{} must be an integer".format(name)) from error
    if minimum is not None and value < minimum:
        raise ConfigurationError(_range_message(name, minimum, maximum))
    if maximum is not None and value > maximum:
        raise ConfigurationError(_range_message(name, minimum, maximum))
    return value


def _range_message(
    name: str, minimum: Optional[int], maximum: Optional[int]
) -> str:
    if minimum is None:
        return "{} must be at most {}".format(name, maximum)
    if maximum is None:
        return "{} must be at least {}".format(name, minimum)
    return "{} must be between {} and {}".format(name, minimum, maximum)
