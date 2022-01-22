from __future__ import annotations
import asyncio
from math import log
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from disnake.ext import commands
import disnake
from disnake.utils import utcnow

from db.models import Score as ScoreModel, Member as MemberModel
from .utils.text import plural, bar  # type: ignore

if TYPE_CHECKING:
    from bot import Bot

B1 = 10
Q = 2

def _count_level(points: int) -> float:
    if points < B1:
        return .0
    if points == B1:
        return 1.0
    res = log(points / B1) / log(Q)
    return res + 1

def _count_score(level: int) -> int:
    if level <= 0:
        return 0
    return B1 * Q**(level-1)

@dataclass
class ScoreRow:
    if TYPE_CHECKING:
        cog: Score
    member: disnake.Member
    started_at: datetime
    task: asyncio.Task = None  # type: ignore
    ended_at: Optional[datetime] = None

    @property
    def count(self) -> int:
        if self.ended_at is None:
            return 0

        return max(round((self.ended_at - self.started_at).total_seconds() / 60), 0)

    async def finalize(self):
        self.cog.row_mapping.pop(self.member.id)
        if len(self.cog.row_mapping) > 0:
            await ScoreModel.create(
                member=(await MemberModel.get_or_create(id=self.member.id))[0],
                score=self.count,
                started_at=self.started_at,
                ended_at=self.ended_at,
            )

    async def _task(self):
        await asyncio.sleep(60)

        if len(self.cog.row_mapping) <= 2:
            rows = list(self.cog.row_mapping.values())
            started_at = max([r.started_at for r in rows])
            for row in rows:
                row.started_at = started_at
                row.ended_at = utcnow()
                if row.member.id != self.member.id:
                    row.task.cancel()
                await row.finalize()
                return

        self.ended_at = utcnow() - timedelta(seconds=60)
        await self.finalize()


class ScoreView(disnake.ui.View):
    def __init__(
        self,
        inter: disnake.CommandInteraction,
        *,
        member: disnake.Member,
        rows: list[ScoreModel],
    ):
        super().__init__(timeout=180)
        self.init_inter = inter
        self.member = member

        self.rows = rows
        now = inter.created_at - timedelta(1)
        self.day_rows = list(filter(lambda x: x.started_at >= now, rows))

    def embed(self):
        score = sum([r.score for r in self.rows])
        level = int(_count_level(score))
        previous_frontier = _count_score(level)
        next_frontier = _count_score(level+1)
        percent = (score - previous_frontier) / (next_frontier - previous_frontier)
        fill_length = int(percent * 25)
        bar = '█' * fill_length + '\u2003' * (25 - fill_length)

        e = (
            disnake.Embed(
                color=0x2F3136,
            )
            .set_author(
                name=self.member.display_name,
                icon_url=self.member.display_avatar
            )
            .add_field(
                "Уровень", f"```diff\n- {int(level)}-й уровень\n```"
            )
            .add_field(
                "Все очки", f'```fix\n# {plural("очко"):{score}}\n```',
            )
            .add_field(
                "До следующего уровня", f'```diff\n+ {plural("очко"):{next_frontier-score}}\n```'
            )
        )
        if self.day_rows:
            e.add_field(
                "За последние сутки",
                f"```md\n# {plural('очко'):{sum([r.score for r in self.day_rows])}}\n```",
                inline=False,
            )
        e.add_field(
            "Прогресс",
            f"```\n{bar}| {level+1}lvl ({round(percent*100)}%)\n```",
            inline=False,
        )
        return e

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author == self.init_inter.author:
            return True
        await interaction.response.send_message("это не для тебя", ephemeral=True)
        return False

    @disnake.ui.button(label="Index")
    async def index_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        for b in self.children:
            if isinstance(b, disnake.ui.Button):
                b.disabled = False
        button.disabled = True
        await inter.response.send_message("soon (tm)", ephemeral=True, view=self)

    @disnake.ui.button(label="Mouth")
    async def m_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        for b in self.children:
            if isinstance(b, disnake.ui.Button):
                b.disabled = False
        button.disabled = True
        await inter.response.send_message("soon (tm)", ephemeral=True, view=self)

    @disnake.ui.button(label="All")
    async def t_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        for b in self.children:
            if isinstance(b, disnake.ui.Button):
                b.disabled = False
        button.disabled = True
        await inter.response.send_message("soon (tm)", ephemeral=True, view=self)


class Score(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.row_mapping: dict[int, ScoreRow] = {}
        ScoreRow.cog = self

    def cog_unload(self) -> None:
        for row in self.row_mapping.values():
            row.task.cancel()
            row.ended_at = utcnow()
            self.bot.loop.create_task(row.finalize())

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel.id not in (824997091725017090, 864140290796945418):
            return
        if message.author.bot:
            return
        if not isinstance(message.author, disnake.Member):
            return

        if message.author.id not in self.row_mapping:
            row = ScoreRow(message.author, utcnow())
            row.task = self.bot.loop.create_task(row._task())
            self.row_mapping[message.author.id] = row
            return

        row = self.row_mapping[message.author.id]
        if not row.task.done():
            row.task.cancel()
            row.task = self.bot.loop.create_task(row._task())

    @commands.slash_command()
    async def score(*_):
        pass

    @score.sub_command()
    async def view(
        self,
        inter: disnake.CommandInteraction,
        member: disnake.Member = commands.param(lambda i: i.author),
    ):
        rows = await ScoreModel.filter(member__id=member.id)
        view = ScoreView(inter, member=member, rows=rows)
        await inter.response.send_message(embed=view.embed(), view=view)


def setup(bot):
    bot.add_cog(Score(bot))
