"""The Meal planner integration."""
from http import HTTPStatus
import logging
from typing import Any

import voluptuous as vol
from datetime import date, timedelta


from homeassistant.components import frontend, http, websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util.json import load_json, save_json

from .const import DOMAIN, ICON, NAME, URL_BASE, URL_FRONTEND

_LOGGER = logging.getLogger(__name__)

PERSISTENCE = ".mealplanner.json"

WS_TYPE_MEALPLANNER_DATE = "mealplanner/date"
WS_TYPE_MEALPLANNER_DAYS = "mealplanner/days"
WS_TYPE_MEALPLANNER_DATE_UPDATE = "mealplanner/date/update"

SCHEMA_WEBSOCKET_DATE = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_MEALPLANNER_DATE,
        vol.Optional("date"): datetime
    }
)
SCHEMA_WEBSOCKET_DAYS = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_MEALPLANNER_DAYS,
        vol.Optional("date"): datetime,
        vol.Optional("days"): int
    }
)

SCHEMA_WEBSOCKET_UPDATE_DATE = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_MEALPLANNER_DATE_UPDATE,
        vol.Required("date"): datetime,
        vol.Required("meal"): str,
        vol.Optional("description"): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up meal planner from config flow."""

    data = hass.data[DOMAIN] = MealPlannerData(hass)
    await data.async_load()

    hass.http.register_view(MealPlannerDateView)
    hass.http.register_view(MealPlannerDaysView)
    hass.http.register_view(UpdateMealPlannerView)

    hass.http.register_static_path(
        URL_BASE,
        hass.config.path(URL_FRONTEND),
    )

    if DOMAIN not in hass.data.get("frontend_panels", {}):
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=NAME,
            sidebar_icon=ICON,
            frontend_url_path=DOMAIN,
            config={
                "_panel_custom": {
                    "name": "meal-planner-frontend",
                    "embed_iframe": True,
                    "trust_external": False,
                    "module_url": f"/meal-planner-frontend/main.js",
                }
            },
            require_admin=False,
        )

    # frontend.async_register_built_in_panel(
    #     hass, "mealplanner", "mealplanner", "mdi:food"
    # )

    websocket_api.async_register_command(
        hass,
        WS_TYPE_MEALPLANNER_DATE,
        websocket_handle_date,
        SCHEMA_WEBSOCKET_DATE,
    )
    websocket_api.async_register_command(
        hass,
        WS_TYPE_MEALPLANNER_DAYS,
        websocket_handle_days,
        SCHEMA_WEBSOCKET_DAYS,
    )
    websocket_api.async_register_command(
        hass,
        WS_TYPE_MEALPLANNER_DATE_UPDATE,
        websocket_handle_update,
        SCHEMA_WEBSOCKET_UPDATE_DATE,
    )

    return True


class MealPlannerData:
    """Class to hold meal planner data."""

    def __init__(self, hass):
        """Initialize the meal planner."""
        self.hass = hass
        self.mealplan: dict[int, dict[int, dict[int, dict[str, Any]]]] = {}
    
    async def _async_add_date(self, date: date):
        """Add a date to the mealplan."""

        item = {date.day: {"meal": None, "description": None}}

        if date.year not in self.mealplan:
            self.mealplan.update({date.year: {}})

        if date.month not in self.mealplan[date.year]:
            self.mealplan[date.year].update({date.month: {}})

        if date.day in self.mealplan[date.year][date.month]:
            raise KeyError("Key already exists")
        self.mealplan[date.year][date.month].update(item)

        await self.hass.async_add_executor_job(self.save)

    async def async_get_date(
        self,
        date: date,
    ):
        """Return a date from the mealplan, add date if missing."""

        if date.year not in self.mealplan or date.month not in self.mealplan[date.year]:
            await self._async_add_date(date)

        return self.mealplan[date.year][date.month][date.day]
    
    async def async_get_days(self, startdate: date, days: int = 7):
        """Retrieve mealplan for x number of days."""       

        def calculate_dates(startdate: date, days: int):
            dates = {}
            for i in range(0, days):
                d = startdate + timedelta(days=i)
                dates.update({d: {}})
            return dates
        
        d = calculate_dates(startdate, days)
        
        for key, value in d.items():
            d[key].update(await self.async_get_date(key))

        return d

    async def async_update(self, date: date, data: dict, context=None):
        """Update mealplan."""
        if date.year not in self.mealplan or date.month not in self.mealplan[date.year] or date.day not in self.mealplan[date.year][date.month]:
            raise KeyError

        day = self.mealplan[date.year][date.month][date.day]
        day.update(data)

        await self.hass.async_add_executor_job(self.save)

        return day

    async def async_load(self):
        """Load items."""

        def load():
            """Load the items synchronously."""
            return load_json(self.hass.config.path(PERSISTENCE), default={})

        self.mealplan = await self.hass.async_add_executor_job(load)

    def save(self):
        """Save the items."""
        save_json(self.hass.config.path(PERSISTENCE), self.mealplan)


class MealPlannerDateView(http.HomeAssistantView):
    """View to retrieve meal planner content."""

    url = "/api/mealplanner/{ts}"
    name = "api:mealplanner:ts"

    async def get(self, request, ts):
        """Retrieve mealplan."""
        return self.json(
            await request.app["hass"].data[DOMAIN].async_get_date(date.fromtimestamp(ts))
        )

class MealPlannerDaysView(http.HomeAssistantView):
    """View to retrieve multiple days."""

    url = "/api/mealplanner/{ts}/{days}"
    name = "api:mealplanner:ts:days"

    async def get(self, request, ts, days):
        """Retrieve mealplan."""
        return self.json(
            await request.app["hass"].data[DOMAIN].async_get_days(date.fromtimestamp(ts), days)
        )

class UpdateMealPlannerView(http.HomeAssistantView):
    """View to update meal planner content."""

    url = "/api/mealplanner/{ts}"
    name = "api:mealplanner:ts"

    async def post(self, request, ts):
        """Update a mealplan."""
        data = await request.json()

        try:
            meal = (
                await request.app["hass"]
                .data[DOMAIN]
                .async_update(date.fromtimestamp(ts), data)
            )
            return self.json(meal)
        except KeyError:
            return self.json_message("Date not found", HTTPStatus.NOT_FOUND)
        except vol.Invalid:
            return self.json_message("Date not found", HTTPStatus.BAD_REQUEST)


@websocket_api.async_response
async def websocket_handle_date(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle get mealplan."""
    date = msg.pop("date")

    data = await hass.data[DOMAIN].async_get_date(date)
    connection.send_message(websocket_api.result_message(msg["id"], data))


@websocket_api.async_response
async def websocket_handle_days(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle get number days."""
    date = msg.pop("date")
    days = msg.pop("days")

    data = await hass.data[DOMAIN].async_get_days(date, days)
    connection.send_message(websocket_api.result_message(msg["id"], data))


@websocket_api.async_response
async def websocket_handle_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle update mealplan."""
    msg_id = msg.pop("id")
    date = msg.pop("date")
    msg.pop("type")
    data = msg

    try:
        meal = await hass.data[DOMAIN].async_update(
            date, data, connection.context(msg)
        )
        connection.send_message(websocket_api.result_message(msg_id, meal))
    except KeyError:
        connection.send_message(
            websocket_api.error_message(msg_id, "date_not_found", "Date not found")
        )
