import asyncio
from typing import Dict, Optional, Any

import disnake
from disnake.ext import menus

class PaginatorView(disnake.ui.View):
    def __init__(
        self,
        source: menus.PageSource,
        *,
        interaction: disnake.Interaction,
        check_embeds: bool = True,
        compact: bool = False,
    ):
        super().__init__()
        self.source: menus.PageSource = source
        self.check_embeds: bool = check_embeds
        self.interaction: disnake.Interaction = interaction
        self.message: Optional[disnake.Message] = None
        self.current_page: int = 0
        self.compact: bool = compact
        self.input_lock = asyncio.Lock()
        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        if not self.compact:
            self.numbered_page.row = 1
            self.stop_pages.row = 1

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)  # type: ignore
            self.add_item(self.go_to_previous_page)  # type: ignore
            if not self.compact:
                self.add_item(self.go_to_current_page)  # type: ignore
            self.add_item(self.go_to_next_page)  # type: ignore
            if use_last_and_first:
                self.add_item(self.go_to_last_page)  # type: ignore
            if not self.compact:
                self.add_item(self.numbered_page)  # type: ignore
            self.add_item(self.stop_pages)  # type: ignore

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await disnake.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, disnake.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: disnake.Interaction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    def _update_labels(self, page_number: int) -> None:
        self.go_to_first_page.disabled = page_number == 0
        if self.compact:
            max_pages = self.source.get_max_pages()
            self.go_to_last_page.disabled = max_pages is None or (page_number + 1) >= max_pages
            self.go_to_next_page.disabled = max_pages is not None and (page_number + 1) >= max_pages
            self.go_to_previous_page.disabled = page_number == 0
            return

        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(self, interaction: disnake.Interaction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        if interaction.user and interaction.user in (self.interaction.bot.owner, self.interaction.author):
            return True
        await interaction.response.send_message('Вы не можете управлять этим.', ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    async def on_error(self, error: Exception, item: disnake.ui.Item, interaction: disnake.Interaction) -> None:
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message('An unknown error occurred, sorry', ephemeral=True)

    async def start(self, *, ephemeral=False) -> None:
        if self.check_embeds and not self.interaction.channel.permissions_for(self.interaction.me).embed_links:
            await self.interaction.response.send_message('Bot does not have embed links permission in this channel.', ephemeral=True)
            return

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        await self.interaction.response.send_message(**kwargs, view=self, ephemeral=ephemeral)
        self.message = await self.interaction.original_message()

    @disnake.ui.button(label='≪', style=disnake.ButtonStyle.grey)
    async def go_to_first_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        """go to the first page"""
        await self.show_page(interaction, 0)

    @disnake.ui.button(label='Назад', style=disnake.ButtonStyle.blurple)
    async def go_to_previous_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        """go to the previous page"""
        await self.show_checked_page(interaction, self.current_page - 1)

    @disnake.ui.button(label='Текущая', style=disnake.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        pass

    @disnake.ui.button(label='Следующая', style=disnake.ButtonStyle.blurple)
    async def go_to_next_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        """go to the next page"""
        await self.show_checked_page(interaction, self.current_page + 1)

    @disnake.ui.button(label='≫', style=disnake.ButtonStyle.grey)
    async def go_to_last_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(interaction, self.source.get_max_pages() - 1)


    @disnake.ui.button(label='На страницу...', style=disnake.ButtonStyle.grey)
    async def numbered_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        """lets you type a page number to go to"""
        if self.input_lock.locked():
            await interaction.response.send_message('Уже ожидаем ваш ответ...', ephemeral=True)
            return

        if self.message is None:
            return

        async with self.input_lock:
            await interaction.response.send_modal(
                title='На какую страницу вы хотите перейти?',
                custom_id=f'{self.interaction.author.id}-{interaction.id}',
                components=(
                    disnake.ui.TextInput(
                        label='Номер страницы', custom_id='page',
                        style=disnake.TextInputStyle.short,
                    )
                )
            )

            def message_check(m):
                return m.custom_id == f'{self.interaction.author.id}-{interaction.id}'

            try:
                modal_inter: disnake.ModalInteraction = await self.interaction.bot.wait_for('modal_submit', check=message_check, timeout=30.0)
            except asyncio.TimeoutError:
                pass

            if modal_inter and modal_inter.values['page'].isdigit():
                await self.show_checked_page(modal_inter, int(modal_inter.values['page']) - 1)
            else:
                await modal_inter.response.send_message('Это не число', ephemeral=True)

    @disnake.ui.button(label='Стоп', style=disnake.ButtonStyle.red)
    async def stop_pages(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        """stops the pagination session."""
        await interaction.response.edit_message(view=None)
        self.stop()

class BaseListSource(menus.ListPageSource):
    COLOR = 0x0084c7
    def base_embed(self, view: PaginatorView, entries) -> disnake.Embed:
        e = disnake.Embed(
            color=self.COLOR
        )
        if self.is_paginating():
            offset = view.current_page*self.per_page
            e.set_footer(
                text=(
                    f'Стр. {view.current_page+1}/{self.get_max_pages()} | '
                    f'Показано {offset+1}-{offset+len(entries)}/{len(self.entries)}'
                )
            )
        return e