from __future__ import annotations
from typing import TYPE_CHECKING

from disnake.ext import commands
import disnake

if TYPE_CHECKING:
    from bot import Bot

CATEGORY_ID = 836670303266144306
BASE_CHANNEL_ID = 930477492211437618


class VoiceRooms(commands.Cog, name="Войсчаты"):  # type: ignore
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ):
        if (
            before.channel
            and before.channel.category_id == CATEGORY_ID
            and before.channel.id != BASE_CHANNEL_ID
            and not len(before.channel.members)
        ):
            await before.channel.delete()
        if after.channel and after.channel.id == BASE_CHANNEL_ID:
            ch = await member.guild.create_voice_channel(
                member.display_name,
                category=disnake.Object(CATEGORY_ID),  # type: ignore
                overwrites={
                    member: disnake.PermissionOverwrite(
                        manage_channels=True, speak=True, connect=True
                    )
                },
            )
            await member.move_to(ch)


def setup(bot):
    bot.add_cog(VoiceRooms(bot))
