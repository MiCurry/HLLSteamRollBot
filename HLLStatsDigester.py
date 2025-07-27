# Give me a CRCON Server and I'll give you stats
from dataclasses import dataclass
import datetime
from enum import Enum
from typing import List, Tuple, TypedDict

from utilities import Team, detect_team
import numpy as np
import numpy.ma as ma

INITAL_DATA_ARRAY_SIZE = 200
RCRON_TIME_STR_FORMAT = "%Y-%m-%dT%H:%M:%S"

class GameState(str, Enum):
    EMPTY = "empty"
    SEEDING = "seeding"
    WARMUP = "Warm-Up"
    PLAYING = "Playing"
    GAMEOVER = "Game-over"


@dataclass
class HllStat:
    name : str
    rcron_name : str
    short_name : str
    compute_sum : bool
    compute_mean : bool
    compute_median : bool
    compute_std : bool
    np_type : str

@dataclass
class StatData:
    name : str
    data : np.ndarray
    sum : float
    mean : float
    median : float
    std : float

class Stat:
    def __init__(self, hllStat : HllStat):
        self.hllStat = hllStat
        self._data = StatData(name=self.hllStat.name,
                             data=np.ma.masked_all((INITAL_DATA_ARRAY_SIZE,)),
                             sum=None,
                             mean=None,
                             median=None,
                             std=None,
                             )
        self.nvalues = 0

        self._data.sum = 0.0
        self._data.mean = 0.0
        self._data.median = 0.0
        self._data.std = 0.0

    def __str__(self) -> str:
        return f'<Stat(Name:{self.short_name}, nValues:{self.nvalues})>'

    @property
    def data(self) -> np.ndarray:
        return self._data.data

    @property
    def name(self) -> str:
        return self.hllStat.name

    @property
    def np_type(self) -> str:
        return self.hllStat.np_type

    @property
    def short_name(self) -> str:
        return self.hllStat.short_name

    @property
    def rcron_name(self) -> str:
        return self.hllStat.rcron_name

    @property
    def sum(self) -> str:
        return self._data.sum

    @property
    def mean(self) -> str:
        return self._data.mean

    @property
    def median(self) -> str:
        return self._data.median

    @property
    def std(self) -> str:
        return self._data.std

    def add_datum(self, datum):
        self.data[self.nvalues] = datum
        self.nvalues += 1

    def compute_stats(self):
        if self.hllStat.compute_sum:
            self.compute_sum()

        if self.hllStat.compute_mean:
            self.compute_mean()

        if self.hllStat.compute_median:
            self.compute_median()

        if self.hllStat.compute_std:
            self.compute_std()

    def compute_sum(self):
        self._data.sum = np.sum(self.data)

    def compute_mean(self):
        self._data.mean = np.average(self.data)

    def compute_median(self):
        self._data.median = np.ma.median(self.data)

    def compute_std(self):
        self._data.std = np.std(self.data)


