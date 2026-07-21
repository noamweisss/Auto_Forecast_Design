"""Validated forecast values admitted to the future rendering boundary."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.data.snapshots import FeedType, ForecastProvenance


@dataclass
class CityForecast:
    """One configured city's publishable values for one exact date."""

    city_id: str
    city_name_hebrew: str
    city_name_english: str
    internal_key: str
    forecast_date: date
    min_temp: int
    max_temp: int
    weather_code: str
    weather_description_hebrew: str
    weather_description_english: str
    provenance: ForecastProvenance
    humidity_min: Optional[int] = None
    humidity_max: Optional[int] = None
    wind_direction: Optional[str] = None
    wind_speed: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.city_id, str) or not self.city_id.strip():
            raise ValueError("city_id is required")
        if not isinstance(self.weather_code, str) or not self.weather_code.strip():
            raise ValueError(f"weather_code is required for city {self.city_id}")
        if type(self.min_temp) is not int or type(self.max_temp) is not int:
            raise ValueError(f"temperatures must be integers for city {self.city_id}")
        if self.min_temp > self.max_temp:
            raise ValueError(
                f"min_temp ({self.min_temp}) cannot be greater than "
                f"max_temp ({self.max_temp}) for city {self.city_id}"
            )
        if not isinstance(self.provenance, ForecastProvenance):
            raise ValueError(f"provenance is required for city {self.city_id}")
        if self.provenance.feed_type is not FeedType.CITIES:
            raise ValueError(f"city {self.city_id} provenance must use the cities feed")

    @property
    def is_fallback(self) -> bool:
        """Whether selection crossed a fallback boundary recorded in provenance."""
        return self.provenance.fallback_reason is not None


@dataclass
class CountryForecast:
    """Publishable country narrative for one exact date."""

    forecast_date: date
    description_hebrew: str
    description_english: str
    provenance: ForecastProvenance
    warning_hebrew: Optional[str] = None
    warning_english: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, ForecastProvenance):
            raise ValueError("country provenance is required")
        if self.provenance.feed_type is not FeedType.COUNTRY:
            raise ValueError("country provenance must use the country feed")
        if not self.description_hebrew or not self.description_hebrew.strip():
            raise ValueError("country description_hebrew is required")

    @property
    def is_fallback(self) -> bool:
        return self.provenance.fallback_reason is not None


@dataclass
class DailyForecast:
    """The only complete forecast shape allowed onto the rendering path."""

    forecast_date: date
    country_forecast: CountryForecast
    city_forecasts: list[CityForecast]

    def __post_init__(self) -> None:
        if len(self.city_forecasts) != 15:
            raise ValueError(
                "DailyForecast requires exactly 15 city forecasts; "
                f"found {len(self.city_forecasts)}"
            )
        city_ids = [city.city_id for city in self.city_forecasts]
        if len(set(city_ids)) != len(city_ids):
            raise ValueError("DailyForecast city IDs must be unique")
        if self.country_forecast.forecast_date != self.forecast_date:
            raise ValueError("Country forecast_date must equal DailyForecast forecast_date")
        mismatched = [
            city.city_id
            for city in self.city_forecasts
            if city.forecast_date != self.forecast_date
        ]
        if mismatched:
            raise ValueError(
                "Every city forecast_date must equal DailyForecast forecast_date; "
                f"mismatched IDs={mismatched}"
            )

    @property
    def is_fallback(self) -> bool:
        return self.country_forecast.is_fallback or any(
            city.is_fallback for city in self.city_forecasts
        )

    def get_city_by_id(self, city_id: str) -> Optional[CityForecast]:
        """Return the matching city, or None if no city has that ID."""
        return next((city for city in self.city_forecasts if city.city_id == city_id), None)

    def get_city_by_name(self, name_english: str) -> Optional[CityForecast]:
        """Return the city whose English name matches (case-insensitive), or None."""
        return next(
            (
                city
                for city in self.city_forecasts
                if city.city_name_english.lower() == name_english.lower()
            ),
            None,
        )
