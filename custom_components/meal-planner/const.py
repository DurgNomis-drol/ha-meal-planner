"""Constants for the Meal planner integration."""

DOMAIN = "meal-planner"

NAME = "Meal Planner"
ICON = "mdi:chef-hat"
DESCRIPTION = "Meal planner for Home Assistant"
PROJECT_URL = "https://github.com/DurgNomis-drol/ha-meal-planner/"
ISSUE_URL = f"{PROJECT_URL}issues"

FE_VERSION = "0.0.1"

URL_BASE = "/meal-planner-frontend"
URL_FRONTEND = "custom_components/meal-planner/frontend/"


# STARTUP LOG MESSAGE
STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""