class HllSideStats:
    def __getattr__(self, name):
        if name == 'score' or name == 'Score':
            return self.score 

        return self.stats_dict[name]

    def __contains__(self, key):
        return key in self.stats_dict

    @property
    def nstats(self) -> int:
        return len(self.stats)

    def __init__(self, team=Team.UNKNOWN):
        self.side : Team = team

        self.stats : List[Stat] = []
        self.stats_dict : dict = {}

        self.time_remaing_secs : int = 0
        self.score : int = 0
        self.nplayers : int = 0

        self.create_stat('Combat', 'combat')
        self.create_stat('Offense', 'offense')
        self.create_stat('Defense', 'defense')
        self.create_stat('Support', 'support')
        self.create_stat('Kills', 'kills')
        self.create_stat('Deaths', 'deaths')

        self.create_stat('Teamkills', 'teamkills') 
        self.create_stat('Teamkill Streak', 'teamkills_streak')

        self.create_stat('Kills Per Minute', 'kills_per_minute', short_name='KPM')
        self.create_stat('Deaths Per Minute', 'deaths_per_minute', short_name='DPM')

        self.create_stat('Kill Death Ratio', 'kill_death_ratio', short_name='KD')

        self.create_stat('Deaths w/o Kill Streak', 'deaths_without_kill_streak')

        self.create_stat('Longest Life', 'longest_life_secs')
        self.create_stat('Shortest Life', 'shortest_life_secs')

    def to_numpy(self):
        stats = ()
        dtypes = []

        stats += (self.score,)
        stats += (self.nplayers,)
        dtypes += ((f'{self.side.name} Score', '<i4'),)
        dtypes += ((f'{self.side.name} Players', '<i4'),)

        for stat in self.stats:
            if stat.hllStat.compute_sum:
                name = f'{self.side.name} {stat.name} Total'
                stats += (stat.sum,)
                dtypes += ((name, stat.np_type),)

            if stat.hllStat.compute_mean:
                name = f'{self.side.name} {stat.name} Mean'
                stats += (stat.mean,)
                dtypes += ((name, '<f8'),)

            if stat.hllStat.compute_median:
                name = f'{self.side.name} {stat.name} Median'
                stats += (stat.median,)
                dtypes += ((name, '<f8'),)

            if stat.hllStat.compute_std:
                name = f'{self.side.name} {stat.name} Std'
                stats += (stat.std,)
                dtypes += ((name, '<f8'),)

        return stats, dtypes

    def make_datatypes(self):
        dtypes = []

        dtypes.append((f'{self.side.name} Score', '<i4'))
        dtypes.append((f'{self.side.name} Players', '<i4'))

        for stat in self.stats:
            if stat.hllStat.compute_sum:
                name = f'{self.side.name} {stat.name} Total'
                dtypes.append((name, stat.np_type))

            if stat.hllStat.compute_mean:
                name = f'{self.side.name} {stat.name} Mean'
                dtypes.append((name, '<f8'))

            if stat.hllStat.compute_median:
                name = f'{self.side.name} {stat.name} Median'
                dtypes.append((name, '<f8'))

            if stat.hllStat.compute_std:
                name = f'{self.side.name} {stat.name} Std'
                dtypes.append((name, '<f8'))

        return dtypes

    def create_stat(self, 
                    name : str, 
                    rcon_name: str,
                    short_name : str=None,
                    compute_sum=True,
                    compute_mean=True,
                    compute_median=True,
                    compute_std=True,
                    np_type='<f8'):

        if short_name is None:
            short_name = name

        statInfo = HllStat(name=name,
                       rcron_name=rcon_name,
                       short_name=short_name,
                       compute_sum=compute_sum,
                       compute_mean=compute_mean,
                       compute_median=compute_median,
                       compute_std=compute_std,
                       np_type=np_type)
        stat = Stat(statInfo)
        
        self.stats.append(stat)
        self.stats_dict[rcon_name] = stat

    def compute_stats(self):
        for stat in self.stats:
            stat.compute_stats()

    def add_datum(self, name, stat):
        if name not in self:
            raise ValueError(f"'{name}' not in this HllSideStats object")

        data : Stat = self.stats_dict[name]
        data.add_datum(stat)
        data.compute_stats()
    
        

class HllGameStatsSlice:
    def __init__(self, stats=None, public_info=None):
        self.final_score = {Team.ALLIES : 0,
                            Team.AXIS : 0}
        self.was_steamroll = False

        self.axis = HllSideStats(Team.AXIS)
        self.allied = HllSideStats(Team.ALLIES)
        self.teams = {Team.AXIS: self.axis,
                      Team.ALLIES : self.allied}
        self.time_remaining_secs = 0
        self.total_players : int = 0
        self.final_duration : int = None

        if stats is not None and public_info is not None:
            self.process_stats(stats, public_info)

    def process_stats(self, rcon_stats, public_info):
        self._process_public_info(public_info)
        player_stats = rcon_stats['result']['stats']

        for player in player_stats:
            team, _ = detect_team(player)

            if team == Team.UNKNOWN:
                continue

            for stat in player:
                if stat not in self.teams[team]:
                    continue

                self.teams[team].add_datum(stat, player[stat])
                
    def _process_public_info(self, public_info):
        public_info = public_info['result']
        self.time_remaining_secs = public_info['time_remaining']

        self.axis.score = public_info['score']['axis']
        self.allied.score = public_info['score']['allied']

        self.total_players = public_info['player_count']
        self.axis.nplayers = public_info['player_count_by_team']['axis']
        self.allied.nplayers = public_info['player_count_by_team']['allied']
    
    def make_datatypes(self):
        dtypes = []

        dtypes.extend(((f'Time Reamining', '<i4'),))
        dtypes.extend(self.allied.make_datatypes())
        dtypes.extend(self.axis.make_datatypes())

        return dtypes

    def to_numpy(self):
        stats = []
        dtypes = []

        axis_stat, axis_dtype = self.axis.to_numpy()
        stats.extend([self.time_remaining_secs])
        stats.extend(axis_stat)
        dtypes.extend(axis_dtype)

        allies_stat, _ = self.allied.to_numpy()
        stats.extend(allies_stat)

        return stats, dtypes

