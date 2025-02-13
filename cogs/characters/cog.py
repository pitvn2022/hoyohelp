import asyncio
import io
import typing

import discord
import genshin
from discord import app_commands
from discord.ext import commands
from genshinpyrail.genshinpyrail import genshin_character_list, honkai_character_list
from genshinpyrail.src.tools.model import GenshinCharterList, StarRaillCharterList

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import SlashCommandLogger

from .ui import DropdownView


class CharactersCog(commands.Cog, name="character"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="character_overview", description="Publicly display all of my characters")
    @app_commands.rename(game="game", sort_key="sort", user="user")
    @app_commands.describe(game="Select a game", user="Query data of other members, leave blank to query your own")
    @app_commands.choices(
        game=[
            app_commands.Choice(name="Genshin Impact", value="genshin"),
            app_commands.Choice(name="Honkai: Star Rail", value="hkrpg"),
        ],
        sort_key=[
            app_commands.Choice(name="Level", value="LEVEL"),
            app_commands.Choice(name="Element", value="ELEMENT"),
            app_commands.Choice(name="Raity", value="RARITY"),
        ],
    )
    @SlashCommandLogger
    async def slash_characters(
        self,
        interaction: discord.Interaction,
        game: genshin.Game,
        sort_key: typing.Literal["LEVEL", "ELEMENT", "RARITY"] = "LEVEL",
        user: discord.User | discord.Member | None = None,
    ):
        user = user or interaction.user
        try:
            match game:
                case genshin.Game.GENSHIN:
                    defer, characters = await asyncio.gather(
                        interaction.response.defer(),
                        genshin_py.get_genshin_characters(user.id),
                    )
                case genshin.Game.STARRAIL:
                    defer, characters = await asyncio.gather(
                        interaction.response.defer(),
                        genshin_py.get_starrail_characters(user.id),
                    )
                case _:
                    return
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            return

        # 排序
        match sort_key:
            case "LEVEL":
                characters = sorted(characters, key=lambda x: (x.level, x.rarity, x.element), reverse=True)
            case "ELEMENT":
                characters = sorted(characters, key=lambda x: (x.element, x.rarity, x.level), reverse=True)
            case "RARITY":
                characters = sorted(characters, key=lambda x: (x.rarity, x.level, x.element), reverse=True)

        try:
            # 使用 genshinpyrail 產生圖片
            match game:
                case genshin.Game.GENSHIN:
                    data = await genshin_character_list.Creat(characters).start()
                    image = GenshinCharterList(**data).card
                case genshin.Game.STARRAIL:
                    data = await honkai_character_list.Creat(characters).start()
                    image = StarRaillCharterList(**data).card
            if image is None:
                raise ValueError("No image")
        except Exception:
            # 文字呈現
            view = DropdownView(user, characters)
            await interaction.edit_original_response(content="Please select a character：", view=view)
            return
        else:
            # 圖片呈現
            fp = io.BytesIO()
            image = image.convert("RGB")
            image.save(fp, "jpeg", optimize=True, quality=90)
            fp.seek(0)
            embed = EmbedTemplate.normal(f"{user.display_name} Character list")
            embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=embed, attachments=[discord.File(fp, "image.jpeg")]
            )


async def setup(client: commands.Bot):
    await client.add_cog(CharactersCog(client))
