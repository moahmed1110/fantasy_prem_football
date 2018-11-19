import requests
import json
import pandas as pd
from pandas.io.json import json_normalize
import numpy as np
import itertools

n = 1000

loop_num = int(n/50)

username = "username"
password = "password"

position_map = [(1,"GOALKEEPER",1),(2,"DEFENDER",3),(3,"MIDFIELDER",4),(4,"STRIKER",3)]

def league_url(n):
    #generates url for list of league leaders
    league_url = "https://fantasy.premierleague.com/drf/leagues-classic-standings/313?phase=1&le-page=1&ls-page=" + str(n)
    return league_url


def team_url(owner_id,match_week):
    #generates url for full teams owned by owner_id
    team_url = "https://fantasy.premierleague.com/drf/entry/" + str(owner_id) + "/event/" + str(match_week) + "/picks"
    return team_url

def match_week():
    #gets current matchweek
    link = 'https://www.premierleague.com/'
    ua = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36'}
    response = requests.get(link, headers=ua)
    class_string = '<div class="week">'
    data = response.text
    n = data.find(class_string,1,len(data))
    x = n + len(class_string)
    return int(data[x:x+12].replace('Matchweek' ,'')) - 1

def get_player_data():
    #id is pk ALL GENERIC PLAYER DATA
    url = 'https://fantasy.premierleague.com/drf/bootstrap-static'
    response = requests.get(url)
    data = json.loads(response.content)
    df = pd.DataFrame(data['elements'])
    position_df = pd.DataFrame(position_map)
    position_df.columns = ["POSITION_ID","POSITION_NAME","FORMATION_COUNT"]
    df = df.merge(position_df, left_on='element_type', right_on='POSITION_ID', how='left')
    return df

def get_session():
    #creates session with fantasy prem
    with requests.Session() as session:
        url_home = 'https://fantasy.premierleague.com/'
        html_home = session.get(url_home)
        csrftoken = session.cookies['csrftoken']
        values = {
            'csrfmiddlewaretoken': csrftoken,
            'login': username,
            'password': password,
            'app': 'plfpl-web',
            'redirect_uri': 'https://fantasy.premierleague.com/a/login'
        }
        head = {
            'Host':'users.premierleague.com',
            'Referer': 'https://fantasy.premierleague.com/',
        }
        session.post('https://users.premierleague.com/accounts/login/',
                     data = values)
        return session


def get_top_teams(session):
    #generates list of all fantasy teams  in top x of the league
    full_team_df = []
    for i in range(1,loop_num+1):
        url = league_url(i)
        data = json.loads(session.get(url).content)
        df = pd.DataFrame(data['standings']['results'])
        full_team_df.append(df)
    return pd.concat(full_team_df)


def all_owned_players(session,match_week):
    full_player_df = []
    teams_df = get_top_teams(session)
    for row in teams_df.iterrows():
        entity_id = row[1][0]
        url = team_url(entity_id,match_week)
        data = json.loads(session.get(url).content)
        df = pd.DataFrame(data['picks'])
        df['owner_id'] = entity_id
        full_player_df.append(df)
    return pd.concat(full_player_df)

def combinations_of_3(l):
    for i, j, k in zip(*np.triu_indices(len(l), 2)):
        yield l[i], l[j], l[k]

week = match_week()
session = get_session()
owner_df = get_top_teams(session)
player_df = get_player_data()
top_players_df = all_owned_players(session,week)
df = owner_df.merge(top_players_df, left_on='entry', right_on='owner_id', how='left')
df = df.merge(player_df, left_on='element', right_on='id', how='left')
df.to_csv("full_data.csv")
