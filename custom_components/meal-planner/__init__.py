"""The Meal planner integration."""
from http import HTTPStatus
import logging
from typing import Any

import voluptuous as vol
import datetime


from homeassistant.components import frontend, http, websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util.json import load_json, save_json

from .const import DOMAIN, ICON, NAME, URL_BASE, URL_FRONTEND

_LOGGER = logging.getLogger(__name__)

PERSISTENCE = ".mealplanner.json"

WS_TYPE_MEALPLANNER_WEEK = "mealplanner/year/week"
WS_TYPE_MEALPLANNER_WEEK_UPDATE = "mealplanner/year/week/update"

SCHEMA_WEBSOCKET_WEEK = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_MEALPLANNER_WEEK,
        vol.Optional("year"): int,
        vol.Optional("week"): int,
    }
)

SCHEMA_WEBSOCKET_UPDATE_WEEK = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_MEALPLANNER_WEEK_UPDATE,
        vol.Required("year"): int,
        vol.Required("week"): int,
        vol.Required("day"): str,
        vol.Required("meal"): str,
        vol.Optional("description"): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up meal planner from config flow."""

    data = hass.data[DOMAIN] = MealPlannerData(hass)
    await data.async_load()

    hass.http.register_view(MealPlannerView)
    hass.http.register_view(UpdateMealPlannerView)

    hass.http.register_static_path(
        URL_BASE,
        hass.config.path(URL_FRONTEND),
    )

    if DOMAIN not in hass.data.get("frontend_panels", {}):
        frontend.async_register_built_in_panel(
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

    websocket_api.async_register_command(
        hass,
        WS_TYPE_MEALPLANNER_WEEK,
        websocket_handle_week,
        SCHEMA_WEBSOCKET_WEEK,
    )
    websocket_api.async_register_command(
        hass,
        WS_TYPE_MEALPLANNER_WEEK_UPDATE,
        websocket_handle_update,
        SCHEMA_WEBSOCKET_UPDATE_WEEK,
    )

    return True


class MealPlannerData:
    """Class to hold meal planner data."""

    def __init__(self, hass):
        """Initialize the meal planner."""
        self.hass = hass
        self.mealplan: dict[int, dict[int, dict[str, dict[str, str]]]] = {}

    async def async_get_week(
        self,
        year: str = datetime.date.today().isocalendar().year,
        week: str = datetime.date.today().isocalendar().week,
    ):
        """Return a week from the mealplan, add week if missing."""

        def add_week(year: str, week: str):
            """Add a new week to the mealplan."""
            weekday = {"meal": None, "description": None}
            complete_week = {
                "monday": weekday,
                "tuesday": weekday,
                "wednesday": weekday,
                "thursday": weekday,
                "friday": weekday,
                "saturday": weekday,
                "sunday": weekday,
            }
            if year in self.mealplan:
                self.mealplan[year].update({week: complete_week})
            else:
                self.mealplan.update({year: {}})
                self.mealplan[year].update({week: complete_week})

        if year not in self.mealplan or week not in self.mealplan[year]:
            add_week(year, week)

        await self.hass.async_add_executor_job(self.save)

        return self.mealplan[year][week]

    async def async_update(self, year, week, day, data, context=None):
        """Update mealplan."""
        if year not in self.mealplan and week not in self.mealplan[year]:
            raise KeyError

        day = self.mealplan[year][week][day]
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


class MealPlannerView(http.HomeAssistantView):
    """View to retrieve meal planner content."""

    url = "/api/mealplanner/{year}/{week}"
    name = "api:mealplanner:year:week"

    async def get(self, request, year, week):
        """Retrieve mealplan."""
        return self.json(
            await request.app["hass"].data[DOMAIN].async_get_week(year, week)
        )


class UpdateMealPlannerView(http.HomeAssistantView):
    """View to update meal planner content."""

    url = "/api/mealplanner/{year}/{week}/{day}"
    name = "api:mealplanner:year:week:day"

    async def post(self, request, year, week, day):
        """Update a mealplan."""
        data = await request.json()

        try:
            meal = (
                await request.app["hass"]
                .data[DOMAIN]
                .async_update(year, week, day, data)
            )
            return self.json(meal)
        except KeyError:
            return self.json_message("Week not found", HTTPStatus.NOT_FOUND)
        except vol.Invalid:
            return self.json_message("Week not found", HTTPStatus.BAD_REQUEST)


@websocket_api.async_response
async def websocket_handle_week(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle get mealplan."""
    year = msg.pop("year")
    week = msg.pop("week")

    data = await hass.data[DOMAIN].async_get_week(year, week)
    connection.send_message(websocket_api.result_message(msg["id"], data))


@websocket_api.async_response
async def websocket_handle_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle update mealplan."""
    msg_id = msg.pop("id")
    year = msg.pop("year")
    week = msg.pop("week")
    day = msg.pop("day")
    msg.pop("type")
    data = msg

    try:
        meal = await hass.data[DOMAIN].async_update(
            year, week, day, data, connection.context(msg)
        )
        connection.send_message(websocket_api.result_message(msg_id, meal))
    except KeyError:
        connection.send_message(
            websocket_api.error_message(msg_id, "week_not_found", "Week not found")
        )