class HllGame:
    def __str__(self) -> str:
        return f'<HllGame - {self.map} - {self.start_time_s} - SR: {self.steamroll}'

    def __init__(self, server=None, map=None, start_time_s=None):
        self.state : GameState = GameState.EMPTY

        self.map = None
        self.server = None
        self.start_time_s = None

        if server is not None:
            self.server = server

        if map is not None:
            self.map = map
        
        if map is not None:
            self.start_time_s = start_time_s

        self.game_mode = None
        self.stat_slices : List[HllGameStatsSlice] = []
        self.current_time_remaining = 0
        self.current_score = {Team.ALLIES : 0, Team.AXIS : 0}

        self.steamroll = False
        self.steamroll_reason = None
        self.winner = Team.UNKNOWN
        self.loser = Team.UNKNOWN

    def add_stat_slice(self, stat, public):
        stat_slice = HllGameStatsSlice(stats=stat, public_info=public)

        self.state = GameState.PLAYING
        self.time_remaining = stat_slice.time_remaining_secs
        self.score[Team.ALLIES] = stat_slice.allied.score
        self.score[Team.AXIS] = stat_slice.axis.score

        self.stat_slices.append(stat_slice)

    @property
    def nslices(self) -> int:
        return len(self.stat_slices)

    @property
    def score(self) -> dict:
        return self.current_score

    @score.setter
    def score(self, value : dict):
        self.current_score = value

    @property
    def time_remaining(self) -> int:
        return self.current_time_remaining

    @time_remaining.setter
    def time_remaining(self, value :int):
        self.current_time_remaining = value

    def mark_stats_with_result(self):
        for stat in self.stat_slices:
            stat.was_steamroll = self.steamroll
            stat.final_score = self.score
            stat.final_duration = self.duration.total_seconds

    def process_game_result(self, result):
        self.start_time=datetime.datetime.strptime(result['start'], RCRON_TIME_STR_FORMAT)
        self.end_time=datetime.datetime.strptime(result['end'], RCRON_TIME_STR_FORMAT)
        self.duration = self.end_time - self.start_time

        self.score[Team.ALLIES] = result['result']['allied']
        self.score[Team.AXIS] = result['result']['axis']
        self.game_mode = result['map']['game_mode']
        self.state = GameState.GAMEOVER

    def was_steamroll(self, steamroll_threshold_minutes=30) -> bool:
        if self.score[Team.ALLIES] > self.score[Team.AXIS]:
            self.winner = Team.ALLIES
            self.loser = Team.AXIS
        else:
            self.winner = Team.AXIS
            self.loser = Team.ALLIES

        if self.game_mode != 'warfare':
            self.steamroll = False
            self.steamroll_reason = "Was an Offensive game"
            self.steamroll = False
        elif self.duration > datetime.timedelta(minutes=steamroll_threshold_minutes):
            self.steamroll = False
            self.steamroll_reason = f'Greater than {steamroll_threshold_minutes} minutes'
        else:
            self.steamroll = True
            self.steamroll_reason = f'Was less than {steamroll_threshold_minutes} minutes'

        self.state = GameState.GAMEOVER

        return self.steamroll

    def make_y_numpy(self) -> np.ndarray:
        stats = ()
        dtypes = []

        name = 'AXIS Score'
        dtypes.append((f'{name}', 'I'))
        stats += (self.score[Team.AXIS],)

        name = 'ALLIED Score'
        dtypes.append((f'{name}', 'I'))
        stats += (self.score[Team.ALLIES],)

        name = 'WAS STEAMROLL'
        dtypes.append((f'{name}', 'I'))
        stats += (self.was_steamroll(), )

        return np.array([stats], dtype=dtypes)

    def to_numpy(self):
        self.y = self.make_y_numpy()
        dtypes = self.stat_slices[0].make_datatypes()

        self.all_x = np.empty([self.nslices], dtype=dtypes)

        for idx, slices in enumerate(self.stat_slices):
            slice, dtype = slices.to_numpy()
            slice = tuple(slice)
            self.all_x[idx]= tuple(slice)

        return 1

    def save_stat_slice(self, fname):
        with open(fname, "a") as f:
            np.savetxt(f, self.all_x, delimiter=',')

    def save_y(self, fname):
        with open(fname, "a") as f:
            np.savetxt(f, self.y)


        

