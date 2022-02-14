import asyncio
import os

from disnake.ext import commands
import disnake
from tortoise.expressions import Q

from db.models import Valentines as ValentinesModel
from .utils.paginator import PaginatorView, BaseListSource


class ValentineSource(BaseListSource):
    COLOR = 0xEF66B8
    def __init__(self, author_id: int, entries: list[ValentinesModel]):
        super().__init__(entries, per_page=6)
        self.author_id = author_id

    async def format_page(self, menu: PaginatorView, page: list[ValentinesModel]):
        e = self.base_embed(menu, page)
        for row in page:
            name = f'{"анонимная " if row.anonymously else ""}валентинка'.capitalize()
            text = f'ID:`{row.id}`\n'
            if self.author_id == row.sender:
                text += f'От: Вас\nКому: <@{row.receiver}>'
            else:
                text += f'От: {f"<@{row.sender}>" if not row.anonymously else "анонима"}\nКому: Вам'
            text += f'\nОтправлена {disnake.utils.format_dt(row.created_at, "R")}'
            e.add_field(name=name, value=text)
        return e

class Valentines(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def valentine(*_):
        pass

    @valentine.sub_command()
    async def send(
        self,
        inter: disnake.CommandInteraction,
        receiver: disnake.Member,
        anonymously: bool = True,
    ):
        """Отправить валентинку
        
        Parameters
        ----------
        receiver: Получатель валентинки
        anonymously: Отправить анонимно или нет?
        """
        if receiver == inter.author:
            return await inter.response.send_message('Вы не можете отправить себе валентинку.', ephemeral=True)
        if receiver.bot:
            return await inter.response.send_message('Вы не можете отправить валентинку боту.', ephemeral=True)
        if not inter.guild:
            return await inter.response.send_message('Эта команда работает только на сервере.', ephemeral=True)

        custom_id = os.urandom(16).hex()
        title = f'{"анонимная " if anonymously else ""}валентинка для '.capitalize() + receiver.display_name

        await inter.response.send_modal(
            title=title,
            custom_id=custom_id,
            components=[
                disnake.ui.TextInput(
                    label='Текст валентинки', custom_id='text',
                    style=disnake.TextInputStyle.paragraph,
                    placeholder=f'Дорогой(ая) {receiver.display_name}...',
                ),
            ],
        )
        def check(i: disnake.ModalInteraction):
            return i.author == inter.author and i.custom_id == custom_id
        modal_inter: disnake.ModalInteraction = await self.bot.wait_for('modal_submit', check=check)
        await modal_inter.response.send_message(
            f'{title} была отправлена. '\
                'Посмотреть список отправленных-полученных валентинок: `/valentine list`',
            ephemeral=True
        )
        row = await ValentinesModel.create(sender=inter.author.id, receiver=receiver.id, anonymously=anonymously, text=modal_inter.text_values['text'])
        try:
            await receiver.send(f'На ваш телефон пришло новое сообщение! Проверь, вдруг там что-то важное!'\
                f' (`/valentine view id:{row.id}`, команду вводить на сервере, не покажется остальным в чате)')
        except disnake.HTTPException:
            pass

    @valentine.sub_command()
    async def list(
        self,
        inter: disnake.CommandInteraction,
        type: str = commands.param('all', choices={'Все (по умолчанию)': 'all', 'Только полученные': 'receiver', 'Только отправленные': 'sender'})
    ):
        """Список полученных и отправленных валентинок
        
        Parameters
        ----------
        type: Какие валентинки показать?
        """
        if type == 'all':
            q = Q(**dict.fromkeys(('receiver', 'sender'), inter.author.id), join_type='OR')
        else:
            q = Q(**{type: inter.author.id})
        
        rows = await ValentinesModel.filter(q).order_by('-created_at')
        if not len(rows):
            return await inter.send('У вас нет валентинок.', ephemeral=True)
        view = PaginatorView(ValentineSource(inter.author.id, rows), interaction=inter)
        await view.start(ephemeral=True)

    @valentine.sub_command()
    async def view(
        self,
        inter: disnake.CommandInteraction,
        id: int,
    ):
        """Посмотреть текст валентинки
        
        Parameters
        ----------
        id: ID валентинки
        """
        row = await ValentinesModel.filter(id=id).first()
        if row is None:
            return await inter.response.send_message('Валентинки с таким ID не существует.')

        if inter.author.id not in (row.sender, row.receiver) and inter.author.id != self.bot.owner_id:
            return await inter.response.send_message('Вы не можете прочитать эту валентинку.')
        
        e = disnake.Embed(description=row.text)
        if row.anonymously and row.sender != inter.author.id:
            e.add_field(name='Отправитель', value='Аноним')
        else:
            e.add_field(name='Отправитель', value=f'<@{row.sender}>')
        e.add_field(name='Получатель', value=f'<@{row.receiver}>{" (анонимно)" if row.anonymously and row.sender == inter.author.id else ""}')
        await inter.response.send_message(embed=e, ephemeral=True)
    
    @commands.command(name='valentine send')
    @commands.dm_only()
    async def text_send(self, ctx: commands.Context, receiver: disnake.Member):
        m = await ctx.send('Отправить анонимно?')
        def check(r: disnake.Reaction, u: disnake.User):
            return r.message == m and not u.bot and str(r.emoji) in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}')
        await m.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await m.add_reaction('\N{CROSS MARK}')
        try:
            _: tuple[disnake.Reaction, disnake.User] = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            r, u = _
        except asyncio.TimeoutError:
            await m.edit(content='Слишком долго')
            await m.clear_reactions()
            return
        if str(r.emoji) == '\N{WHITE HEAVY CHECK MARK}':
            anonymously = True
        else:
            anonymously = False

        m = await m.reply('У вас есть 5 минут, чтобы написать текст валентинки. Чтобы отменить, отправьте `-`.')

        def check(m: disnake.Message):
            return ctx.channel == m.channel and ctx.author == m.activity
        try:
            m2: disnake.Message = await self.bot.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await m.edit(content='Вы не успели.')
            return
        if m2.content == '-':
            return await m2.reply('Отмена.')
        e = disnake.Embed(description=m2.content)
        e.add_field(name='Отправитель', value='Аноним' if anonymously else ctx.author.mention)

        m3 = await m2.reply('Вот так будет выглядеть валентинка.. Отправлять?', embed=e)
        await m3.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await m3.add_reaction('\N{CROSS MARK}')
        try:
            _: tuple[disnake.Reaction, disnake.User] = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            r, u = _
        except asyncio.TimeoutError:
            await m.edit(content='Слишком долго')
            await m.clear_reactions()
            return
        if str(r.emoji) == '\N{CROSS MARK}':
            await m3.reply('Валентинка сгорела в пламени камина..')
            return
        await m3.reply(
            'Валентинка была отправлена. '\
                'Посмотреть список отправленных-полученных валентинок: `/valentine list`',
        )
        row = await ValentinesModel.create(sender=ctx.author.id, receiver=receiver.id, anonymously=anonymously, text=m3.content)
        try:
            await receiver.send(f'На ваш телефон пришло новое сообщение! Проверь, вдруг там что-то важное!'\
                f' (`/valentine view id:{row.id}`, команду вводить на сервере, не покажется остальным в чате)')
        except disnake.HTTPException:
            pass

    @text_send.error
    async def text_send_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('только в лс ок?')

def setup(bot):
    bot.add_cog(Valentines(bot))