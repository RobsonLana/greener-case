from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SolarPanels(Base):
    __tablename__ = 'solar_panels'
    sha_id = Column(String(64), primary_key = True)
    origin = Column(String(32))
    updated_at = Column(DateTime)
    port = Column(String(16))
    price = Column(String(32))
    structure = Column(String(16))

tables = {
    'solar_panels': SolarPanels
}

class MysqlConnection:

    def __init__(self, user, password, host, database):
        self.user = user
        self.password = password
        self.host = host
        self.database = database

        self.tables = tables

        connection_url = f'mysql+pymysql://{self.user}:{self.password}@{self.host}:3306/{database}'

        try:
            engine = create_engine(connection_url)
            Session = sessionmaker(bind = engine)
            self.session = Session()


        except Exception as e:
            print('Something went wrong when tried to connect to database')

            self.session.close()
            raise e

    def insert_statement(self, table, *rows):
        if len(rows) == 0:
            print('No rows provided to be inserted')
            return None

        self.session.bulk_insert_mappings(
            self.tables[table], rows,
            render_nulls = True
        )

        self.session.commit()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def __del__(self):
        self.session.close()