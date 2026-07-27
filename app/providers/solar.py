from datetime import datetime, timedelta, date
import zoneinfo
import logging

from astral import LocationInfo
from astral.sun import sun, dawn, dusk, noon

from app.config import settings
from app.providers.base import Provider, ScheduleConfig

logger = logging.getLogger(__name__)


class SolarProvider(Provider):
    name = "solar"

    async def fetch(self) -> dict:
        tz = zoneinfo.ZoneInfo(settings.tz)
        now = datetime.now(tz)
        location = LocationInfo(
            name="Home",
            region="",
            timezone=settings.tz,
            latitude=settings.latitude,
            longitude=settings.longitude,
        )

        try:
            s = sun(location.observer, date=now.date(), tzinfo=tz)
            sunrise = s["sunrise"]
            sunset = s["sunset"]
        except Exception as e:
            logger.error("Failed to compute sun times: %s", e)
            # period must be day/night — "daytime" is a phase value, and using it
            # here meant every solar rule silently stopped matching on failure.
            fallback_period = "day" if 6 <= now.hour < 18 else "night"
            return {
                "sunrise": "06:00",
                "sunset": "18:00",
                "period": fallback_period,
                "phase": "daytime" if fallback_period == "day" else (
                    "before_sunrise" if now.hour < 6 else "after_sunset"
                ),
                "dawn": "05:30",
                "dusk": "18:30",
                "solar_noon": "12:00",
                "error": str(e),
            }

        try:
            dawn_time = dawn(location.observer, date=now.date(), tzinfo=tz)
        except Exception as e:
            logger.debug("astral dawn() unavailable (%s), deriving from sunrise/sunset", e)
            dawn_time = sunrise - timedelta(minutes=30)

        try:
            dusk_time = dusk(location.observer, date=now.date(), tzinfo=tz)
        except Exception as e:
            logger.debug("astral dusk() unavailable (%s), deriving from sunrise/sunset", e)
            dusk_time = sunset + timedelta(minutes=30)

        try:
            noon_time = noon(location.observer, date=now.date(), tzinfo=tz)
        except Exception as e:
            logger.debug("astral noon() unavailable (%s), deriving from sunrise/sunset", e)
            noon_time = sunrise + (sunset - sunrise) / 2

        if now < sunrise:
            phase = "before_sunrise"
            period = "night"
        elif now > sunset:
            phase = "after_sunset"
            period = "night"
        else:
            phase = "daytime"
            period = "day"

        return {
            "sunrise": sunrise.strftime("%H:%M"),
            "sunset": sunset.strftime("%H:%M"),
            "period": period,
            "phase": phase,
            "dawn": dawn_time.strftime("%H:%M"),
            "dusk": dusk_time.strftime("%H:%M"),
            "solar_noon": noon_time.strftime("%H:%M"),
        }

    def schedule(self) -> ScheduleConfig:
        # Solar transitions (sunrise/sunset) are scheduled precisely by the
        # engine scheduler. Daily refresh at midnight to recompute times.
        return ScheduleConfig(type="cron", kwargs={"hour": 0, "minute": 1})

    def ttl(self) -> timedelta:
        return timedelta(hours=25)

    @staticmethod
    def compute_fresh(tz_name: str, lat: float, lon: float) -> dict:
        """Compute solar state for right now — called inline by the evaluator."""
        tz = zoneinfo.ZoneInfo(tz_name)
        now = datetime.now(tz)
        location = LocationInfo(
            name="Home", region="", timezone=tz_name,
            latitude=lat, longitude=lon,
        )
        try:
            s = sun(location.observer, date=now.date(), tzinfo=tz)
            sunrise = s["sunrise"]
            sunset = s["sunset"]
        except Exception as e:
            logger.error("Failed to compute sun times: %s", e)
            period = "day" if 6 <= now.hour < 18 else "night"
            return {
                "period": period,
                "phase": "daytime" if period == "day" else (
                    "before_sunrise" if now.hour < 6 else "after_sunset"
                ),
                "sunrise": "06:00",
                "sunset": "18:00",
            }

        if now < sunrise:
            period = "night"
            phase = "before_sunrise"
        elif now > sunset:
            period = "night"
            phase = "after_sunset"
        else:
            period = "day"
            phase = "daytime"

        # Also return actual datetime objects for the scheduler
        return {
            "sunrise": sunrise.strftime("%H:%M"),
            "sunset": sunset.strftime("%H:%M"),
            "period": period,
            "phase": phase,
            "_sunrise_dt": sunrise,
            "_sunset_dt": sunset,
        }
