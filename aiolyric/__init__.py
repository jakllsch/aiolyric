"""Lyric: Init"""
from aiohttp import ClientError, ClientSession, ClientResponse
from asyncio import CancelledError, TimeoutError, get_event_loop
from datetime import datetime, timedelta
from typing import cast, List

from .const import BASE_URL
from .exceptions import LyricException, LyricAuthenticationException
from .objects.base import LyricBase
from .objects.device import LyricDevice
from .objects.location import LyricLocation


class Lyric(LyricBase):
    """Handles authentication refresh tokens."""

    def __init__(self, client: "LyricClient", client_id: str) -> None:
        """Initialize the token manager class."""
        self._client = client
        self._client_id = client_id
        self._devices: List[LyricDevice] = []
        self._locations: List[LyricLocation] = []

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def devices(self) -> List[LyricDevice]:
        return self._devices

    @property
    def locations(self) -> List[LyricLocation]:
        return self._locations

    async def get_devices(self, location_id: int) -> None:
        """Get Devices."""
        response: ClientResponse = await self._client.get(
            f"{BASE_URL}/devices?apikey={self.client_id}&locationId={location_id}"
        )
        json = await response.json()
        self.logger.debug(json)
        self._devices = [LyricDevice(self._client, device) for device in json or []]

    async def get_locations(self) -> None:
        """Get Locations."""
        response: ClientResponse = await self._client.get(
            f"{BASE_URL}/locations?apikey={self.client_id}"
        )
        json = await response.json()
        self.logger.debug(json)
        self._locations = [
            LyricLocation(self._client, location) for location in json or []
        ]

    async def update_thermostat(
        self,
        location_id: str,
        device: LyricDevice,
        mode=None,
        heatSetpoint=None,
        coolSetpoint=None,
        AutoChangeover=None,
        thermostatSetpointStatus=None,
        nextPeriodTime=None,
    ) -> dict:
        """Update Theremostat."""
        if mode is None:
            mode = device.operationMode
        if heatSetpoint is None:
            heatSetpoint = device.heatSetpoint
        if coolSetpoint is None:
            coolSetpoint = device.coolSetpoint

        if "thermostatSetpointStatus" in device.changeableValues:
            if thermostatSetpointStatus is None:
                thermostatSetpointStatus = device.thermostatSetpointStatus

        if "autoChangeoverActive" in device.changeableValues:
            if AutoChangeover is None:
                AutoChangeover = device.changeableValues.get("autoChangeoverActive")

        data = {
            "mode": mode,
            "heatSetpoint": heatSetpoint,
            "coolSetpoint": coolSetpoint,
        }

        if "thermostatSetpointStatus" in device.changeableValues:
            data["thermostatSetpointStatus"] = thermostatSetpointStatus
        if "autoChangeoverActive" in device.changeableValues:
            data["autoChangeoverActive"] = AutoChangeover
        if nextPeriodTime is not None:
            data["nextPeriodTime"] = nextPeriodTime

        response: ClientResponse = await self._client.post(
            f"{BASE_URL}/devices/thermostats/{device.deviceID}",
            params={"apikey": self._client_id, "locationId": location_id},
            data=data,
        )
        return await cast(dict, await response.json())

    async def update_fan(
        self, location_id: str, device: LyricDevice, mode: str
    ) -> dict:
        """Update Fan."""
        if mode is None:
            mode = device.fanMode

        response: ClientResponse = await self._client.post(
            f"{BASE_URL}/devices/thermostats/{device.deviceID}/fan",
            params={"apikey": self._client_id, "locationId": location_id},
            data={"mode": mode},
        )
        return await cast(dict, await response.json())
