# Get and set config info.
import sqlalchemy

from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import select
from src.logging import logger


Base = declarative_base()

class ConfigEntry(Base):
    __tablename__ = "config_entry"
    # A guild ID of -1 means "whole server config" because doing the sensible
    # thing and using NULL for that won't work with primary keys.
    guild_id = Column(Integer, primary_key = True)
    setting = Column(String(30), primary_key = True)
    value = Column(String(30))

    def __repr__(self):
        return f"<ConfigEntry(guild_id={self.guild_id}, setting={self.setting}, value={self.value})>"

class Config:
    """
       The config class gives access to configuration information for the
       bot. Both bot-wide and per-guild config data can be stored and
       recalled.
    """
    def __init__(self, bot):
        self.bot = bot
        # This can go once the code's running everywhere so the DB is up to
        # date everywhere.
        self.init_tables(bot)
        
    def init_tables(self, bot):
        db = bot.database
        tables = bot.database.meta_data.tables
        if tables.get("config_entry") is not None:
            return

        db.config_entry = Table("config_entry", db.meta_data,
                                Column("guild_id", Integer, primary_key=True),
                                Column("setting", String(30), primary_key=True),
                                Column("value", String(30)))
        db.safe_start()
        
    def get(self, guild_id, setting, default=None):
        """
            Get a config value. If it doesn't exist then create it for later
            use and return the passed-in default.

            Note that the boolean value False is saved in the DB as "0" which
            is actually true for... reasons. Which are stupid.

            Use a guild ID of None (or -1) for settings not attached to a
            particular guild.
        """
        if guild_id is None:
            guild_id = -1
        setting = setting.lower()
        
        with Session(self.bot.engine) as session:
            c = None
            s = select(ConfigEntry).where(ConfigEntry.guild_id == guild_id,
                                          ConfigEntry.setting == setting)
            rows = session.execute(s)
            for r in rows.unique():
                return r[0].value

            # If we're here then we didn't find a row, so create a new entry.
            c = ConfigEntry(guild_id=guild_id, setting=setting, value=default)
            session.add(c)
            session.commit()

        # Didn't find anything so return the default.
        return default
        

    def set(self, guild_id, setting, value):
        """
            Set a config value. Note that, sadly, real booleans are weird
            and kind of stupid -- if you want to set a value to false then
            you should pass in the empty string not a False. (which is actually
            turned into the string "0" which is... true)

            Use a guild ID of None (or -1) for settings not attached to a
            particular guild.
        """
        if guild_id is None:
            guild_id = -1
        setting = setting.lower()
        with Session(self.bot.engine) as session:
            c = None
            s = select(ConfigEntry).where(ConfigEntry.guild_id == guild_id,
                                          ConfigEntry.setting == setting)
            rows = session.execute(s)
            for r in rows.unique():
                c = r[0]
                break
            if c is None:
                c = ConfigEntry(guild_id = guild_id, setting = setting)

            c.value = value
            session.add(c)
            session.commit()
