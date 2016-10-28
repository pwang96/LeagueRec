import requests
from user.resources import champions
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time

payload = {"api_key": "RGAPI-94a43db0-e13a-4b45-910c-30bc00a97896"}
# payload = {"api_key": "RGAPI-8a9caf1a-b6dd-41d2-a7be-c7d19f8a7112"}

site = "https://na.api.pvp.net"

summoner_info_req = "/api/lol/na/v1.4/summoner/by-name/%s"
ranked_stats_req = "/api/lol/na/v1.3/stats/by-summoner/%s/ranked"
league_req = "/api/lol/na/v2.5/league/by-summoner/%s"
matchlist_req = "/api/lol/na/v2.2/matchlist/by-summoner/%s"


def process_summoner(summoner_name):
    """
    Uses the LoL API to find the top 5 champions. Then uses machine learning to
    find suggested champions for the particular summoner.
    :param summoner_name: String, summoner name
    :return: Tuple:
            [List of summoner's top 5 champions]
            [List of recommended champions]
            summoner icon link (String)
            summoner rank (String)

    """
    request_count = 0  # limit: 10 requests per 10 seconds, 500 requests per 10 min

    # Getting the summoner ID and summoner icon
    r = requests.get(site + summoner_info_req % summoner_name, params=payload).json()
    request_count += 1
    summoner_id = r[summoner_name]["id"]
    iconId = r[summoner_name]["profileIconId"]
    summoner_icon = "http://ddragon.leagueoflegends.com/cdn/6.21.1/img/profileicon/%s.png" % iconId

    # Getting summoner rank
    rank, request_count, eqRankPlayers = get_summoner_rank(summoner_id, request_count)

    # Getting map of champion to games played and finding top 5 played champions
    championUsage, request_count = get_champion_usage(summoner_id, request_count)
    top5played, top5played_numGames = get_top5_played(championUsage)
    top5verbose = [champ+" "+num+" games" for champ, num in zip(top5played, top5played_numGames)]

    suggestions, request_count = get_suggestions(get_summoner_vector(championUsage),
                                                 eqRankPlayers, top5played, request_count)

    return top5verbose, suggestions, summoner_icon, rank


def get_summoner_rank(summonerId, request_count):
    league_stats = requests.get(site + league_req % summonerId, params=payload).json()
    request_count += 1
    if str(summonerId) in league_stats:
        for dct in league_stats[str(summonerId)]:
            if dct["queue"] == "RANKED_SOLO_5x5":
                tier = dct["tier"]
                eqRankPlayers = dct["entries"]
                for dct2 in eqRankPlayers:
                    if dct2["playerOrTeamId"] == str(summonerId):
                        division = dct2["division"]
                        lp = dct2["leaguePoints"]
                        if "miniSeries" in dct2:
                            progress = dct2["miniSeries"]["progress"]
                        else:
                            progress = ""
                        return " ".join([tier, division, "LP:", str(lp), progress]), request_count, eqRankPlayers
    else:
        return "Not enough ranked games played", request_count, {}


def get_top5_played(championUsage):
    """

    :param championUsage: output of get_champion_usage
    :return: list of names of top 5 played champions in ranked
    """
    top5played_id = sorted(championUsage, key=championUsage.get, reverse=True)[:5]
    top5played_name = [champions[i] for i in top5played_id]
    top5played_numGames = [str(championUsage[i]) for i in top5played_id]

    return top5played_name, top5played_numGames


def get_summoner_vector(championUsage):
    """
    This function returns the summoner's vector that will be used for cosine similarity
    The vector will be in the form of a list with n elements, where n is the number of
    champions there are
    :param championUsage: output of get_champion_usage
    :return: summoner's vector used for cosine similarity
    """
    champion_ids = champions.keys()
    summoner_vector = []
    for id in champion_ids:
        if id in championUsage:
            summoner_vector.append(championUsage[id])
        else:
            summoner_vector.append(0)

    return summoner_vector


def get_champion_usage(summonerId, request_count):
    """

    :param summonerId: int or string of summoner ID
    :return: dictionary mapping champion ID to games played with champion
    """

    ranked_stats = requests.get(site + ranked_stats_req % summonerId, params=payload).json()
    request_count += 1
    if request_count >= 10:
        time.sleep(10)
        request_count = 0
    numGamesPerChamp = {}
    for i in range(len(ranked_stats["champions"])):
        id = ranked_stats["champions"][i]["id"]
        sessions = ranked_stats["champions"][i]["stats"]["totalSessionsPlayed"]
        numGamesPerChamp[id] = sessions

    # Pop champion 0, the aggregate
    totalGames = numGamesPerChamp.pop(0)

    return numGamesPerChamp, request_count


def get_suggestions(summoner_vector, eqRankPlayerList, top5, request_count):
    """

    :param summoner_vector: summoner's vector, output of get_summoner_vector
    :param eqRankPlayerList: 250-long list of dictionaries, one for each player in the league
                            Each dictionary has the format:
                            {'division': string,
                             'isFreshBlood': boolean,
                             'isHotStreak': boolean,
                             'isInactive': boolean,
                             'isVeteran': boolean,
                             'leaguePoints': int,
                             'losses': int,
                             'miniSeries': dict,
                             'playerOrTeamId': string,
                             'playerOrTeamName': string,
                             'playstyle': string,
                             'wins': int}
    :param top5: list of length 5 of the summoner's top 5 played champions
    :param request_count:
    :return:
    """
    # if the eqRankPlayerList is an empty dictionary, don't compare
    if len(eqRankPlayerList) == 0:
        return ["play", "more", "games!!"], request_count

    # Exclude the one with cosine similarity =  1 because you compare summoner_vector to itself
    playerIds = [dct["playerOrTeamId"] for dct in eqRankPlayerList]

    # look through a quarter of the list for sake of time in testing
    similarity = dict.fromkeys(playerIds[0:len(playerIds)/16])

    # Get the cosing similarity between summoner and everyone else
    for pId in playerIds[0:len(playerIds)/16]:
        championUsage, request_count = get_champion_usage(pId, request_count)
        similarity[pId] = cosine_similarity(np.array(summoner_vector).reshape(1,-1),
                                            np.array(get_summoner_vector(championUsage)).reshape(1,-1))

    mostSimilarPlayerIds = sorted(similarity, key=similarity.get, reverse=True)[1:6]

    # get a set of their most played champions
    champ_set = set()
    for playerId in mostSimilarPlayerIds:
        championUsage, request_count = get_champion_usage(playerId, request_count)
        for champ in get_top5_played(championUsage)[0]:
            champ_set.add(champ)

    diff = champ_set.difference(set(top5))

    return list(diff)[:3], request_count
