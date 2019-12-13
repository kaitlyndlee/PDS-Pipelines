from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import (Column, Integer, Float,
                        Time, String, Boolean, PrimaryKeyConstraint, ForeignKey, CHAR, DateTime)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

import datetime

Base = declarative_base()

class BaseMixin(object):
    @classmethod
    def create(cls, session, **kw):
        obj = cls(**kw)
        session.add(obj)
        session.commit()
        return obj

    @staticmethod
    def bulkadd(iterable):
        session = Session()
        session.add_all(iterable)
        session.commit()
        session.close()


def create_table(keytype, *args, **kwargs):
    """ Returns a table based on the keytype description.

    Parameters
    ----------
    keytype : str
        A type description of the table's value.

    Returns
    -------
    out : :class:`.Instruments or :class:`.DataFiles or :class:`.Targets
        A SQLAlchemy table with type specific column specification.
    """

    try:
        return class_map[keytype.lower()](**kwargs)
    except NameError:
        print('Keytype {} not found\n'.format(keytype))


class DataFiles(BaseMixin, Base):
    __tablename__ = 'datafiles'
    upcid = Column(Integer, primary_key=True, autoincrement = True)
    isisid = Column(String(256))
    productid = Column(String(256))
    source = Column(String(1024))
    detached_label = Column(String(1024))
    instrumentid = Column(Integer, ForeignKey("instruments.instrumentid"))
    targetid = Column(Integer, ForeignKey("targets.targetid"))
    level = Column(CHAR(1))
    search_term = relationship('SearchTerms', backref="datafiles", uselist=False)


class Instruments(BaseMixin, Base):
    __tablename__ = 'instruments'
    instrumentid = Column(Integer, primary_key=True, autoincrement = True)
    instrument = Column(String(256), nullable=False)
    displayname = Column(String(256))
    mission = Column(String(256))
    spacecraft = Column(String(256))
    description = Column(String(256))
    #product_type = Column(String(8))


class Targets(BaseMixin, Base):
    __tablename__ = 'targets'
    targetid = Column(Integer, primary_key = True, autoincrement = True)
    naifid = Column(Integer)
    targetname = Column(String(20), nullable = False)
    system = Column(String(20), nullable = False)
    displayname = Column(String(20))
    aaxisradius = Column(Float)
    baxisradius = Column(Float)
    caxisradius = Column(Float)
    description = Column(String(1024))
    #iau_mean_radius = Column(Float)


class NewStats(BaseMixin, Base):
    __tablename__ = 'new_stats'
    instrumentid = Column(Integer, primary_key=True)
    targetid = Column(Integer, primary_key=True)
    targetname = Column(String(256))
    system = Column(String(20))
    instrument = Column(String(256))
    mission = Column(String(256))
    spacecraft = Column(String(256))
    displayname = Column(String(256))
    start_date = Column(Time)
    stop_date = Column(Time)
    last_published = Column(Time)
    bands = Column(Integer)
    total = Column(Integer)
    errors = Column(Integer)


class SearchTerms(BaseMixin, Base):
    __tablename__ = 'search_terms'
    upcid = Column(Integer, primary_key=True)
    upctime = Column(DateTime)
    starttime = Column(DateTime)
    solarlongitude = Column(Float)
    meangroundresolution = Column(Float)
    minimumemission = Column(Float)
    maximumemission = Column(Float)
    emissionangle = Column(Float)
    minimumincidence = Column(Float)
    maximumincidence = Column(Float)
    incidenceangle = Column(Float)
    minimumphase = Column(Float)
    maximumphase = Column(Float)
    phaseangle = Column(Float)
    targetid = Column(Integer, ForeignKey("targets.targetid"))
    instrumentid = Column(Integer, ForeignKey("instruments.instrumentid"))
    pdsproductid = Column(String(256), ForeignKey("datafiles.productid"))
    err_flag = Column(Boolean)
    isisfootprint = Column(Geometry())


class JsonKeywords(BaseMixin, Base):
    __tablename__ = "json_keywords"
    upcid = Column(Integer, primary_key=True)
    jsonkeywords = Column(JSONB)


class_map = {
    'datafiles': DataFiles,
    'instruments': Instruments,
    'targets' : Targets
}
