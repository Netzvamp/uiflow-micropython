# SPDX-FileCopyrightText: 2024 M5Stack Technology CO LTD
#
# SPDX-License-Identifier: MIT

from . import app_base
import M5
import gc
import asyncio
import hardware
import machine
from unit import CardKBUnit, KeyCode


class KeyEvent:
    key = 0
    status = False


class Framework:
    def __init__(self) -> None:
        self._apps = []
        self._app_selector = app_base.AppSelector(self._apps)
        self._launcher = None
        self._bar = None
        self._sidebar = None

    def install_bar(self, bar: app_base.AppBase):
        self._bar = bar

    def install_sidebar(self, bar: app_base.AppBase):
        self._sidebar = bar

    def install_launcher(self, launcher: app_base.AppBase):
        self._launcher = launcher

    def install(self, app: app_base.AppBase):
        app.install()
        self._apps.append(app)

    def start(self):
        # asyncio.create_task(self.gc_task())
        asyncio.run(self.run())

    async def unload(self, app: app_base.AppBase):
        # app = self._apps.pop()
        app.stop()

    async def load(self, app: app_base.AppBase):
        app.start()

    async def reload(self, app: app_base.AppBase):
        app.stop()
        app.start()

    async def run(self):
        rotary = hardware.Rotary()
        self._bar and self._bar.start()
        self._sidebar and self._sidebar.start()
        if self._launcher:
            self._app_selector.select(self._launcher)
            self._launcher.start()

        self.i2c0 = machine.I2C(0, scl=machine.Pin(15), sda=machine.Pin(13), freq=100000)
        self._kb_status = False
        if 0x5F in self.i2c0.scan():
            self._kb = CardKBUnit(self.i2c0)
            self._event = KeyEvent()
            self._kb_status = True

        while True:
            M5.update()

            if M5.BtnA.wasClicked():
                M5.Speaker.tone(4000, 50)
                app = self._app_selector.current()
                if hasattr(app, "_keycode_enter_event_handler"):
                    await app._keycode_enter_event_handler(self)
            elif M5.BtnA.wasHold():
                M5.Speaker.tone(3500, 50)
                app = self._app_selector.current()
                if hasattr(app, "_keycode_back_event_handler"):
                    await app._keycode_back_event_handler(self)
                app.stop()
                self._app_selector.select(self._launcher)
                self._launcher.start()
            elif M5.BtnA.wasDoubleClicked():
                M5.Speaker.tone(4500, 50)
                app = self._app_selector.current()
                if hasattr(app, "_keycode_ctrl_event_handler"):
                    await app._keycode_ctrl_event_handler(self)

            if rotary.get_rotary_status():
                direction = rotary.get_rotary_increments()
                if direction < 0:
                    M5.Speaker.tone(3500, 50)
                    app = self._app_selector.current()
                    if hasattr(app, "_keycode_dpad_down_event_handler"):
                        await app._keycode_dpad_down_event_handler(self)
                elif direction > 0:
                    M5.Speaker.tone(3500, 50)
                    app = self._app_selector.current()
                    if hasattr(app, "_keycode_dpad_up_event_handler"):
                        await app._keycode_dpad_up_event_handler(self)

            if self._kb_status:
                if self._kb.is_pressed():
                    M5.Speaker.tone(3500, 50)
                    self._event.key = self._kb.get_key()
                    self._event.status = False
                    await self.handle_input(self._event)

            await asyncio.sleep_ms(10)

    async def handle_input(self, event: KeyEvent):
        if event.key is KeyCode.KEYCODE_RIGHT:
            M5.Speaker.tone(3500, 50)
            app = self._app_selector.current()
            if hasattr(app, "_keycode_dpad_up_event_handler"):
                await app._keycode_dpad_up_event_handler(self)
            event.status = True
        if KeyCode.KEYCODE_LEFT == event.key:
            app = self._app_selector.current()
            if hasattr(app, "_keycode_dpad_down_event_handler"):
                await app._keycode_dpad_down_event_handler(self)
            event.status = True
        if event.status is False:
            app = self._app_selector.current()
            if hasattr(app, "_kb_event_handler"):
                await app._kb_event_handler(event, self)

    async def gc_task(self):
        while True:
            gc.collect()
            print("heap RAM free:", gc.mem_free())
            print("heap RAM alloc:", gc.mem_alloc())
            await asyncio.sleep_ms(5000)
