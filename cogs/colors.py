from __future__ import annotations
from typing import TYPE_CHECKING

from disnake.ext import commands
import disnake

if TYPE_CHECKING:
    from bot import Bot

# fmt: off
COLORS = (
    (833053374600577026, "Кальмар", "\N{SQUID}"),
    (833053402405142538, "Коралловый", "\N{PURSE}"),
    (833053432234901505, "Красный фонарь", "\N{IZAKAYA LANTERN}"),
    (833235083355095082, "Бежевый", "\N{OK HAND SIGN}\N{EMOJI MODIFIER FITZPATRICK TYPE-1-2}",),
    (833053576745451613, "Закат", "\N{CITYSCAPE AT DUSK}"),
    (833053452405571604, "Золотой", "\N{LEDGER}"),
    (833053536245383238, "Я – банан", "\N{BANANA}"),
    (833053525432860692, "Листопад", "\N{LEAF FLUTTERING IN WIND}"),
    (833053547142709319, "Черепаха Наталия", "\N{TURTLE}"),
    (833053557347450901, "Изумрудный", "\N{GREEN BOOK}"),
    (833232827134246952, "Windows 98", "\N{TEST TUBE}"),
    (833231105385562142, "Пантсу", "\N{BRIEFS}"),
    (833053748380827649, "Морская волна", "\N{WATER WAVE}"),
    (833053502833950730, "Синий глаз", "\N{NAZAR AMULET}"),
    (833053757498982500, "Я знаю, что вы делали этим летом", "\N{CRYSTAL BALL}"),
    (833238131964379166, "Баклажан", "\N{AUBERGINE}"),
    (833053319218855966, "Гибискус", "\N{HIBISCUS}"),
    (833065024091848724, "Добрый ёжик", "\N{HEDGEHOG}"),
    (833053569304494136, "Легендарная пыль", "\N{OPTICAL DISC}"),
    (833053487033090058, "Тень", "\N{BLACK CHESS PAWN}\N{VARIATION SELECTOR-16}"),
)
COLORS_SNOWFLAKE_SET = set(t[0] for t in COLORS)
# fmt: on

class GuildMessageInteraction(disnake.MessageInteraction):
    guild: disnake.Guild
    author: disnake.Member

class ColorButton(disnake.ui.Button["ColorView"]):
    custom_id: str

    def __init__(self, color):
        super().__init__(custom_id=str(color[0]), emoji=color[2])

    async def callback(self, interaction: GuildMessageInteraction):
        await interaction.response.defer()
        if int(self.custom_id) in interaction.author._roles:
            await interaction.author.remove_roles(disnake.Object(self.custom_id))
            return

        to_remove = COLORS_SNOWFLAKE_SET.intersection(interaction.author._roles)
        await interaction.author.add_roles(disnake.Object(self.custom_id))
        if to_remove:
            await interaction.author.remove_roles(*(disnake.Object(role_id) for role_id in to_remove))

class ColorView(disnake.ui.View):
    def __init__(self, *, bot: Bot = None):
        super().__init__(timeout=None)
        for color in COLORS:
            self.add_item(ColorButton(color))

        if bot is None:
            self.stop()
            return
        self.bot = bot


class ColorChanger(commands.Cog, name="Цвета"):  # type: ignore
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self):
        await self.bot.wait_until_ready()

        self.view = ColorView(bot=self.bot)
        self.bot.add_view(self.view)

    def cog_unload(self) -> None:
        self.view.stop()


def setup(bot):
    bot.add_cog(ColorChanger(bot))
