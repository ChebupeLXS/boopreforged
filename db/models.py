from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from tortoise.models import Model
from tortoise.fields import (
    BigIntField,
    IntField,
    ForeignKeyField,
    DatetimeField,
    ForeignKeyRelation,
    ReverseRelation,
    BooleanField
)
import disnake
if TYPE_CHECKING:
    from cogs.score import ScoreRow

class Member(Model):
    id = BigIntField(pk=True)

    scores: ReverseRelation['Score']

    @classmethod
    def from_member(cls, member: disnake.Member):
        return cls.get_or_create({'id': member.id}, id=member.id)

class Score(Model):
    member: ForeignKeyRelation[Member] = ForeignKeyField(
        'models.Member', 'scores'
    )
    score: IntField()
    started_at: DatetimeField()
    ended_at: DatetimeField(auto_now_add=True)
    dumped: BooleanField(default=False)

    @classmethod
    def from_member(cls, member: disnake.Member):
        return cls.all().filter(member__id=member.id)
    
    @classmethod
    async def paste_row(cls, row: ScoreRow):
        count = row.count()
        if count is None or count <= 0:
            return
        return await cls.create(
            member=await Member.from_member(row.member),
            score=count,
            started_at=row.started_at,
            ended_at=row.ended_at
        )