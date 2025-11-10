from dataclasses import asdict
from datetime import datetime, timezone

from botc.model import Game

EVENT = "event"
INFO = "info"
PATCH = "patch"
SPECTATOR_JOINED = "SpectatorJoined"
SPECTATOR_LEFT = "SpectatorLeft"
PLAYER_TAKEN_SEAT = "PlayerTakenSeat"
PLAYER_VACATED_SEAT = "PlayerVacatedSeat"
PLAYER_LEFT = "PlayerLeft"
PHASE_CHANGED = "PhaseChange"


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def construct_envelope(message_type, data, gid):
    return {
        "type": message_type,
        "data": data,
        "gid": gid,
        "ts": _iso_now(),
    }


def construct_event_message(kind, gid, data):
    envelope = construct_envelope(EVENT, data, gid)
    envelope['kind'] = kind
    return envelope


def construct_patch_message(kind, gid, data):
    envelope = construct_envelope(PATCH, data, gid)
    envelope['kind'] = kind
    return envelope


def construct_info_message(gid, data):
    envelope = construct_envelope(INFO, data, gid)
    return envelope


def role_assigned_info_message(gid: str, role_name: str, meta: str):
    return construct_info_message(
        gid,
        {
            "role_name": role_name,
            "meta": meta
        }
    )

"""
def spectator_joined_message(gid: str, spectator_id: str, spectator_name: str):
    return construct_event_message(
        SPECTATOR_JOINED,
        gid,
        {
            "spectator_id": spectator_id,
            "spectator_name": spectator_name
        })
"""

def spectator_left_message(gid: str, spectator_id: str, spectator_name: str):
    return construct_event_message(
        SPECTATOR_LEFT,
        gid,
        {
            "spectator_id": spectator_id,
            "spectator_name": spectator_name
        })

"""
def player_taken_seat(gid: str, spectator_id: str, spectator_name: str, seat: int):
    return construct_event_message(
        PLAYER_TAKEN_SEAT,
        gid,
        {
            "spectator_id": spectator_id,
            "spectator_name": spectator_name,
            "seat": seat
        })
"""

def player_vacated_seat(gid: str, spectator_id: str, spectator_name: str, seat: int):
    return construct_event_message(
        PLAYER_VACATED_SEAT,
        gid,
        {
            "spectator_id": spectator_id,
            "spectator_name": spectator_name,
            "seat": seat
        })


def player_left_message(gid: str, player_id: str, player_name: str):
    return construct_event_message(
        PLAYER_LEFT,
        gid,
        {
            "player_id": player_id,
            "player_name": player_name
        })


def night_prepared_message(gid: str, wake_list: str):
    return construct_patch_message(
        PHASE_CHANGED,
        gid,
        wake_list
    )