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


class Score(Model):
    member: ForeignKeyRelation[Member] = ForeignKeyField(
        'models.Member', 'scores'
    )
    score: IntField()
    started_at: DatetimeField()
    ended_at: DatetimeField(auto_now_add=True)
    dumped: BooleanField(default=False)