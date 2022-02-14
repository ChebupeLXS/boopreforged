from typing import Mapping
import traceback

import disnake
from disnake.ext import commands, tasks

import db

initial_extensions = (
    "cogs.colors",
    "cogs.voice_rooms",
    "cogs.score",
    "cogs.valentines"
    "jishaku",
)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=";",
            description="смешной ботик теперь перекованный",
            test_guilds=[
                824997091075555419,
            ],  # 859290967475879966
            intents=disnake.Intents.all(),
            debug_events=True,
        )
        self.startup = disnake.utils.utcnow()
        self.defer_pool: Mapping[int, disnake.Interaction] = {}

        for ext in initial_extensions:
            try:
                self.load_extension(ext)
            except Exception as e:
                tb = "\n".join(traceback.format_exception(None, e, e.__traceback__))
                print(
                    f"Could not load extension {ext} due to {e.__class__.__name__}: {e}"
                )
                print(tb)

        self.db_refresh.loop = self.loop
        self.db_refresh.start()
    
    @tasks.loop(hours=2)
    async def db_refresh(self):
        await db.init(reconnect=True, regenerate=True)

    async def on_ready(self):
        print(f"Logged on as {self.user} (ID: {self.user.id})")
