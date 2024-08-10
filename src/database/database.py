from sqlalchemy import create_engine, event, MetaData

class Database:
    def __init__(self):
        # Parameterize this if you want to use another database engine.
        self.engine = create_engine('sqlite:///Bot.db')
        self.meta_data = MetaData()

        def set_pragmas(db, conn_record):
            """
               Sets some SQLite pragmas for our DB connections. This needs
               to be done every time a connection is made, as pragmas in SQLite
               (at least these) are connection-specific.

               These make database access a little more forgiving and, most
               importantly, make sure foreign keys are respected.
            """
            db.execute("pragma journal_mode = WAL")
            db.execute("pragma busy_timeout = 5000")
            db.execute("pragma synchronous = NORMAL")
            db.execute("pragma foreign_keys = true")

        event.listen(self.engine, 'connect', set_pragmas)

    def safe_start(self):
        """
            Make sure we're all set, and create any tables we need.
        """
        self.meta_data.create_all(self.engine, checkfirst=True)
