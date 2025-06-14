# Give me a CRCON Server and I'll give you stats
from typing import Tuple, TypedDict

from weapons import Team, detect_team
import numpy as np
np.set_printoptions(precision=3)

class Stats(TypedDict):
    side : Team = None
    nplayers : int = 0

    combat_list : list[int] = []
    combat : int = 0
    avg_combat : float = 0.0

    offense_list : list[int] = []
    offense : int = 0
    avg_offense : float = 0.0

    defense_list : list[int] = []
    defense : int = 0
    avg_defense : float = 0.0

    support_list : list[int] = []
    support : int = 0
    avg_support : float = 0.0

    kills_list : list[int] = []
    kills : int = 0
    avg_kills : float = 0.0

    deaths_list : list[int] = []
    deaths : int = 0
    avg_deaths : float = 0.0

    kd_list : list[float] = []
    avg_kd : float = 0.0
    team_kd : float = 0.0

    teamkills_list : list[int] = []
    teamkills : int = 0
    avg_team_kills : float = 0.0

    kills_per_minute_list : list[float] = []
    avg_kills_per_minute : float = 0.0

    deaths_per_minute_list : list[float] = []
    avg_deaths_per_minute : float = 0.0

    kill_streak_list : list[int]
    avg_kill_streak : float = 0.0

    death_streak_list : list[int]
    avg_death_streak : float = 0.0

    deaths_without_kill_streak_list : list[int]
    avg_deaths_without_kill_streak : float = 0.0

    longest_life_list : list[float]
    avg_longest_life : float = 0.0

    shortest_life_list : list[float]
    avg_shortest_life : float = 0.0


def new_stats():
    return Stats(side=None,
                 nplayers=0,
                 combat_list=[],
                 combat=0,
                 avg_combat=0.0,
                 offense_list=[],
                 offense=0,
                 avg_offense=0.0,
                 defense_list=[],
                 defense=0,
                 avg_defense=0.0,
                 support_list=[],
                 support=0,
                 avg_support=0.0,
                 kills_list=[],
                 kills=0,
                 avg_kills=0.0,
                 deaths_list=[],
                 deaths=0,
                 avg_deaths=0.0,
                 kd_list=[],
                 avg_kd=0.0,
                 team_kd=0.0,
                 teamkills_list=[],
                 teamkills=0,
                 kills_per_minute_list=[],
                 avg_kills_per_minute=0.0,
                 deaths_per_minute_list=[],
                 avg_deaths_per_minute=0.0,
                 kill_streak_list=[],
                 avg_kill_streak=0.0,
                 death_streak_list=[],
                 avg_death_streak=0.0,
                 deaths_without_kill_streak_list=[],
                 avg_deaths_without_kill_streak=0.0,
                 longest_life_list=[],
                 avg_longest_life=0.0,
                 shortest_life_list=[],
                 avg_shortest_life=0.0,
                 avg_team_kills=[]
                )

class GameStats(TypedDict):
    allied : Stats = None
    axis : Stats = None

def add_to_stat(stats, side, player, stat):
    stats[side][stat] += player[stat]


