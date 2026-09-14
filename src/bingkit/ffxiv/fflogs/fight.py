import os

import httpr

from .model.fights import Fight, FightsResponse
from .model.summary import Event, SummaryResponse

BASE_URL = "https://www.fflogs.com/v1"
FFLOGS_API_KEY_ENV = "FFLOGS_API_KEY"

_client = httpr.Client()


def _api_key(api_key: str | None = None) -> str:
    key = api_key or os.getenv(FFLOGS_API_KEY_ENV)
    if not key:
        msg = "FFLOGS API key is required"
        raise ValueError(msg)
    return key


def get_fight(report_code: str, fight_id: int, api_key: str | None = None) -> Fight:
    api_key = _api_key(api_key)
    url = f"{BASE_URL}/report/fights/{report_code}"
    resp = _client.get(url, params={"api_key": api_key, "translate": "false"})
    data: FightsResponse = resp.raise_for_status().json()
    for fight in data["fights"]:
        if fight["id"] == fight_id:
            return fight
    msg = f"fight {fight_id} not found in report {report_code}"
    raise ValueError(msg)


def get_all_fight_events(
    report_code: str,
    fight_id: int,
    api_key: str | None = None,
) -> list[Event]:
    fight = get_fight(
        report_code,
        fight_id,
        api_key,
    )

    start: int = fight["start_time"]
    end: int = fight["end_time"]

    events: list[Event] = []

    while start < end:
        resp = _client.get(
            f"{BASE_URL}/report/events/summary/{report_code}",
            params={
                "api_key": api_key,
                "start": start,
                "end": end,
                "translate": "false",
            },
        )

        data: SummaryResponse = resp.raise_for_status().json()

        events.extend(data.get("events", []))

        next_timestamp = data.get("nextPageTimestamp")

        if next_timestamp is None:
            break

        if next_timestamp <= start:
            msg = f"pagination did not advance: {start = } {next_timestamp = }"
            raise RuntimeError(msg)

        start = next_timestamp

    return events
