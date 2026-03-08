from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False, index=True)
    season = Column(Integer, nullable=False, index=True)
    visitor = Column(String, nullable=False, index=True)
    home = Column(String, nullable=False, index=True)
    visitor_points = Column(Integer, nullable=True)
    home_points = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    result = Column(String, nullable=True)         # "visitor" | "home"
    visitor_elo_before = Column(Float, nullable=True)
    visitor_elo_after = Column(Float, nullable=True)
    home_elo_before = Column(Float, nullable=True)
    home_elo_after = Column(Float, nullable=True)
    visitor_delta = Column(Float, nullable=True)
    home_delta = Column(Float, nullable=True)
    win_prob_visitor = Column(Float, nullable=True)


class EloHistory(Base):
    __tablename__ = "elo_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team = Column(String, nullable=False, index=True)
    date = Column(String, nullable=False, index=True)
    elo = Column(Float, nullable=False)


class UpcomingGameDB(Base):
    __tablename__ = "upcoming_games"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    date       = Column(String, nullable=False)   # "YYYY-MM-DD"
    visitor    = Column(String, nullable=False)
    home       = Column(String, nullable=False)
    v_logo     = Column(String, nullable=True)
    h_logo     = Column(String, nullable=True)
    prob_v     = Column(Float, nullable=False)
    prob_h     = Column(Float, nullable=False)
    r_v        = Column(Float, nullable=False)
    r_h        = Column(Float, nullable=False)
    scraped_at = Column(DateTime(timezone=True), nullable=False)  # UTC
