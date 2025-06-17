# Give me a CRCON Server and I'll give you stats
from dataclasses import dataclass
from typing import List, Tuple, TypedDict

from weapons import Team, detect_team
import numpy as np
import numpy.ma as ma

INITAL_DATA_ARRAY_SIZE = 70

@dataclass
class HllStat:
    name : str
    rcron_name : str
    short_name : str
    compute_sum : bool
    compute_mean : bool
    compute_median : bool
    compute_std : bool

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
                             std=None)
        self.nvalues = 0

    def __str__(self) -> str:
        return f'<Stat(Name:{self.short_name}, nValues:{self.nvalues})>'
    
    @property
    def data(self) -> np.ndarray:
        return self._data.data

    @property
    def name(self) -> str:
        return self.hllStat.name

    @property
    def short_name(self) -> str:
        return self.hllStat.short_name

    @property
    def rcron_name(self) -> str:
        return self.hllStat.rcron_name

    @property
    def sum(self) -> str:
        return self.data.sum

    @property
    def mean(self) -> str:
        return self.data.mean

    @property
    def median(self) -> str:
        return self.data.median

    @property
    def std(self) -> str:
        return self.data.std

    def add_datum(self, datum):
        self.data[self.nvalues] = datum
        self.nvalues += 1

    def compute_stats(self):
        if self.hllStat.compute_sum:
            self.compute_sum()

        if self.hllStat.compute_mean:
            self.compute_mean()

        if self.hllStat.compute_median:
            self.compute_mean()

        if self.hllStat.compute_std:
            self.compute_std()

    def compute_sum(self):
        self.data.sum = np.sum(self.data)

    def compute_mean(self):
        self.data.mean = np.average(self.data)

    def compute_median(self):
        self.data.median = np.median(self.data)

    def compute_std(self):
        self.data.std = np.std(self.data)

class HllSideStats:
    def __getattr__(self, name):
        if name == 'score' or name == 'Score':
            return self.score 

        return self.stats_dict[name]

    def __contains__(self, key):
        return key in self.stats_dict

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

    def create_stat(self, 
                    name : str, 
                    rcon_name: str,
                    short_name : str=None,
                    compute_sum=True,
                    compute_mean=True,
                    compute_median=True,
                    compute_std=True):

        if short_name is None:
            short_name = name

        statInfo = HllStat(name=name,
                       rcron_name=rcon_name,
                       short_name=short_name,
                       compute_sum=compute_sum,
                       compute_mean=compute_mean,
                       compute_median=compute_median,
                       compute_std=compute_std)
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
        


class HllGameStats:
    def __init__(self, stats=None, public_info=None):
        self.axis = HllSideStats(Team.AXIS)
        self.allied = HllSideStats(Team.ALLIES)
        self.teams = {Team.AXIS: self.axis,
                      Team.ALLIES : self.allied}
        self.total_players : int = 0

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
        self.axis.time_remaing_secs = public_info['time_remaining']
        self.allied.time_remaing_secs = public_info['time_remaining']

        self.axis.score = public_info['score']['axis']
        self.allied.score = public_info['score']['allied']

        self.total_players = public_info['player_count']
        self.axis.nplayers = public_info['player_count_by_team']['axis']
        self.allied.nplayers = public_info['player_count_by_team']['allied']
