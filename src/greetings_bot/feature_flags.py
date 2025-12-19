from dataclasses import dataclass
from typing import Dict, Mapping, Tuple


@dataclass(frozen=True)
class FeatureFlag:
    name: str
    environment_name: str
    default: bool


FEATURE_FLAGS = (
    FeatureFlag("information_requests", "INFO_REQUESTS_ENABLED", False),
    FeatureFlag("greeting_previews", "GREETING_PREVIEWS_ENABLED", True),
    FeatureFlag("weather_summaries", "WEATHER_SUMMARIES_ENABLED", True),
)


class FeatureFlags:
    def __init__(self, values: Mapping[str, bool]) -> None:
        known = {flag.name for flag in FEATURE_FLAGS}
        if set(values) != known:
            raise ValueError("feature flag set does not match definitions")
        self.values = dict(values)

    def enabled(self, name: str) -> bool:
        try:
            return self.values[name]
        except KeyError as error:
            raise KeyError("unknown feature flag") from error

    def public_snapshot(self) -> Tuple[Tuple[str, bool], ...]:
        return tuple((flag.name, self.values[flag.name]) for flag in FEATURE_FLAGS)


def feature_flags_from_env(environ: Mapping[str, str]) -> FeatureFlags:
    values: Dict[str, bool] = {}
    for flag in FEATURE_FLAGS:
        raw = environ.get(
            flag.environment_name, "true" if flag.default else "false"
        ).strip().lower()
        if raw not in ("true", "false"):
            raise ValueError(
                "{} must be true or false".format(flag.environment_name)
            )
        values[flag.name] = raw == "true"
    return FeatureFlags(values)
