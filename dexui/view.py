from __future__ import annotations

import discord
from discord import ui 
from discord.ext import commands
from typing import Optional, Union


__all__ = (
    "View",
    "ExitableView",
    "CancellableView"
)


def _can_be_disabled(item):
    return hasattr(item, "disabled")


class View(ui.View):
    def __init__(self, **kwargs):
        super().__init__(timeout=kwargs.pop("timeout", 120))
        
        self.client = None
        self.author: Optional[discord.Member] = None
        self.msg: Optional[Union[discord.Message, discord.InteractionMessage]] = None
        self.embed: Optional[discord.Embed] = None
        self.user_check = kwargs.pop("user_check", False)
        
        self._disabled = False
        self.kwargs = kwargs
        
    async def init(self, **kwargs): 
        pass 
        
    async def get_data(self):
        return 
        
    async def get_content(self, *args) -> Optional[str]:
        return 
        
    async def get_embed(self, *args) -> Optional[discord.Embed]:
        return 
        
    async def update_components(self, *args):
        pass 
    
    def _get_client(self, origin: Union[commands.Context, discord.abc.Messageable, discord.Interaction]) -> Union[discord.Client, commands.Bot]:
        if isinstance(origin, discord.Interaction):
            return origin.client    
        elif isinstance(origin, commands.Context):
            return origin.bot
        else:
            return origin._state._get_client()

    def _get_author(self, origin: Union[commands.Context, discord.Interaction]) -> Union[discord.User, discord.Member]:
        if isinstance(origin, discord.Interaction):
            return origin.user
        elif isinstance(origin, commands.Context):
            return origin.author
    
    async def _send(self, origin: Union[discord.abc.Messageable, discord.Interaction], **kwargs) -> Union[discord.Message, discord.InteractionMessage]:
        if isinstance(origin, discord.Interaction):
            await origin.response.send_message(**kwargs)
            return await origin.original_response()
        
        return await origin.send(**kwargs)
        
    async def process_data(self) -> dict:
        data = await discord.utils.maybe_coroutine(self.get_data)
        if not isinstance(data, tuple):
            data = (data,) if data is not None else tuple()

        content = await discord.utils.maybe_coroutine(self.get_content, *data)
        self.embed = await discord.utils.maybe_coroutine(self.get_embed, *data)
        await discord.utils.maybe_coroutine(self.update_components, *data)
         
        return {
            "content": content, 
            "embed": self.embed, 
            "view": self
        }
    
    async def start(self, origin: Union[discord.abc.Messageable, discord.Interaction], **kwargs):
        self.client = self._get_client(origin)
        self.author = self._get_author(origin)
        
        await self.init(**self.kwargs)
        data = await self.process_data()
        kwargs = {**kwargs, **data} 
        
        self.msg = await self._send(origin, **kwargs)
    
    async def update(self) -> Union[discord.Message, discord.InteractionMessage]:
        kwargs = await self.process_data()
        
        if self.msg is None:
            raise RuntimeError("can't update view without start")

        return await self.msg.edit(**kwargs)
    
    def _disable_children(self):
        for item in self.children:
            if _can_be_disabled(item):
                item.disabled = True
        
    async def disable(self) -> Union[discord.Message, discord.InteractionMessage]:
        if self._disabled:
            return
        
        self.stop()
        self._disabled = True
        self._disable_children()
        
        if self.msg is None:
            raise RuntimeError("can't disable view without start")

        return await self.msg.edit(view=self)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_check:
            check = interaction.user == self.author
            if not check:
                await interaction.response.send_message("Sorry, this is not for you.", ephemeral=True) 

            return check
        
        return True
    
    async def on_timeout(self) -> None:
        await self.disable()
        
        
class _StopButton(ui.Button):
    view: View
    
    async def callback(self, interaction):
        view = self.view
        if view is None:
            raise RuntimeError("Missing view to disable.")

        view.stop()
        view._disable_children()

        if view.msg is not None:
            await interaction.response.edit_message(view=view)
        

class ExitableView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_item(_StopButton(label="Exit", style=discord.ButtonStyle.red))


class CancellableView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_item(_StopButton(label="Cancel", style=discord.ButtonStyle.red))
