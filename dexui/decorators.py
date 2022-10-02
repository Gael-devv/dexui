import discord
from discord import ui 
import functools


__all__ = (
    "change_color_when_used",
    "disable_after_pressed"
)


def change_color_when_used(func): 
    @functools.wraps(func)
    async def callback_wrapper(self, interaction: discord.Interaction, button: ui.Button):
        for item in self.children:
            if getattr(item, "__change_color__", None) is not None:
                item.style = discord.ButtonStyle.secondary
        
        button.style = discord.ButtonStyle.primary 
        
        try:
            await func(self, interaction, button) 
        finally:
            await self.msg.edit(view=self)

    class _ChangeColorButton(ui.Button):
        __change_color__ = True
    
    callback_wrapper.__discord_ui_model_type__ = _ChangeColorButton
    return callback_wrapper


def disable_after_pressed(func): 
    @functools.wraps(func)
    async def callback_wrapper(self, interaction: discord.Interaction, button: ui.Button):
        try:
            await func(self, interaction, button)
        finally:
            await self.disable()

    return callback_wrapper
