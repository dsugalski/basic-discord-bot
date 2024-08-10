import sqlalchemy

from datetime import datetime
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import Column, Integer, String, Table, DateTime
from sqlalchemy import select, func
from src.logging import logger

Base = declarative_base()

class StatEntry(Base):
    __tablename__ = "stats"
    guild_id = Column(Integer, primary_key = True)
    statname = Column(String(100), primary_key = True)
    substat = Column(String(100), primary_key = True)
    count = Column(Integer)
    last_update = Column(DateTime)

    def __repr__(self):
        return f"<StatEntry(guild_id={self.guild_id}, stat={self.statname}, substat={self.substat}, count={self.count}, last_update={self.last_update})>"

class StatsDay(Base):
    __tablename__ = "stats_granular"
    guild_id = Column(Integer, primary_key = True)
    statname = Column(String(100), primary_key = True)
    substat = Column(String(100), primary_key = True)
    day_number = Column(Integer, primary_key = True)
    count = Column(Integer)

class StatsTracker():
    """
        The stats tracker class tracks stats. Stats are normally per-guild,
        but stats with a guild_id of -1 are global.
    """

    def __init__(self, bot):
        self.bot = bot
        # Because we keep adding stuff, track the version so code can
        # check this and maybe refresh the object if need be.
        self.version = 1
        # Make sure the tables exist, in case we've hot-loaded this into
        # a running bot.
        self.init_tables(bot)

    def init_tables(self, bot):
        db = bot.database
        tables = bot.database.meta_data.tables
        if tables.get("stats") is not None and tables.get("stats_granular") is not None:
            return

        if tables.get("stats") is None:
            db.stats = Table("stats", db.meta_data,
                             Column("guild_id", Integer, primary_key=True),
                             Column("statname", String(100), primary_key=True),
                             Column("substat", String(100), primary_key=True),
                             Column("count", Integer),
                             Column("last_update", DateTime))

        if tables.get("stats_granular") is None:
            db.stats_granular = Table("stats_granular", db.meta_data,
                                      Column("guild_id", Integer,
                                             primary_key=True),
                                      Column("statname", String(100),
                                             primary_key=True),
                                      Column("substat", String(100),
                                             primary_key=True),
                                      Column("day_number", Integer, primary_key=True),
                                      Column("count", Integer))
        db.safe_start()

    def get_current_day(self):
        """
           Returns the current day, which is the number of days since Jan 1 1970.
        """
        return int(int(datetime.now().strftime("%s")) / 86400)
        
    def get(self, guild_id, stat, substat="", days = None):
        """
            Get the current value of a stat for a guild. Use a guild ID of
            None (or -1, they're interchangeable) for global stats.

            Days is how many days of history should be summed. None means
            'all history'.
    
            Returns the current value of the tracked stat, or None if the
            stat has no value.
        """
        if guild_id is None:
            guild_id = -1

        with Session(self.bot.engine) as session:
            if days is None:
                s = select(StatEntry).where(StatEntry.guild_id == guild_id,
                                            StatEntry.statname == stat,
                                            StatEntry.substat == substat)
                rows = session.execute(s)
                for r in rows.unique():
                    return r[0].count
                # Maybe nothing? Just return then.
                return None

            # OK, they want days. Use that instead.
            today = self.get_current_day()
            s = select(StatsEntry).where(StatsDay.guild_id == guild_id,
                                         StatsDay.statname == stat,
                                         StatsDay.substat == substat,
                                         StatsDay.day_number >= (today-days))
            count = 0
            rows = session.execute(s)
            for r in rows.unique():
                count = count + r[0].count

            return count
            
        # If we didn't find anything then return None
        return None

    def fetch(self, guild_id, stat, count=10, days=7, descending=True, submatch=None):
        """
          Fetch the top <count> substats, over the last <days> days, for
          <stat>. If <stat> was "emoji", for example, then this would return
          the most commonly used emoji in the most recent days.

          Returns a dict of substat and count
        """
        ret = []
        start_day = self.get_current_day()-days
        like_param = "%"
        if submatch is not None:
            like_param = "%" + submatch + "%"
        with Session(self.bot.engine) as session:
            s = None
            if descending:
                s = select(StatsDay.substat,
                           func.sum(StatsDay.count)).group_by(StatsDay.substat).where(StatsDay.guild_id == guild_id, StatsDay.statname == stat, StatsDay.day_number >= start_day, StatsDay.substat.like(like_param)).order_by(func.sum(StatsDay.count).desc()).limit(count)
            else:
                s = select(StatsDay.substat,
                           func.sum(StatsDay.count)).group_by(StatsDay.substat).where(StatsDay.guild_id == guild_id, StatsDay.statname == stat, StatsDay.day_number >= start_day, StatsDay.substat.like(like_param)).order_by(func.sum(StatsDay.count)).limit(count)
                
            rows = session.execute(s)
            for r in rows:
                ret.append([r[0], r[1]])
            
        return ret

    def increment(self, guild_id, stat, count=1, substat=""):
        """
            Increment the specified counter. If no count is given then the
            count will be incremented by one.
                                                                        
            Creates the counter entry if there isn't one already.
        """
        if guild_id is None:
            guild_id = -1
            
        with Session(self.bot.engine) as session:
            c = None
            s = select(StatEntry).where(StatEntry.guild_id == guild_id,
                                        StatEntry.statname == stat,
                                        StatEntry.substat == substat)
            rows = session.execute(s)
            for r in rows.unique():
                c = r[0]
                break
            if c is None:
                c = StatEntry(guild_id = guild_id,
                              statname = stat,
                              substat = substat,
                              count = 0)
            c.count = c.count + count
            c.last_update = datetime.now()
            session.add(c)
                
            doobj = None
            day = self.get_current_day()
            s = select(StatsDay).where(StatsDay.guild_id == guild_id,
                                       StatsDay.statname == stat,
                                       StatsDay.substat == substat,
                                       StatsDay.day_number == day)
            rows = session.execute(s)
            for r in rows.unique():
                doobj = r[0]
                break
            if doobj is None:
                doobj = StatsDay(guild_id = guild_id,
                                 statname = stat,
                                 substat = substat,
                                 day_number = day,
                                 count = 0)
            doobj.count = doobj.count + count
            session.add(doobj)
            session.commit()
            
    def decrement(self, guild_id, stat, count=1, substat=""):
        """
            Decrement the specified counter. If no count is given then
            the count will be decremented by one.

            Creates the counter entry if there isn't one already.
        """
        if guild_id is None:
            guild_id = -1
            
        with Session(self.bot.engine) as session:
            c = None
            s = select(StatEntry).where(StatEntry.guild_id == guild_id,
                                        StatEntry.statname == stat,
                                        StatEntry.substat == substat)
            rows = session.execute(s)
            for r in rows.unique():
                c = r[0]
                break
            if c is None:
                c = StatEntry(guild_id = guild_id,
                              statname = stat,
                              substat = substat,
                              count = 0)
            c.count = c.count - count
            c.last_update = datetime.now()
            session.add(c)
            
            doobj = None
            day = self.get_current_day()
            s = select(StatsDay).where(StatsDay.guild_id == guild_id,
                                       StatsDay.statname == stat,
                                       StatsDay.substat == substat,
                                       StatsDay.day_number == day)
            rows = session.execute(s)
            for r in rows.unique():
                do = r[0]
                break
            if doobj is None:
                doobj = StatsDay(guild_id = guild_id,
                                 statname = stat,
                                 substat = substat,
                                 day_number = day,
                                 count = 0)
            doobj.count = doobj.count + count
            session.add(doobj)
            session.commit()
            
