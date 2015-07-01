import requests, time, json, os, sys, random
import resources as rs
import MySQLdb as mdb, MySQLdb.cursors

def summoner_get_by_name(name):
    "gets summoner_id from a summoner name or list of names"
    token = get_token()
    api_url = "https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}".format(name, token)
    req = requests.get(api_url)
    if req.status_code == requests.codes.ok:
        return req.json()
    else:
        raise("Riot didn't respond to our request")

def summoner_get_current_rank(summoner_id):
    # takes a summoner ID and returns their current rank and division
    token = get_token()
    summoner_id = str(summoner_id)
    api_url = "https://na.api.pvp.net/api/lol/na/v2.5/league/by-summoner/{}/entry?api_key={}".format(summoner_id, token)
    req = requests.get(api_url, timeout=5)
    if req.status_code == requests.codes.ok:
    print req.json()
        tier = req.json()[summoner_id][0]["tier"]
        division = req.json()[summoner_id][0]["entries"][0]["division"]
        return "{} {}".format(tier, division)
    elif req.status_code == 404:
        return "Currently Unranked"
    else:
        raise("Rito didn't respond to our request")

def get_token():
    return os.getenv('leaguetoken')

def chunks(l, n):
    """Yield successive n-sized chunks from l"""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def __main__():
    slack_token = str(sys.argv[1])
    channel = str(sys.argv[2])

    con = mdb.connect('localhost', os.getenv('dbuser1'), os.getenv('dbpass1'), 'rtm',
                      cursorclass=MySQLdb.cursors.DictCursor)
    cur = con.cursor()
    cur.execute("SELECT * FROM Monikers WHERE Network = ':league:'")
    full_list = cur.fetchall()
    leaguers = list(chunks(full_list, 35))
    bad_names = []
    for leaguer_list in leaguers:
        namelist = []
        for leaguer in leaguer_list:
            name = leaguer["Moniker"]
            namelist.append(name)
        namelist = ','.join(namelist)
        for summoner in summoner_get_by_name(namelist).items():
            summoner = summoner[1]
            sql = "SELECT * FROM League WHERE S_ID = '%s'"
            query = cur.execute(sql, (summoner["id"]))
            if query == 0:
                # add the user to the League table if they're not in it yet
                sql = "SELECT * FROM Monikers WHERE Network = ':league:' AND Moniker = %s"
                query = cur.execute(sql, (summoner["name"]))
                if query > 0:
                    user = cur.fetchone()
                    sql = "INSERT INTO League (Slack_Id, Name, S_ID, Level) VALUES(%s, %s, %s, %s)"
                    cur.execute(sql, (user["Slack_Id"], summoner["name"], summoner["id"], summoner["summonerLevel"]))
                else:
                    bad_names.append(summoner["name"])
            else:
                # update the user in the table if their level changes
                rank = summoner_get_current_rank(summoner["id"])
                rank_sql = "SELECT * FROM League WHERE S_ID = %s AND Rank = %s"
                rank_query = cur.execute(rank_sql, (summoner["id"], rank))
                sql = "SELECT * FROM League WHERE S_ID = '%s' AND Level = '%s'"
                query1 = cur.execute(sql, (summoner["id"], summoner["summonerLevel"]))
                # now check to make sure they're in the Moniker table
                # (riot api fuzzy matches names better than i can)
                sql = "SELECT * FROM Monikers WHERE Network = ':league:' AND Moniker = %s"
                query = cur.execute(sql, (summoner["name"]))
                if query > 0 and query1 == 0:
                    user = cur.fetchone()
                    sql = "UPDATE League SET Level = %s WHERE S_ID = %s"
                    cur.execute(sql, (summoner["summonerLevel"], summoner["id"]))
                    sql = "SELECT * FROM Users WHERE Slack_Id = %s"
                    cur.execute(sql, (user["Slack_Id"]))
                    frd_user = cur.fetchone()
                    message = "omg {}/{} just leveled up to {}".format(frd_user["Nick"], summoner["name"], summoner["summonerLevel"])
                    rs.post(channel, message, "LoL shades", slack_token, icon_emoji=':league:')

                if query > 0 and rank_query == 0:
                    user = cur.fetchone()
                    sql = "UPDATE League SET Rank = %s where S_ID = %s"
                    cur.execute(sql, (rank, summoner["id"]))
                    if rank != "Currently Unranked":
                        sql = "SELECT * FROM Users WHERE Slack_Id = %s"
                        cur.execute(sql, (user["Slack_Id"]))
                        frd_user = cur.fetchone()
                        message = "omg {}/{} just changed ranks to {}.".format(frd_user["Nick"], summoner["name"], rank)
                        rs.post(channel, message, "LoL shades", slack_token, icon_emoji=':league:')
                time.sleep(1)

    con.commit()
    if len(bad_names) > 0:
        rs.msg_sean("bad names in monikers for :league: :" + ", ".join(bad_names), slack_token)



__main__()


