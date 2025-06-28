#!/usr/bin/env -S uv run -s
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "async-typer",
#     "loguru",
#     "pydantic",
#     "rich",
#     "rofimoji",
#     "typer",
#     "web-pdb",
# ]
# ///

import asyncio
import dataclasses
import enum
from collections.abc import Awaitable, Callable, Iterable
import functools
import json
import os
import hashlib
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Annotated, Any

import pydantic
import typer
import async_typer
import web_pdb
from loguru import logger


app = async_typer.AsyncTyper()


RestArgs = Annotated[
    list[str],
    typer.Option(default_factory=list, help="Remaining arguments passed to program"),
]


@functools.cache
def get_default_audio_sink():
    return subprocess.run(
        [which("pactl"), "get-default-sink"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()


@dataclasses.dataclass
class KeyProps:
    target_mute_state: str | None = None
    target_volume: str | None = None
    should_whit: bool = False

    def handle(self):
        if self.target_mute_state:
            subprocess.run(
                [
                    "pactl",
                    "set-sink-mute",
                    get_default_audio_sink(),
                    self.target_mute_state,
                ],
                check=True,
            )

        if self.target_volume:
            subprocess.run(
                [
                    "pactl",
                    "set-sink-volume",
                    get_default_audio_sink(),
                    self.target_volume,
                ],
                check=True,
            )

        if self.should_whit:
            run_detach(
                ["play", "aplay", "mpv"],
                Path.home() / "dotfiles" / "assets" / "whit.wav",
            )


XF86_KEYS = {
    "XF86AudioRaiseVolume": KeyProps(
        target_mute_state="0", target_volume="+10%", should_whit=True
    ),
    "XF86AudioLowerVolume": KeyProps(
        target_mute_state="0", target_volume="-10%", should_whit=True
    ),
    "XF86AudioMute": KeyProps(target_mute_state="toggle", should_whit=True),
}


class SwayMsg(enum.Enum):
    RUN_COMMAND = 0
    GET_WORKSPACES = 1
    SUBSCRIBE = 2
    GET_OUTPUTS = 3
    GET_TREE = 4
    GET_MARKS = 5
    GET_BAR_CONFIG = 6
    GET_VERSION = 7
    GET_BINDING_MODES = 8
    GET_CONFIG = 9
    SEND_TICK = 10
    SYNC = 11
    GET_BINDING_STATE = 12
    GET_INPUTS = 100
    GET_SEATS = 101
    EVENT_WORKSPACE = 0x80000000
    EVENT_OUTPUT = 0x80000001
    EVENT_MODE = 0x80000002
    EVENT_WINDOW = 0x80000003
    EVENT_BAR_CONFIG_UPDATE = 0x80000004
    EVENT_BINDING = 0x80000005
    EVENT_SHUTDOWN = 0x80000006
    EVENT_TICK = 0x80000007
    EVENT_BAR_STATE_UPDATE = 0x800000014
    EVENT_INPUT = 0x800000015


class SwayCmdResult(pydantic.BaseModel):
    success: bool
    parse_error: bool = False
    error: str = ""


class SwayBindingInfo(pydantic.BaseModel):
    command: str
    event_state_mask: list[str]
    input_code: int
    input_type: str
    symbol: str | None = None


class SwayEventBinding(pydantic.BaseModel):
    change: str
    binding: SwayBindingInfo


@dataclasses.dataclass
class SwayIPCError(Exception):
    """Raised for errors reported by sway during IPC."""

    message: str
    cmd_results: list[SwayCmdResult] | None = None


@dataclasses.dataclass
class SwayIPC:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    _subscribed: set[SwayMsg] = dataclasses.field(default_factory=set)
    _queues: list[asyncio.Queue] = dataclasses.field(default_factory=list)
    _shutdown: bool = False

    async def write_message(self, message_type: SwayMsg, payload: bytes) -> None:
        logger.debug(f"Write message: {message_type=} {payload=}")
        self.writer.write(
            b"i3-ipc" + struct.pack("=II", message_type.value, len(payload)) + payload
        )
        await self.writer.drain()

    async def read_message(self) -> tuple[SwayMsg, Any]:
        header = await self.reader.readexactly(14)
        header = header.removeprefix(b'i3-ipc')
        payload_size, payload_type = struct.unpack("=II", header)
        payload = await self.reader.readexactly(payload_size)
        message_type = SwayMsg(payload_type)
        payload_json = json.loads(payload)
        logger.debug(f"Read message: {message_type=} {payload_json=}")
        return message_type, payload_json

    async def wait_for_message(self) -> tuple[SwayMsg, Any]:
        logger.debug("Waiting for message...")
        queue = asyncio.Queue()
        self._queues.append(queue)
        msg = await queue.get()
        logger.debug(f"Got message {msg=}")
        self._queues.remove(queue)
        queue.task_done()
        return msg

    async def wait_for_message_of_type(self, message_type: SwayMsg) -> Any:
        logger.debug(f"Wait for message of type {message_type=}")
        while True:
            payload_type, payload = await self.wait_for_message()
            if payload_type == message_type:
                logger.debug(f"Got message of desired type {message_type=}")
                return payload
            logger.debug(f"Got messsage of type {payload_type=} != {message_type=}")

    async def run(self) -> None:
        while True:
            msg = await self.read_message()
            queue_list = list(self._queues)
            for i, queue in enumerate(queue_list, 1):
                logger.debug(f"Putting message in queue {i}/{len(queue_list)}")
                await queue.put(msg)

            if msg[0] == SwayMsg.EVENT_SHUTDOWN:
                logger.debug("Received shutdown message")
                self._shutdown = True
                for queue in self._queues:
                    queue.shutdown(immediate=True)
                return

    async def run_command(self, command: str) -> None:
        await self.write_message(SwayMsg.RUN_COMMAND, command.encode("utf-8"))
        response = await self.wait_for_message_of_type(SwayMsg.RUN_COMMAND)
        cmd_results = [SwayCmdResult.model_validate(x) for x in response]
        if any(not x.success for x in cmd_results):
            raise SwayIPCError(
                f"Error running command: {command}", cmd_results=cmd_results
            )

    async def subscribe(self, *event_type: SwayMsg) -> None:
        if self._subscribed | set(event_type) == self._subscribed:
            return
        self._subscribed.update(event_type)
        await self.write_message(
            SwayMsg.SUBSCRIBE,
            json.dumps([x.value for x in self._subscribed]).encode("utf-8"),
        )
        #response = await self.wait_for_message_of_type(SwayMsg.SUBSCRIBE)
        #if not response["success"]:
        #    raise SwayIPCError(f"Failed to subscribe to: {event_type}")

    async def bindsym(
        self,
        keysym: str,
        modifiers: Iterable[str] = (),
        command: str = "nop",
        cb: Callable[[], Awaitable[Any]] | None = None,
    ):
        mod_set = set(modifiers)
        sym_full = "+".join([*sorted(mod_set), keysym])
        cmd = f"bindsym {sym_full} {command}"
        await self.run_command(cmd)

        if cb:
            await self.subscribe(SwayMsg.EVENT_BINDING)
            while not self._shutdown:
                msg = await self.wait_for_message_of_type(SwayMsg.EVENT_BINDING)
                msg_mod_set = {msg.binding.symbol, *msg.binding.event_state_mask}
                if msg_mod_set == mod_set:
                    cb()


def hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def which(cmd: Iterable[str]) -> Path:
    if isinstance(cmd, str):
        cmd = (cmd,)

    for possible in cmd:
        if found := shutil.which(possible):
            return Path(found)

    raise FileNotFoundError(f"Unable to locate command: {cmd!r}")


def which_setdefault(dct: dict[Any, str], key: Any, search: Iterable[str]) -> str:
    if value := dct.get(key):
        return value

    try:
        path = which(search)
    except FileNotFoundError:
        return

    dct[key] = str(path)
    return str(path)


@app.callback()
def ensure_env() -> None:
    confbot_marker = hash_file(Path(__file__))

    if os.environ.get("CONFBOT_MARKER") == confbot_marker:
        return

    path = os.environ.get("PATH", os.defpath)
    path_parts = [Path(x) for x in path.split(os.pathsep)]
    path_parts = [
        Path.home() / ".cargo" / "bin",
        Path.home() / ".local" / "bin",
        Path.home() / "dotfiles" / "bin",
        *path_parts,
    ]
    os.environ["PATH"] = os.pathsep.join(str(x) for x in path_parts)

    which_setdefault(
        os.environ,
        "BROWSER",
        [
            "google-chrome-stable",
            "google-chrome",
            "chromium",
            "firefox",
            "netsurf",
            "w3m",
        ],
    )

    which_setdefault(os.environ, "XTERM", ["kitty", "urxvt", "xterm"])
    which_setdefault(os.environ, "EDITOR", ["code", "vim", "vi"])
    which_setdefault(os.environ, "PAGER", "less")

    if term := os.environ.get("TERM"):
        if not Path(f"/usr/share/terminfo/{term[0]}/{term}").is_file():
            os.environ["TERM"] = "xterm-256color"

    os.environ["LESS"] = "FRX"
    os.environ["CONFBOT_MARKER"] = confbot_marker


async def run_detach(cmd: str | os.PathLike[str], *args: str | os.PathLike[str]):
    cmd_path = which(cmd)
    await asyncio.create_subprocess_exec(
        cmd_path,
        *args,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@app.command()
def handle_xf86_key(key: Annotated[KeyProps, typer.Argument(parser=XF86_KEYS.get)]):
    key.handle()


@app.command()
def shell(args: RestArgs):
    zsh = which("zsh")
    os.execvpe(zsh, [zsh, *args], os.environ)


@app.async_command()
async def swaymon():
    with web_pdb.catch_post_mortem():
        swayipc_path = os.environ["SWAYSOCK"]
        reader, writer = await asyncio.open_unix_connection(swayipc_path)
        swayipc = SwayIPC(reader, writer)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(swayipc.run())
            await swayipc.subscribe(SwayMsg.EVENT_SHUTDOWN)
            tg.create_task(
                swayipc.bindsym(
                    "Tab", ["Alt_L"], cb=lambda: run_detach(os.environ["XTERM"])
                )
            )


if __name__ == "__main__":
    app()
