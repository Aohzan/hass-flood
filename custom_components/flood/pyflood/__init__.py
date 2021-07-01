"""Get information from Flood."""
import asyncio
from operator import itemgetter
import socket

import aiohttp
import async_timeout


class FloodApi:
    """Class representing the Flood and its API."""

    def __init__(
        self,
        host: str,
        port: int = 80,
        username: str = None,
        password: str = None,
        request_timeout: int = 10,
        session: aiohttp.client.ClientSession = None,
    ) -> None:
        """Init a Flood API."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._request_timeout = request_timeout
        self._api_url = f"http://{host}:{port}/api/"
        self._version = None
        self._mac_address = None

        self._session = session
        self._close_session = False

    async def _request(
        self, url: str, method: str, content: dict = None, params: dict = None
    ) -> dict:
        """Make a request to get data."""
        try_count = 0
        while True:
            try_count += 1
            if self._session is None:
                jar = aiohttp.CookieJar(unsafe=True)
                self._session = aiohttp.ClientSession(
                    headers={"Content-Type": "application/json"}, cookie_jar=jar
                )
                self._close_session = True

            try:
                with async_timeout.timeout(self._request_timeout):
                    response = await self._session.request(
                        method=method, url=url, json=content, params=params
                    )
            except asyncio.TimeoutError as exception:
                raise FloodCannotConnectError(
                    "Timeout occurred while connecting to Flood."
                ) from exception
            except (aiohttp.ClientError, socket.gaierror) as exception:
                raise FloodCannotConnectError(
                    "Error occurred while communicating with Flood."
                ) from exception
            if response.status == 401:
                if try_count < 3:
                    self.auth()
                    continue
                raise FloodInvalidAuthError("Authentication failed with Flood.")

            if response.status:  # == 200:
                result = await response.json()
                response.close()
                return result
            else:
                raise FloodCannotConnectError("Unknown error")

    @property
    def host(self) -> str:
        """Return host name or ip used."""
        return self._host

    @property
    async def connected(self) -> bool:
        """Check if flood is connected to torrent client."""
        data = await self._request(
            method="GET", url=self._api_url + "client/connection-test"
        )
        return data.get("isConnected") is True

    @property
    async def history(self) -> dict:
        """Get all client settings."""
        history = await self._request(
            method="GET",
            url=self._api_url + "history",
            params={"snapshot": "FIVE_MINUTE"},
        )
        return {
            "downloadSpeed": history.get("download", [])[-1],
            "uploadSpeed": history.get("upload", [])[-1],
        }

    async def auth(self) -> bool:
        """Get authentication status after send credentials."""
        data = await self._request(
            method="POST",
            url=self._api_url + "auth/authenticate",
            content={"username": self._username, "password": self._password},
        )
        if data.get("success"):
            return True
        else:
            return False

    async def global_get(self) -> dict:
        """Get all data."""
        return {
            "client_settings": await self._request(
                method="GET", url=self._api_url + "client/settings"
            ),
            "settings": await self._request(
                method="GET", url=self._api_url + "settings"
            ),
            "last_notification": await self.last_notification(),
            "history": await self.history,
            "torrents": await self.torrents(),
            "connected": {"status": await self.connected},
        }

    async def client_settings(self) -> dict:
        """Get all client settings."""
        return await self._request(method="GET", url=self._api_url + "client/settings")

    async def notifications(self) -> dict:
        """Get all notifications."""
        return await self._request(method="GET", url=self._api_url + "notifications")

    async def last_notification(self):
        """Get last notifications."""
        api_notifications = await self._request(
            method="GET", url=self._api_url + "notifications"
        )
        notifications = api_notifications.get("notifications")
        if not notifications:
            return None
        last_notification = notifications[0]

        torrent_name = last_notification.get("data").get(
            "name", last_notification.get("data").get("title", "torrent name not found")
        )

        type_notification = last_notification.get("id", "notification type not found")
        if type_notification == "notification.torrent.finished":
            type_notification = "Finished"
        elif type_notification == "notification.torrent.errored":
            type_notification = "Errored"
        elif type_notification == "notification.feed.torrent.added":
            feed_name = last_notification.get("data").get(
                "feedLabel", "feed name not found"
            )
            type_notification = f"Added from {feed_name}"

        return {
            "title": f"{type_notification}: {torrent_name}",
            "type": last_notification.get("id", "notification type not found"),
            "torrent": torrent_name,
        }

    async def torrents(self) -> dict:
        """Get all client settings."""
        api_torrents = await self._request(method="GET", url=self._api_url + "torrents")
        torrents = api_torrents["torrents"].values()
        completed = list(filter(lambda d: "complete" in d["status"], torrents))
        seeding = list(filter(lambda d: "seeding" in d["status"], torrents))
        downloading = list(filter(lambda d: "downloading" in d["status"], torrents))
        active = list(filter(lambda d: "active" in d["status"], torrents))
        inactive = list(filter(lambda d: "inactive" in d["status"], torrents))
        stopped = list(filter(lambda d: "stopped" in d["status"], torrents))

        return {
            "count": len(torrents),
            "completed": len(completed),
            "downloading": len(downloading),
            "seeding": len(seeding),
            "stopped": len(stopped),
            "inactive": len(inactive),
            "active": len(active),
        }

    async def set_download_limit(self, speed: int) -> None:
        """Set download speed limit in kB/s."""
        await self._request(
            method="PATCH",
            url=self._api_url + "client/settings",
            content={"throttleGlobalDownSpeed": speed * 1024},
        )

    async def set_upload_limit(self, speed: int) -> None:
        """Set upload speed limit in kB/s."""
        await self._request(
            method="PATCH",
            url=self._api_url + "client/settings",
            content={"throttleGlobalUpSpeed": speed * 1024},
        )

    async def stop_all(self) -> None:
        """Stop all torrents."""
        api_torrents = await self._request(method="GET", url=self._api_url + "torrents")
        torrents = api_torrents["torrents"].values()
        torrents_hashes = {"hashes": list(map(itemgetter("hash"), torrents))}
        await self._request(
            method="POST",
            url=self._api_url + "torrents/stop",
            content=torrents_hashes,
        )

    async def start_all(self) -> None:
        """Start all torrents."""
        api_torrents = await self._request(method="GET", url=self._api_url + "torrents")
        torrents = api_torrents.get("torrents", {}).values()
        torrents_hashes = {"hashes": list(map(itemgetter("hash"), torrents))}
        await self._request(
            method="POST",
            url=self._api_url + "torrents/start",
            content=torrents_hashes,
        )

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info) -> None:
        """Async exit."""
        await self.close()


class FloodCannotConnectError(Exception):
    """Exception to indicate an error in connection."""


class FloodInvalidAuthError(Exception):
    """Exception to indicate an error in authentication."""
