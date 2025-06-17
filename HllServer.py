import datetime
from HLLStatsDigester import HllGame
import httpx
from httpx_retries import Retry, RetryTransport

from typing import Tuple, Any

lobal_timeout = httpx.Timeout(15.0, read=None)
retry = Retry(backoff_factor=2, status_forcelist=[httpx.codes.INTERNAL_SERVER_ERROR, httpx.codes.BAD_GATEWAY])
transport = RetryTransport(retry=retry)

API_EP = '/api'
GAME_HISTORY_EP = '/get_scoreboard_maps'
CURRENT_MAP = '/get_public_info'
LIVE_GAME_STATS = '/get_live_game_stats'
EST_TO_GMT = datetime.timedelta(hours=6)
RCRON_TIME_STR_FORMAT = "%Y-%m-%dT%H:%M:%S"


def convert_s_to_datetime(seconds : int) -> datetime.datetime:
    dt = datetime.datetime.fromtimestamp(seconds)
    dt = dt + EST_TO_GMT
    return dt

def convert_rcron_time_str_to_datetime(time : str) -> datetime.datetime:
    dt = datetime.datetime.strptime(time, RCRON_TIME_STR_FORMAT)
    return dt

class HLLServer:
    def __init__(self, server_name, uri):
        self.server_name = server_name
        self.uri = uri

    def process_game_stats(self):
        pass

    # Return the current game
    async def get_current_game(self) -> HllGame:
        async with httpx.AsyncClient(transport=transport) as client:
            url = f'{self.uri}/{API_EP}/{CURRENT_MAP}'
            response = await client.get(url)

        if response.status_code != httpx.codes.OK:
            print(f"ERROR: Got a non-200 response code in 'get_current_game' for url: {url}")

        r = response.json()
        if r['failed']:
            raise ValueError(f'Bad response from CRCON in \'get_current_game\' for url: {url}')

        current_map = {'map_id' : None, 'start_time_s' : None} 
        map_id = r['result']['current_map']['map']['id']
        start_time_s = int(r['result']['current_map']['start'])

        return HllGame(self, map_id, start_time_s)

    async def get_current_game_stats(self) -> dict[Any : Any]:
        async with httpx.AsyncClient(transport=transport) as client:
            url = f'{self.uri}/{API_EP}/{LIVE_GAME_STATS}'
            response = await client.get(url)

        if response.status_code != httpx.codes.OK:
            raise ConnectionError(f'Got a non-200 response code in \'get_current_game_stats\' for url: {url}')
        
        stats = response.json()
        if stats['failed']:
            raise ValueError(f'Bad response from CRCON in \'get_current_game_stats\' for url: {url}')

        async with httpx.AsyncClient(transport=transport) as client:
            url = f'{self.uri}/{API_EP}/{CURRENT_MAP}'
            response = await client.get(url)

        if response.status_code != httpx.codes.OK:
            print(f"ERROR: Got a non-200 response code in 'get_current_game_stats' for url: {url}")

        public_info = response.json()
        if public_info['failed']:
            raise ValueError(f'Bad response from CRCON in \'get_current_game_stats\' for url: {url}')
        
        
        return stats, public_info

    # Is the game with game_id over?
    async def is_game_over(self, game: HllGame) -> bool:
        async with httpx.AsyncClient(transport=transport) as client:
            url = f'{self.uri}/{API_EP}/{CURRENT_MAP}'
            response = await client.get(url)

        if response.status_code != httpx.codes.OK:
            raise ConnectionError(f'Got a non-200 response code in \'is_game_over\' for url: {url}')
        
        r = response.json()
        if r['failed']:
            raise ValueError(f'Bad response from CRCON in \'is_game_over\' for url: {url}')

        current_map = await self.get_current_game()

        if game.map == current_map.map and game.start_time_s == current_map.start_time_s:
            return False

        return True

    # Get information about the game
    async def get_game(self, game: dict[str : str, str : int]) -> dict[any : any]:

        # Make a call to the GAME_HISTORY_EP to first get a list of all the maps..
        async with httpx.AsyncClient(transport=transport) as client:
            url = f'{self.uri}/{API_EP}/{GAME_HISTORY_EP}'
            response = await client.get(url)

        if response.status_code != httpx.codes.OK:
            raise ConnectionError(f'Got a non-200 response code in \'get_game\' for url: {url}')

        r = response.json()
        if r['failed']:
            raise ValueError(f'Bad response from CRCON in \'get_game\' for url: {url}')

        # Now search through the list of resutls and find the game by the id and the start time
        game_list = r['result']['maps']

        game_start_datetime = convert_s_to_datetime(game.start_time_s)
        game_match = None
        for prev_game in game_list:
            prev_game_start_time = convert_rcron_time_str_to_datetime(prev_game['start'])

            if game.map == prev_game['map']['id'] and game_start_datetime == prev_game_start_time:
                game_match = prev_game
                break
            else:
                continue

        return game_match
    