def grab_raw_stats(stats_json):
    stats = GameStats(allied=new_stats(), axis=new_stats())

    for player in stats_json['result']['stats']:

        res = detect_team(player)

        if res['side'] == Team.UNKNOWN:
            continue

        if res['side'] == Team.ALLIES:
            side = 'allied'
        elif res['side'] == Team.AXIS:
            side = 'axis'
        else:
            continue

        stats[side]['nplayers'] += 1
        stats[side]['side'] = res['side']

        add_to_stat(stats, side, player, 'combat')
        stats[side]['combat_list'].append(player['combat'])

        add_to_stat(stats, side, player, 'offense')
        stats[side]['offense_list'].append(player['offense'])

        add_to_stat(stats, side, player, 'defense')
        stats[side]['defense_list'].append(player['defense'])

        add_to_stat(stats, side, player, 'support')
        stats[side]['support_list'].append(player['support'])

        add_to_stat(stats, side, player, 'kills')
        stats[side]['kills_list'].append(player['kills'])

        add_to_stat(stats, side, player, 'deaths')
        stats[side]['deaths_list'].append(player['deaths'])

        add_to_stat(stats, side, player, 'teamkills')
        stats[side]['teamkills_list'].append(player['teamkills'])

        stats[side]['kd_list'].append(player['kill_death_ratio'])

        stats[side]['kills_per_minute_list'].append(player['kills_per_minute'])

        stats[side]['deaths_per_minute_list'].append(player['deaths_per_minute'])

        stats[side]['kill_streak_list'].append(player['kills_streak'])

        stats[side]['deaths_without_kill_streak_list'].append(player['deaths_without_kill_streak'])

        stats[side]['longest_life_list'].append(player['longest_life_secs'])

        stats[side]['shortest_life_list'].append(player['shortest_life_secs'])

        stats[side]['teamkills_list'].append(player['teamkills'])

    return stats


def process_stats(raw_stats):
    team_stats = grab_raw_stats(raw_stats)

    for team in team_stats.values():
        for stat in team:
            if type(team[stat]) == list:
                team[stat] = np.array(team[stat])

        team['combat'] = np.sum(team['combat_list'])
        team['avg_combat'] = np.average(team['combat_list'])

        team['offense'] = np.sum(team['offense_list'])
        team['avg_offense'] = np.average(team['offense_list'])

        team['defense'] = np.sum(team['defense_list'])
        team['avg_defense'] = np.average(team['defense_list'])

        team['support'] = np.sum(team['support_list'])
        team['avg_support'] = np.average(team['support_list'])

        team['kills'] = np.sum(team['kills_list'])
        team['avg_kills'] = np.average(team['kills_list'])

        team['deaths'] = np.sum(team['deaths_list'])
        team['avg_deaths'] = np.average(team['deaths_list'])

        team['avg_kd'] = np.average(team['kd_list'])
        team['team_kd'] = team['kills'] / team['deaths']

        team['teamkills'] = np.sum(team['teamkills_list'])
        team['avg_teamkills'] = np.average(team['teamkills_list'])

        team['avg_kills_per_minute'] = np.average(team['kills_per_minute_list'])

        team['avg_deaths_per_minute'] = np.average(team['deaths_per_minute_list'])

        team['avg_kill_streak'] = np.average(team['kill_streak_list'])

        team['avg_deaths_without_kill_streak'] = np.average(team['deaths_without_kill_streak_list'])

        team['avg_shortest_life'] = np.average(team['longest_life_list'])

        team['avg_shortest_life'] = np.average(team['shortest_life_list'])

    return team_stats


        





class HLLStatsDigester:
    def __init__(self, server):
        self.server = server
        stats, public = self.get_stats()
        self.stats = {'stats' : stats, 'public_info' : public}

    def get_stats(self):
        return self.server.get_current_game_stats()

    @property
    def player_count(self) -> int:
        return self.stats['public_info']['player_count']

    @property
    def nallied(self) -> int:
        return self.stats['public_info']['player_count_by_team']['allied']

    @property
    def naxis(self) -> int:
        return self.stats['public_info']['player_count_by_team']['axis']

    @property
    def score_raw(self) -> dict[str : int, str : int]:
        return self.stats['public_info']['score']

    @property
    def score_allied_axis(self) -> tuple[int, int]:
        return (self.stats['public_info']['score']['allied'],
                self.stats['public_info']['score']['axis'])
    
    @property
    def allied_score(self) -> int:
        return self.stats['public_info']['score']['allied']

    @property
    def axis_score(self) -> int:
        return self.stats['public_info']['score']['axis']

    @property
    def time_remaining_s(self) -> int:
        return self.stats['public_info']['time_remaining']

