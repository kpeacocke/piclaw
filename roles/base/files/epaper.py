#!/usr/bin/env python3
# pylint: disable=missing-function-docstring,missing-class-docstring,broad-exception-caught
"""Waveshare 4.3" UART e-Paper status display loop.

This script sends protocol frames over UART to:
- wake the panel,
- draw useful host status lines,
- refresh the display,
- put the panel back to sleep.
"""

from __future__ import annotations

import datetime
import importlib
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, List

serial = importlib.import_module("serial")

FRAME_HEADER = 0xA5
FRAME_END = bytes([0xCC, 0x33, 0xC3, 0x3C])

CMD_HANDSHAKE = 0x00
CMD_SLEEP = 0x08
CMD_REFRESH = 0x0A
CMD_CLEAR = 0x2E
CMD_DRAW_TEXT = 0x30


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name, str(default)).strip()
    try:
        return int(value)
    except ValueError:
        return default


def env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(args: Iterable[str], timeout: float = 2.0) -> str:
    try:
        completed = subprocess.run(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return ""
    return (completed.stdout or "").strip()


def pick_serial_device(configured: str) -> str:
    if configured.lower() != "auto":
        return configured

    for candidate in ("/dev/ttyAMA0", "/dev/serial0", "/dev/ttyS0"):
        if os.path.exists(candidate):
            return candidate
    return "/dev/serial0"


def gpio_set(pin: int, level: str) -> None:
    if not command_exists("pinctrl"):
        return
    subprocess.run(
        ["pinctrl", str(pin), "op", level],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def format_uptime(seconds: float) -> str:
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02}h {minutes:02}m"
    return f"{hours:02}h {minutes:02}m"


def get_uptime() -> str:
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as handle:
            seconds = float(handle.read().split()[0])
        return format_uptime(seconds)
    except Exception:
        return "n/a"


def get_cpu_temp() -> str:
    try:
        with open(
            "/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8"
        ) as handle:
            temp_milli_c = int(handle.read().strip())
        return f"{temp_milli_c / 1000.0:.1f}C"
    except Exception:
        return "n/a"


def get_load() -> str:
    try:
        with open("/proc/loadavg", "r", encoding="utf-8") as handle:
            first = handle.read().split()[:3]
        return "/".join(first)
    except Exception:
        return "n/a"


def get_mem_usage() -> str:
    total = 0
    available = 0
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    available = int(line.split()[1])
    except Exception:
        return "n/a"

    if total <= 0:
        return "n/a"

    used = total - available
    pct = int((used * 100) / total)
    return f"{pct}%"


def get_disk_usage() -> str:
    try:
        usage = shutil.disk_usage("/")
        pct = int((usage.used * 100) / usage.total)
        return f"{pct}%"
    except Exception:
        return "n/a"


def get_ip_address() -> str:
    ip_output = run_command(["hostname", "-I"])
    if ip_output:
        return ip_output.split()[0]
    return "n/a"


def get_supply_voltage() -> str:
    if not command_exists("vcgencmd"):
        return "n/a"
    output = run_command(["vcgencmd", "pmic_read_adc", "EXT5V_V"])
    if not output:
        return "n/a"
    return output.replace("EXT5V_V=", "").strip()


def get_optional_battery() -> str:
    for candidate in (
        "/run/piclaw/battery_percent",
        "/run/waveshare-ups/battery_percent",
    ):
        if not os.path.exists(candidate):
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as handle:
                raw = handle.read().strip()
            if raw:
                return raw
        except Exception:
            continue
    return "n/a"


def xor_checksum(data: bytes) -> int:
    checksum = 0
    for value in data:
        checksum ^= value
    return checksum


def short_be(value: int) -> bytes:
    return int(value).to_bytes(2, byteorder="big", signed=False)


def build_frame(command: int, payload: bytes = b"") -> bytes:
    length = 1 + 2 + 1 + len(payload) + len(FRAME_END) + 1
    body = (
        bytes([FRAME_HEADER])
        + short_be(length)
        + bytes([command])
        + payload
        + FRAME_END
    )
    return body + bytes([xor_checksum(body)])


class EpaperController:
    def __init__(
        self, serial_path: str, baud_rate: int, wake_pin: int, reset_pin: int
    ) -> None:
        self.serial_path = serial_path
        self.wake_pin = wake_pin
        self.reset_pin = reset_pin
        self.serial: Any = serial.Serial(
            port=serial_path,
            baudrate=baud_rate,
            timeout=1.0,
            write_timeout=1.0,
        )

    def close(self) -> None:
        try:
            self.serial.close()
        except Exception:
            pass

    def send(self, command: int, payload: bytes = b"") -> bytes:
        frame = build_frame(command, payload)
        self.serial.write(frame)
        self.serial.flush()
        time.sleep(0.06)
        return bytes(self.serial.read(256))

    def handshake(self) -> None:
        self.send(CMD_HANDSHAKE)

    def wake(self) -> None:
        gpio_set(self.reset_pin, "dh")
        gpio_set(self.wake_pin, "dl")
        time.sleep(0.05)
        gpio_set(self.wake_pin, "dh")
        time.sleep(0.08)
        gpio_set(self.wake_pin, "dl")
        time.sleep(0.20)

    def sleep(self) -> None:
        self.send(CMD_SLEEP)

    def clear(self) -> None:
        self.send(CMD_CLEAR)

    def refresh(self) -> None:
        self.send(CMD_REFRESH)

    def draw_text(self, x: int, y: int, text: str) -> None:
        encoded = text.encode("gbk", errors="replace") + b"\x00"
        payload = short_be(x) + short_be(y) + encoded
        self.send(CMD_DRAW_TEXT, payload)


def build_status_lines() -> List[str]:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    hostname = run_command(["hostname"]) or "pi"
    uptime = get_uptime()
    temp = get_cpu_temp()
    load = get_load()
    memory = get_mem_usage()
    disk = get_disk_usage()
    ip_addr = get_ip_address()
    battery = get_optional_battery()
    ext5v = get_supply_voltage()

    return [
        f"PiClaw Status   {now}",
        f"Host: {hostname}",
        f"Uptime: {uptime}    Load: {load}",
        f"Temp: {temp}      Mem: {memory}",
        f"Disk: {disk}      IP: {ip_addr}",
        f"Battery: {battery}   5V: {ext5v}",
        "Mode: wake -> draw -> refresh -> sleep",
    ]


def run_loop() -> int:
    serial_device = pick_serial_device(env_str("EPAPER_SERIAL_DEVICE", "auto"))
    baud_rate = env_int("EPAPER_BAUD_RATE", 115200)
    refresh_seconds = max(60, env_int("EPAPER_REFRESH_SECONDS", 300))
    wake_pin = env_int("EPAPER_WAKE_GPIO", 26)
    reset_pin = env_int("EPAPER_RESET_GPIO", 27)

    if not os.path.exists(serial_device):
        print(f"Serial device not found: {serial_device}", file=sys.stderr)

    controller = EpaperController(
        serial_path=serial_device,
        baud_rate=baud_rate,
        wake_pin=wake_pin,
        reset_pin=reset_pin,
    )

    try:
        while True:
            try:
                controller.wake()
                controller.handshake()
                controller.clear()

                y = 14
                for line in build_status_lines():
                    controller.draw_text(10, y, line)
                    y += 36

                controller.refresh()
                controller.sleep()
            except Exception as exc:
                print(f"Display update error: {exc}", file=sys.stderr)

            time.sleep(refresh_seconds)
    finally:
        controller.close()


def main() -> int:
    try:
        return run_loop()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
