import MySQLdb as mdb, MySQLdb.cursors, os, time, json, random, subprocess, re, sys, datetime, requests
from colorama import Fore as F, Back as B, Style as S, init
import resources as rs
from imp import reload
from resources import SlackEvent
init()

def __main__():
    colors = [F.GREEN, F.YELLOW, F.BLUE, F.MAGENTA, F.CYAN]
    super_users = {'slewis':'U029RFUDH'}
    username = 'shades McGee' #username for the bot
    token = os.getenv('stoken')
    dats_the_sound_of_da_police = False # enables police bot for @channels or @groups
    kill_me = False
    old_minute = 1000

    con = mdb.connect('localhost', os.getenv('dbuser1'), os.getenv('dbpass1'), 'rtm',
                      cursorclass=MySQLdb.cursors.DictCursor)
    cur = con.cursor()
    con2 = mdb.connect('localhost', os.getenv('dbuser2'), os.getenv('dbpass2'), 'rtm',
                      cursorclass=MySQLdb.cursors.DictCursor)
    cr = con2.cursor()

    print "Connecting"
    open_connection = rs.renew(token)
    if 'hello' in rs.to_u(open_connection.recv()):
        print 'Successfully Connected'
        open_connection.recv()
    icolor = 0
    while kill_me == False:
        try:
            # make sure we're connected to the db
            try:
                cur.fetchone()
                cr.fetchone()
            except:
                con = mdb.connect('localhost', os.getenv('dbuser1'), os.getenv('dbpass1'), 'rtm', cursorclass=mdb.cursors.DictCursor)
                cur = con.cursor()
                con2 = mdb.connect('localhost', os.getenv('dbuser2'), os.getenv('dbpass2'), 'rtm',
                                  cursorclass=MySQLdb.cursors.DictCursor)
                cr = con2.cursor()

            rightnow = datetime.datetime.now()
            hour = rightnow.hour
            minute = rightnow.minute
            is_weekday = 'True' if rightnow.isoweekday() < 6 else 'False'
            if old_minute != minute:
                sql = "SELECT * FROM Tasks WHERE (HOUR = %s OR HOUR = 247) AND Min = %s"
                query = cur.execute(sql, (hour, minute))
                if query > 0:
                    rows = cur.fetchall()
                    for row in rows:
                        if row["Weekday"] == is_weekday or row["Weekday"] == "All":
                            try:
                                exec(row["Command"])
                            except Exception, e:
                                rs.msg_sean("Scheduled problem: {} error: {}".format(row["Command"],str(e)), token)
            old_minute = minute
            try:
                event_json = json.loads(open_connection.recv())
            except:
                rs.msg_sean(str(open_connection.recv()), token)

            event = SlackEvent(event_json, cur, token)
            if 'user' in event_json.keys():
                event_json['user'] = event.name
            if 'channel' in event_json.keys():
                event_json['channel'] = event.channel_name

            if icolor >= len(colors):
                icolor = 0
            if ('message' not in event.etype) and event.subtype != "bot_message":
                print rs.colorize(event_json, icolor)
                icolor = icolor + 1
            else:

                if event.etype == 'message':
                    if 'gif me ' in event.text:
                        sql = "SELECT * FROM Gif_Whitelist WHERE Slack_Id = %s AND Channel = %s"
                        query = cur.execute(sql, (event.user_id, event.channel_id))
                        if query > 0 or (event.channel_id == rs.get_im(event.user_id, token)):
                            user_authed = True
                        else:
                            user_authed = False

                        if (user_authed == True) or (event.user_id in super_users.values()):
                            tag = event.text.replace('gif me ', '').replace(' ', '+')
                            subprocess.Popen(["python", rs.get_shades_path() + "gifme.py", tag, event.channel_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            print tag + ' ' + event.channel_id

                    if event.user_id in super_users.values():

                        if 'gif bless ' in event.text:
                            to_bless = event.text.replace('gif bless ', '')
                            sql = "SELECT * FROM Users WHERE Name LIKE %s OR Nick LIKE %s"
                            query = cur.execute(sql, (rs.like(to_bless), rs.like(to_bless)))
                            if query > 0:
                                row = cur.fetchone()
                                slackid = row["Slack_Id"]
                                to_bless = row["Name"]
                                sql = "SELECT * FROM Gif_Whitelist WHERE Slack_Id = %s AND Channel = %s"
                                query = cur.execute(sql, (slackid, event.channel_id))
                                if query > 0:
                                    message = "%s has already been blessed in this channel." % to_bless
                                else:
                                    sql = "INSERT INTO Gif_Whitelist (Slack_Id, Channel) VALUES(%s, %s)"
                                    cur.execute(sql, (slackid, event.channel_id))
                                    message = to_bless + " has been blessed with gif me powers in this channel."
                            else:
                                message = "Sorry brochinski, I don't know who " + to_bless + " is."
                            rs.post(event.channel_id, message, "based GIF GODS", token, icon_emoji=":fire:")

                        if 'gif revoke ' in event.text:
                            to_revoke = event.text.replace('gif revoke ', '')
                            sql = "SELECT * FROM Users WHERE Name LIKE %s or Nick LIKE %s"
                            query = cur.execute(sql, (rs.like(to_revoke), rs.like(to_revoke)))
                            if query > 0:
                                row = cur.fetchone()
                                slackid = row["Slack_Id"]
                                to_revoke = row["Name"]
                                sql = "SELECT * FROM Gif_Whitelist WHERE Slack_Id = %s AND Channel = %s"
                                query = cur.execute(sql, (slackid, event.channel_id))
                                if query > 0:
                                    sql = "DELETE FROM Gif_Whitelist WHERE Slack_Id = %s AND Channel = %s"
                                    cur.execute(sql, (slackid, event.channel_id))
                                    message = to_revoke + ' has been damned by the gif gods.'
                                else:
                                    message = to_revoke + " ain't blessed, yo"
                            else:
                                message = "Sorry brochinski, I don't know who " + to_revoke + " is."
                            rs.post(event.channel_id, message, "based GIF GODS", token, icon_emoji=":fire:")

                        if "!shutdown" in event.text:
                            rs.post(event.channel_id, 'going down', 'shades', token)
                            kill_me = True

                        if "!restart" in event.text:
                            rs.post(event.channel_id, 'restarting and updating, be back shortly', 'shades', token)
                            subprocess.Popen(["bash", rs.get_shades_path() + "restart.sh"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            kill_me = True

                        if "shades channel_police " in event.text:
                            if 'off' in event.text:
                                dats_the_sound_of_da_police == False
                                rs.msg_sean('Channel police has been turned off', token)
                            if 'on' in event.text:
                                dats_the_sound_of_da_police == True
                                rs.msg_sean('Channel police is back on baby!', token)

                        if "dbdump " in event.text:
                            try:
                                db = event.text.replace("dbdump ", "")
                                # getting extra quotes if we cur.execut(sql, (db)) on this one
                                sql = "SELECT * FROM {}".format(db)
                                query = cur.execute(sql)
                                if query > 0:
                                    temp_arr = []
                                    rows = cur.fetchall()
                                    for row in rows:
                                        temp_arr.append(row)
                                    data = str(temp_arr)
                                    message = data
                                else:
                                    message = "yo, I don't have {} in my db".format(db)
                            except Exception, e:
                                message = "problem with {}: \r {}".format(db, e)
                            rs.msg_sean(message, token)

                        if "shades tweet: " in event.text:
                            tweet = event.text.replace("shades tweet: ", "")
                            tweet = "{}".format(tweet)
                            subprocess.Popen(["python", rs.get_shades_path() + "tweet.py", tweet], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            message = "Sending tweet :bird:"
                            rs.post(event.channel_id, message, "tweetyshadesofgrey", token, icon_emoji=":bird:")

                        if "!schedule " in event.text:
                            try:
                                commands = event.text.replace("!schedule ", "")
                                weekday = re.search(r'(?<=w\:)\S+', commands).group()
                                hour = re.search(r'(?<=h\:)\d+', commands).group()
                                minute = re.search(r'(?<=m\:)\d+', commands).group()
                                command = re.search(r'(?<=cmd\:).*', commands).group()

                                sql = "INSERT INTO Tasks (Command, Weekday, Hour, Min) VALUES(%s, %s, %s, %s)"
                                cur.execute(sql, (command, weekday, hour, minute))
                                message = "Successfully scheduled task"
                            except Exception, problem:
                                message = "Couldn't schedule because: {}".format(problem)
                            rs.post(event.channel_id, message, "shades mcstatus", token)

                        if "reload resources" in event.text:
                            try:
                                reload(rs)
                                message = "Successfully reimported our resources file"
                            except:
                                message = "Was unable to reimport resources.py"
                            rs.msg_sean(message, token)

                        if re.search(r'^!e', event.text) != None:
                            code = event.text.replace("DOT", ".")
                            if re.search(r'^!ev ', event.text) != None:
                                code = code.replace("!ev ", "")
                                try:
                                    message = str(eval(code))
                                    rs.post(event.channel_id, message, 'shades mcPythonInterpreter', token)
                                except Exception, e:
                                    message = str(e)
                                    rs.post(event.channel_id, message, 'shades mcPythonInterpreter', token)

                            if re.search(r'^!ex ', event.text) != None:
                                code = code.replace("!ex ", "")
                                print code
                                try:
                                    exec(code)
                                    message = "success"
                                except Exception, e:
                                    message = str(e)
                                rs.post(event.channel_id, message, 'shades mcPythonInterpreter', token)

                # block where we deal with 2n stuff
                    if re.search(r'^!2n ', event.text) != None:
                        if re.search(r'^!2n status \w*$', event.text) != None:
                            team = event.text.replace('!2n status ', '')
                            rs.two_n(team, event.channel_id, token, cur)

                        if re.search(r'^!2n change \S* \d*$', event.text) or re.search(r'^!2n add \S* \d*$', event.text):
                            msg_items = re.search(r'^!2n \w* \w* \d*$', event.text).group().split(' ')
                            team = msg_items[2]
                            n_number = int(msg_items[3])
                            sql = "SELECT * FROM 2n_Teams WHERE Team = %s"
                            query = cur.execute(sql, (team))
                            if query > 0:
                                team_row = cur.fetchone()
                                current_n = int(team_row["N_Number"])
                                if current_n != n_number:
                                    sql = "UPDATE 2n_Teams SET N_Number = %s WHERE Team = %s"
                                    cur.execute(sql, (n_number, team))
                                    message = team + ' n number changed from ' + str(team_row["N_Number"]) + ' to ' + str(n_number)
                                else:
                                    message = "Current N number is already that value. Nothing to change."
                            else:
                                sql = "INSERT INTO 2n_Teams (Team, N_Number) VALUES(%s, %s)"
                                cur.execute(sql, (team, n_number))
                                message = team + ' added with an n number of ' + str(n_number)
                            rs.post(event.channel_id, message, '2n bot', token, icon_emoji=':robot:')
                            rs.msg_sean(message + ' changed by ' + event.name, token)

                        if re.search(r'^!2n delete \w*$', event.text) and event.user_id in super_users.values():
                            team = re.search(r'^!2n delete \w*$', event.text).group().split(' ')[2]
                            sql = "SELECT * FROM 2n_Teams WHERE Team = '%s'" % team
                            query = cur.execute(sql)
                            if query > 0:
                                sql = "DELETE FROM 2n_Teams WHERE Team = '%s'" % team
                                cur.execute(sql)
                                sql = "DELETE FROM 2n_Nicks WHERE Team = '%s'" % team
                                cur.execute(sql)
                                msg = team + ' has been deleted and all associated nicknames removed.'
                                rs.post(event.channel_id, msg, '2n bot', token, icon_emoji=':robot:')
                                rs.msg_sean(msg + ' by ' + event.name, token)
                            else:
                                rs.post(event.channel_id, team + " doesn't exist.", '2n bot', token, icon_emoji=':robot:')

                        if re.search(r'^!2n add_nick \S* \S*$', event.text):
                            msg_items = re.search(r'^!2n add_nick \S* \S*$', event.text).group().split(' ')
                            nickname = msg_items[2]
                            team = msg_items[3]
                            sql = "SELECT * FROM 2n_Nicks WHERE Team = '{}' AND Nick = '{}'".format(team, nickname)
                            query = cur.execute(sql)
                            if query == 0:
                                sql = "SELECT * FROM 2n_Teams WHERE Team = '{}'".format(team)
                                query = cur.execute(sql)
                                if query == 1:
                                    sql = "INSERT INTO 2n_Nicks (Team, Nick) VALUES('{}', '{}')".format(team, nickname)
                                    cur.execute(sql)
                                    message = "`!2n status {}` will now return data for {}!".format(nickname, team)
                                else:
                                    message = "I can't add {} as a nickname because {} doesn't exist. Use `!2n add team number` to add your team.".format(nickname, team)
                            else:
                                message = "{} already has {} as a nickname :(".format(team, nickname)
                            rs.post(event.channel_id, message, '2n bot', token, icon_emoji=':robot:')

                        if re.search(r'^!2n delete_nick \S*$', event.text):
                            msg_items = re.search(r'^!2n delete_nick \S*$', event.text).group().split(' ')
                            nickname = msg_items[2]
                            sql = "SELECT * FROM 2n_Nicks WHERE Nick = '{}'".format(nickname)
                            query = cur.execute(sql)
                            if query > 0:
                                sql = "DELETE FROM 2n_Nicks WHERE Nick = '{}'".format(nickname)
                                cur.execute(sql)
                                message = "All nicknames: {} have been removed from the database. They will no longer work in !2n status.".format(nickname)
                            else:
                                message = "{} doesn't seem to have been added as a nickname yet.".format(nickname)
                            rs.post(event.channel_id, message, '2n bot', token, icon_emoji=':robot:')
                        if re.search(r'^!2n query \S*$', event.text):
                            msg_items = re.search(r'^!2n query \S*$', event.text).group().split(' ')
                            team = msg_items[2]
                            sql = "SELECT * FROM 2n_Nicks WHERE Nick = %s"
                            nick_query = cur.execute(sql, (team))
                            nick_row = cur.fetchone()
                            team_sql = "SELECT * FROM 2n_Teams WHERE Team = %s"
                            team_query = cur.execute(team_sql, (team))
                            if nick_query > 0 or team_query > 0:
                                if team_query > 0:
                                    row = cur.fetchone()
                                if nick_query > 0:
                                    team_query = cur.execute(team_sql, (nick_row["Team"]))
                                    row = cur.fetchone()
                                    team = row["Team"]

                                query = row["Query"]
                                if query == None:
                                    base = "https://{}.atlassian.net/rest/api/2/search?jql=".format(os.getenv('jiradomain'))
                                    default_query = base + (base + '(status%20%20%3D%20Open%20OR%20status%20%3D%20"In%20Progress"%20OR%20status%20%3'
                                                           'D%20"QA"%20OR%20status%20%3D%20Feedback%20or%20status%20%3D%20"QA%20Ready")'
                                                           '%20AND%20((type%20%3D%20"Support%20Week%'
                                                           '20Task"%20AND%20status%20!%3D%20"QA")%20OR%20type%20%3D%20Bug)%20AND%20("Sprint%'
                                                           '20Team"%20%3D%20%27' + team + '%27)')

                                    message = ("The `{}` team does not have a custom query set, "
                                               "they will be using this default query: `{}`").format(team, default_query)
                                else:
                                    message = "Here's the query for the {} team: \r\n `{}`".format(team, query)
                            else:
                                message = "{} doesn't seem to be a team I recognize.".format(team)
                            rs.post(event.channel_id, message, '2n bot', token, icon_emoji=':robot:')
                        if re.search(r'^!2n change_query \S* \S*$', event.text):
                            msg_items = re.search(r'^!2n change_query \S* \S*$', event.text).group().split(' ')
                            team = msg_items[2]
                            new_query = re.sub(r"\S*\|", "", msg_items[3].replace(">", "").replace("<", ""))

                            sql = "SELECT * FROM 2n_Nicks WHERE Team = %s"
                            nick_query = cur.execute(sql, (team))
                            nick_row = cur.fetchone()
                            team_sql = "SELECT * FROM 2n_Teams WHERE Team = %s"
                            team_query = cur.execute(team_sql, (team))
                            if (nick_query > 0 or team_query > 0):
                                if re.search(r'https:\/\/\w*\.atlassian.net\S*jql=', new_query) != None:
                                    # check query validity
                                    jiracred = (os.getenv('juser') + ':' + os.getenv('jpass')).encode('base64', 'strict')
                                    headers = {'Authorization': 'Basic ' + jiracred}
                                    query_test = requests.get(new_query, headers=headers)
                                    if query_test.status_code == requests.codes.ok:
                                        if team_query > 0:
                                            row = cur.fetchone()
                                        if nick_query > 0:
                                            team_query = cur.execute(team_sql, (nick_row["Team"]))
                                            row = cur.fetchone()
                                            team = row["Team"]
                                        old_query = row["Query"]
                                        sql = "UPDATE 2n_Teams SET Query = %s WHERE Team = %s"
                                        cur.execute(sql, (new_query, team))
                                        message = "New Query `{}` applied to {}".format(query, team)
                                        rs.msg_sean(message + " by {}. \r\n The old query was: `{}`".format(event.name, old_query), token)
                                    else:
                                        message = "{} is not a valid query, you can only add a valid query to a team.".format(new_query)
                                else:
                                    message = "{} is not a valid query, you can only add a valid query to a team.".format(new_query)
                            else:
                                message = "{} doesn't seem to be a team I recognize.".format(team)
                            rs.post(event.channel_id, message, '2n bot', token, icon_emoji=':robot:')

                # Logic for monikers
                    if re.search(r'^!monikers ', event.text) != None:
                        msg_items = event.text.split(" ")
                        message = "What are you trying to have me do?! Use !monikers help to get some help."
                        banned_monikers = ["all", "me"]
                        del_args = ["remove", "delete"]
                        add_args = ["add", "create"]
                        command_list = ["list", "reset"] + del_args + add_args
                        if msg_items[1] not in command_list:
                            if msg_items[1] == "help":
                                message = """Here's how to use my monikers module:
                                    `!monikers somename` will look up somename and if they exist attempt to list out the usernames and networks they belong to.
                                    `!monikers me` will look up and return your usernames and networks they belong to.
                                    `!monikers add/create username network` will associate you to username on network.
                                    `!monikers delete/remove username network` will delete all usernames that match username on that network.
                                    `!monikers list network` will list all monikers and who they belong to for network.
                                    `!monikers reset all/network` will remove all monikers or all monikers on network.
                                """
                            else:
                                search_for = event.text.replace("!monikers ", "")
                                if search_for == "me":
                                    sql = "SELECT * FROM Monikers WHERE Slack_Id = '{}'".format(event.user_id)
                                    query = cur.execute(sql)
                                    if query > 0:
                                        mn_rows = cur.fetchall()
                                        message = "These are the monikers associated to you: \r\n"
                                        for row in mn_rows:
                                            network = row['Network']
                                            message = message + "{}: {}\r\n".format(network, row['Moniker'])
                                    else:
                                        message = "You do not have any monikers stored in my database. Use `!monikers add username network` to add one for yourself."
                                else:
                                    sql = "SELECT * FROM Users WHERE Name LIKE '%{}%' OR Nick LIKE '%{}%'".format(search_for, search_for)
                                    query = cur.execute(sql)
                                    if query > 0:
                                        row = cur.fetchone()
                                        slackid = row["Slack_Id"]
                                        name = row["Name"]
                                        sql = "SELECT * FROM Monikers WHERE Slack_Id = '{}'".format(slackid)
                                        query = cur.execute(sql)
                                        if query > 0:
                                            mn_rows = cur.fetchall()
                                            message = "I found these monikers for {}:\r\n".format(name)
                                            for row in mn_rows:
                                                network = row['Network']
                                                message = message + "{}: {}\r\n".format(network, row['Moniker'])
                                        else:
                                            message = "{} does not have any monikers stored in my database. Use `!monikers add username network` to add one for yourself.".format(name)
                                            sql = "SELECT * FROM Monikers WHERE Moniker LIKE '%{}%'".format(search_for)
                                            query = cur.execute(sql)
                                            if query > 0:
                                                msearch_rows = cur.fetchall()
                                                message = "I found these monikers matching `{}`:\r\n".format(search_for)
                                                for row in msearch_rows:
                                                    slack_id = row['Slack_Id']
                                                    sql = "SELECT * FROM Users WHERE Slack_Id = '{}'".format(slack_id)
                                                    cur.execute(sql)
                                                    nick_row = cur.fetchone()
                                                    nick = nick_row['Nick']
                                                    network = row['Network']
                                                    moniker = row['Moniker']
                                                    message = message + "@{}: moniker: {} on network: {} \r\n".format(nick, moniker, network)
                                    else:
                                        message = "I could not find anybody with the name or moniker {} in the db. You may want to try their @name or their full name.".format(search_for)
                                        sql = "SELECT * FROM Monikers WHERE Moniker LIKE '%{}%'".format(search_for)
                                        query = cur.execute(sql)
                                        if query > 0:
                                            msearch_rows = cur.fetchall()
                                            message = "I found these monikers matching `{}`:\r\n".format(search_for)
                                            for row in msearch_rows:
                                                slack_id = row['Slack_Id']
                                                sql = "SELECT * FROM Users WHERE Slack_Id = '{}'".format(slack_id)
                                                cur.execute(sql)
                                                nick_row = cur.fetchone()
                                                nick = nick_row['Nick']
                                                network = row['Network']
                                                moniker = row['Moniker']
                                                message = message + "@{}: moniker: {} on network: {} \r\n".format(nick, moniker, network)

                        else:
                            command = msg_items[1]
                            if msg_items > 3:
                                moniker = event.text.replace("!monikers {} ".format(command), "")
                                if command in add_args:
                                    network = msg_items[-1]
                                    if network in banned_monikers:
                                        message = "You cannot use `all` as a network, this would break things."
                                    else:
                                        moniker = re.sub(r" {}$".format(network), "", moniker)
                                        sql = "SELECT * FROM Monikers WHERE Slack_Id = %s AND Network = %s"
                                        query = cur.execute(sql, (event.user_id, network))
                                        cur_monikers = cur.fetchall()
                                        moniker_array = []
                                        for item in cur_monikers:
                                            moniker_array.append(item['Moniker'])
                                        if moniker not in moniker_array:
                                            sql = "INSERT INTO Monikers (Slack_Id, Moniker, Network) VALUES(%s, %s, %s)"
                                            ins_query = cur.execute(sql, (event.user_id, moniker, network))
                                            if ins_query > 0:
                                                message = "Successfully added `{}` as a moniker on {} for you.".format(moniker, network)
                                        else:
                                            message = "Already have {} as a moniker for you bro".format(moniker)
                                if command in del_args:
                                    network = msg_items[-1]
                                    moniker = re.sub(r" {}$".format(network), "", moniker)
                                    sql = ("SELECT * FROM Monikers WHERE Slack_Id = '{}' AND Monike"
                                             "r= '{}' AND Network = '{}'")
                                    sql = sql.format(event.user_id, moniker, network)
                                    query = cur.execute(sql)
                                    if query > 0:
                                        sql = "DELETE FROM Monikers WHERE Slack_Id = '{}' AND Moniker = '{}' AND Network = '{}'".format(event.user_id, moniker, network)
                                        cur.execute(sql)
                                        message = "All monikers matching {} associated to you on {} have been deleted from the database.".format(moniker, network)
                                    else:
                                        message = "Sorry yo, I don't have `{}` as a moniker for you on {}".format(moniker, network)
                                if command == "list":
                                    network = msg_items[-1]
                                    if network == "list":
                                        message = "You need to tell me a network to search for: `!monikers list network`"
                                    else:
                                        sql = "SELECT * FROM Monikers WHERE Network = '{}'".format(network)
                                        query = cur.execute(sql)
                                        if query > 0:
                                            net_rows = cur.fetchall()
                                            message = "These are the users and their monikers I found for {}:\r\n".format(network)
                                            for row in net_rows:
                                                slack_id = row['Slack_Id']
                                                sql = "SELECT * FROM Users WHERE Slack_Id = '{}'".format(slack_id)
                                                query = cur.execute(sql)
                                                if query > 0:
                                                    name_row = cur.fetchone()
                                                    if name_row['Name'] == "None":
                                                        name = name_row['Nick']
                                                    else:
                                                        name = name_row['Name']
                                                    message = message + "{}: {}\r\n".format(name, row['Moniker'])
                                if command == "reset":
                                    network = msg_items[-1]
                                    if network == 'all':
                                        sql = "DELETE FROM Monikers WHERE Slack_Id = '{}'".format(event.user_id)
                                        cur.execute(sql)
                                        message = "All monikers belonging to you have been deleted."
                                    else:
                                        sql = "DELETE FROM Monikers WHERE Slack_Id = '{}' AND Network = '{}'".format(event.user_id, network)
                                        cur.execute(sql)
                                        message = "All monikers on {} belonging to you have been removed.".format(network)
                                #if command == "search":
                                 #   search_for = msg_items[-1]
                                  #  if search_for == 'search':
                                   #     message = "Please specify something to search for. `!monikers search name/network`"
                        user_dm = rs.get_im(event.user_id, token)
                        rs.post(user_dm, message, 'shades McMoniker', token, icon_emoji=':robot:')
                        if event.channel_id != user_dm:
                            rs.post(event.channel_id, "just dm'd you bruv", 'shades McMoniker', token, icon_emoji=':robot:')

                    if re.search(r'^!shades help$', event.text) != None:
                        message = """ Here's a list of things I can do:
                         `!2n` - lets you check the 2n status of any team
                            `!2n status assessments` this will return x/y where x is current open JIRAs and y is the team's 2n number
                            `!2n change newteam 3` this will change newteam's n number to 3, or add newteam to the bot with an n number of 3.
                            `!2n add newteam 3` same as above
                            `!2n delete newteam` will delete the team 'newteam' from the bot. admin only
                            `!2n add_nick nickname team` will add a nickname for a team, then `!2n status nickname` will fetch data for team
                                (can use one nick name for multiple teams, ex. mobile will call both ios and android)
                            `!2n delete_nick nickname` will remove all nicknames matching nickname from the database.
                            `!2n query team` will show you the current JIRA query that team is following.
                            `!2n change_query team new_query` will set new_query to be used when team is called by !2n status

                        `!monikers` - lets you associate yourself to various usernames on various networks (like :xbl:, :psn:, or :steam:)
                            `!monikers somename` will look up somename and if they exist attempt to list out the usernames and networks they belong to.
                            `!monikers me` will look up and return your usernames and networks they belong to.
                            `!monikers add username network` will associate you to username on network.
                            `!monikers delete username network` will delete all usernames that match username on that network.
                        """
                        rs.post(event.channel_id, message, username, token, icon_emoji=':robot:')

            if (("<!channel>" in event.text) or ("<!group>" in event.text)) and dats_the_sound_of_da_police == True:
                food_var = False
                if event.channel_id[0] == 'C':
                    channel_info = rs.get_channel(event.channel_id, token, full_object=True)
                    member_count = len(channel_info[u'channel'][u'members'])
                    if 'lunch' in event.text:
                        food_var = True
                    if 'food' in event.text:
                        food_var = True
                    if (member_count >= 100 and food_var == False):
                        police_username = event.name + " has @channel\'d " # + rs.to_u(member_count) + " people drop everything"
                        url = 'http://post.mnsun.com/wp-content/uploads/2012/08/stop-sign.jpg'
                        emoji = ":alert:"
                        channel_messages = [' grab your pitchforks ', ' _drops everything_ ', ' grab your torches :fire: ',
                                            ' :beaker: ', ' dis gon be gud :popcorn: ',
                                            ' the @channel police are en route to your location :cop: :alert:']
                        message = random.choice(channel_messages)
                        rs.post(event.channel_id, message, police_username, token, url, emoji)

            if (("gist.github" not in str(event_json)) and ("message_changed" not in str(event_json)) and ("presence_change" not in str(event_json))):
                try:
                    print rs.colorize(event_json, icolor, highlight=True)
                    icolor = icolor + 1
                except:
                    pass
                #       s_message = 'We got a problem sir, \r\n' + str(event)
                #       rs.msg_sean(s_message, token)
        except Exception, e:
            try:
                open_connection.close()
            except:
                pass
            connected = False
            while connected == False:
                try:
                    print "Disconnected, reconnecting. \r\n {}".format(str(e))
                    rs.msg_sean("Oops i died \r\n {}".format(str(e)), token)
                    open_connection = rs.renew(token)
                    if 'hello' in rs.to_u(open_connection.recv()):
                        print "Successfully reconnected."
                        connected = True
                except:
                    print "Failed to reconnect, retrying"
                    time.sleep(1)
        con.commit()
        time.sleep(.001)

__main__()
