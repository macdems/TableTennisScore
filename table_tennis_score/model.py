# Copyright (c) 2022 Maciej Dems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()
Session = sessionmaker()

dbsession = None


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    color = Column(String(9))
    icon = Column(String(25), default='face', nullable=False)
    deleted = Column(Boolean, default=False)

    @property
    def matches(self):
        return Session().query(Match).filter(or_(Match.player1_id == self.id, Match.player2_id == self.id))

    @staticmethod
    def get_all():
        return dbsession.query(Player).filter(Player.deleted != True)

    def delete(self):
        if self.matches.count() == 0:
            dbsession.delete(self)
        else:
            self.deleted = True
        dbsession.commit()

    def purge(self):
        dbsession.refresh(self)
        if self.deleted and self.matches.count() == 0:
            dbsession.delete(self)


class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    player1_id = Column(Integer, ForeignKey('players.id'))
    player1 = relationship('Player', foreign_keys=player1_id)
    player2_id = Column(Integer, ForeignKey('players.id'))
    player2 = relationship('Player', foreign_keys=player2_id)
    start = Column(DateTime, default=datetime.now)
    end = Column(DateTime)
    _details = Column('details', String)
    score1 = Column(Integer)
    score2 = Column(Integer)
    finished = Column(Boolean)
    sets = relationship('Sets', cascade="all, delete, delete-orphan")

    @property
    def players(self):
        return self.player1, self.player2

    @property
    def scores(self):
        return self.score1, self.score2

    @property
    def winner(self):
        scores = self.scores
        return max((0, 1), key=lambda i: scores[i]) + 1

    @property
    def details(self):
        return json.loads(self._details)

    @details.setter
    def details(self, value):
        self._details = json.dumps(value)

    def end_match(self, score, stats, finished=True):
        self.end = datetime.now()
        self.finished = finished
        self.score1, self.score2 = score
        if stats:
            if self.id is None:
                dbsession.refresh(self)
            for p1, p2 in stats:
                dbsession.add(Sets(match_id=self.id, points1=p1, points2=p2))
        dbsession.commit()

    def delete(self):
        dbsession.delete(self)
        dbsession.commit()
        self.player1.purge()
        self.player2.purge()
        dbsession.commit()

class Sets(Base):
    __tablename__ = 'match_sets'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    points1 = Column(Integer)
    points2 = Column(Integer)


def init_db(app):
    dbdir = app.user_data_dir
    if os.name == 'nt': dbdir = dbdir.replace('\\', '/')
    engine = create_engine(f'sqlite:///{dbdir}/{app.name}.db')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    global dbsession
    dbsession = Session()
