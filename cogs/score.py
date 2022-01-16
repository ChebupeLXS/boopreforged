from __future__ import annotations
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from disnake.ext import commands
import disnake
from disnake.utils import utcnow

from db.models import Score as ScoreModel
from utils.text import plural, random_chr

if TYPE_CHECKING:
    from bot import Bot

@dataclass
class ScoreRow:
    if TYPE_CHECKING:
        cog: Score
    member: disnake.Member
    started_at: datetime
    task: asyncio.Task = None
    ended_at: datetime = None

    def count(self) -> Optional[int]:
        if self.ended_at is None:
            return 0
        
        return round((self.ended_at - self.started_at).total_seconds() / 60)
    
    async def _task(self, *, crush=False):
        print(f'for {self.member}, started task with {crush=}')
        if not crush:
            await asyncio.sleep(60)

            if len(self.cog.row_mapping) <= 2:
                for row in self.cog.row_mapping.values():
                    if row == self:
                        continue
                    row.task.cancel()
                    await row._task(crush=True)
                    print(f'from {self.member}, crushed: {row.member}')
        
        self.cog.row_mapping.pop(self.member.id)
        self.ended_at = utcnow() 
        if not crush:
            self.ended_at -= timedelta(seconds=60)
        await ScoreModel.paste_row(self)
        print(f'for {self.member}, pasted score: {self.count()}')
        
    def __eq__(self, __o: object) -> bool:
        return self.member.id == __o.member.id

class ScoreView(disnake.ui.View):
    def __init__(self, inter: disnake.CommandInteraction, *, member: disnake.Member, rows: list[ScoreModel]):
        super().__init__(timeout=180)
        self.init_inter = inter
        self.member = member

        self.rows = rows
        now = inter.created_at - timedelta(1)
        self.day_rows = list(filter(lambda x: x.created_at >= now, rows))

    def embed(self):
        e = disnake.Embed(
            color=0x2f3136,
        ).set_author(
            name=self.member.display_name,
            icon_url=self.member.display_avatar
        ).add_field(
            'Уровень', f'```diff\n- x-й уровень\n```'
        ).add_field(
            'Все очки', f'```fix\n# {plural("очко"):{sum([r.score for r in self.rows])}}\n```'
        ).add_field(
            'До следующего уровня', f'```diff\n+ {plural("очко"):0}\n```'
        )
        if self.day_rows:
            e.add_field(
                'За последние сутки', f'```md\n# {plural("очко"):{sum([r.score for r in self.day_rows])}}',
                inline=False
            )
        e.add_field(
            'Прогресс', f'```\n{random_chr(0x2580, 0x259F):25}| ?lvl (?%)\n```', inline=False
        )
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author == self.init_inter.author:
            return True
        await interaction.response.send_message('тебе нельзя', ephemeral=True)
    
    @disnake.ui.button(label='Index')
    async def index_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        for b in self.children:
            b.disabled = False
        button.disabled = True
        await inter.response.send_message('soon (tm)', ephemeral=True, view=self)

    @disnake.ui.button(label='Mouth')
    async def m_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        for b in self.children:
            b.disabled = False
        button.disabled = True
        await inter.response.send_message('soon (tm)', ephemeral=True, view=self)

    @disnake.ui.button(label='All')
    async def t_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        for b in self.children:
            b.disabled = False
        button.disabled = True
        await inter.response.send_message('soon (tm)', ephemeral=True, view=self)


class Score(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.row_mapping: dict[int, ScoreRow] = {}
        ScoreRow.cog = self

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel.id not in (824997091725017090, 864140290796945418):
            return

        if message.author.id not in self.row_mapping:
            print(f'for {message.author}, new entry: {message.channel.id}-{message.id}')
            row = ScoreRow(message.author, utcnow())
            row.task = self.bot.loop.create_task(row._task())
            self.row_mapping[message.author.id] = row
            return
        
        print(f'for {message.author}, update: {message.channel.id}-{message.id}')
        row = self.row_mapping[message.author.id]
        if not row.task.done():
            row.task.cancel()
            row.task = self.bot.loop.create_task(row._task())
    
    @commands.slash_command()
    async def score(*_):
        pass

    @score.sub_command()
    async def view(self, inter: disnake.CommandInteraction, member: disnake.Member = commands.param(lambda i: i.author)):
        rows = await ScoreModel.from_member(member)
        view = ScoreView(inter, member=member, rows=rows)
        await inter.response.send_message(embed=view.embed(), view=view)


def setup(bot):
    bot.add_cog(Score(bot))
