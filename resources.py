import MySQLdb as mdb, MySQLdb.cursors, requests, os, time, json, ast, random, subprocess, re, sys, urllib
from websocket import create_connection
from colorama import Fore as F, Back as B, init
init()

class SlackEvent:
    """slack event class"""
    def __init__(self, event_json, cur, token):
        self.keys = event_json.keys()
        self.etype = to_u(event_json[u'type'])
        self.subtype = to_u(event_json[u'subtype']) if 'subtype' in self.keys else 'none'
        self.channel_id = to_u(event_json[u'channel']) if 'channel' in self.keys else 'none'
        self.text = to_u(event_json[u'text']) if 'text' in self.keys else 'none'
        self.user_id = 'none'
        self.user_dm = 'none'
        self.name = 'none'
        self.channel_name = 'none'

        # time for the hard stuff
        if 'user' in self.keys and len(event_json[u'user']) <= 10:
            self.user_id = to_u(event_json[u'user'])
            try:
                sql = "SELECT * FROM Users WHERE Slack_Id = '%s'" % self.user_id
                query = cur.execute(sql)
                if query > 0:
                    user_row = cur.fetchone()
                    self.name = user_row["Name"]
                    self.nick = user_row["Nick"]
                else:
                    names = get_name(self.user_id, token)
                    self.nick = names[0]
                    self.name = names[1]
                    add_user(self.name, self.nick, self.user_id, cur)
                if self.name == "None":
                    self.name = self.nick
            except Exception, e:
                message = ("borked " + to_u(self.user_id) +
                           "event " + to_u(event_json) +
                           "exception: " + to_u(e))
                msg_sean(message, token)

        if 'channel' in self.keys:
            try:
                if self.channel_id[0] == 'C':
                    sql = "SELECT * FROM Channels WHERE Slack_Id = '{}'".format(self.channel_id)
                    query = cur.execute(sql)
                    if query > 0:
                        row = cur.fetchone()
                        self.channel_name = row["Name"]
                    else:
                        self.channel_name = get_channel(self.channel_id, token)
                        sql = "INSERT INTO Channels (Slack_Id, Name) VALUES('{}', '{}')".format(self.channel_id, self.channel_name)
                        cur.execute(sql)
                else:
                    self.channel_name = self.channel_id
            except:
                msg_sean(event_json, token)

def find_or_create(filepath, write=False):
    """finds or creates a file with the passed path"""
    if write == False:
        try:
            new_file = open(filepath, 'r')
        except:
            new_file = open(filepath, 'w')
            new_file.close()
            new_file = open(filepath, 'r')
    else:
        new_file = open(filepath, 'w')
    return new_file

def like(string):
    """formats a string for mysql LIKE query"""
    return '%' + string + '%'

def to_u(text):
    """turn a string to a unicode string (hopefully)"""
    try:
        return str(text)
    except:
        return text.encode('ascii','ignore').strip()

def league_check(token, channel):
    """Runs the League Check scripts which checks for all :league: monikers and updates them or puts them in the League table"""
    subprocess.Popen(["python", get_shades_path() + "league.py", token, channel], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def add_user(name, nick, slackid, cur):
    """adds a user to the database"""
    sql = ("INSERT INTO Users "
           "(Name, Nick, Slack_Id) "
           "VALUES(%s, %s, %s)")
    cur.execute(sql, (name, nick, slackid))

def two_n_fetch(team, cur):
    """fetches a teams two_n number from the db"""
    temp_arr = []
    sql = "SELECT * FROM 2n_Teams WHERE Team = '%s'" % team
    query = cur.execute(sql)
    if query > 0:
        temp_arr.append(cur.fetchone())
        return temp_arr
    else:
        sql = "SELECT * FROM 2n_Nicks WHERE Nick = '%s'" % team
        query = cur.execute(sql)
        if query > 0:
            for row in cur.fetchall():
                team = row["Team"]
                sql = "SELECT * FROM 2n_Teams WHERE Team = '%s'" % team
                query = cur.execute(sql)
                rows = cur.fetchall()
                for item in rows:
                    temp_arr.append(item)
            return temp_arr
        else:
            return None

def post(channel, message, username, token, icon_url='', icon_emoji=':shadesmcgee:'):
    """posts a message to a channel (in slack) with the supplied parameters"""
    nurl_temp = ("https://slack.com/api/chat.postMessage?token={}&channel={}"
                 "&text={}&username={}&icon_url={}&icon_emoji={}")
    nurl = nurl_temp.format(token, channel, urllib.quote(message), username, icon_url, icon_emoji)
    return requests.get(nurl, timeout=5)

def schedule_task(code_string, weekday, hour, minute, cur):
    """ put a task into the database for execution """
    sql = ("INSERT INTO Tasks (Command, Weekday, Hour, Min) VALUES('{}','{}','{}','{}')"
          ).format(code_string, weekday, hour, minute)
    cur.execute(sql)

def slack_connect():
    """db connection for slack"""
    return mdb.connect('localhost', os.getenv('dbuser2'), os.getenv('dbpass2'), 'rtm', cursorclass=mdb.cursors.DictCursor)

def get_shades_path():
    return os.getenv('shades_dir')

def two_n(team, channel, token, cur, stat = "False"):
    human_arr = ['yo', 'eh', 'lol', 'nerd', 'boo', 'friend', 'comrade', 'chum', 'crony', 'confidant', 'ally', 'associate', 'confrere', 'compatriot']
    two_n = two_n_fetch(team, cur)
    if two_n != None:
        if len(two_n) == 1:
            two_n = two_n[0]
            subprocess.Popen(["python", get_shades_path() + "two_n.py", str(two_n["Team"]), str(two_n["N_Number"]), channel, stat], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            for item in two_n:
                subprocess.Popen(["python", get_shades_path() + "two_n.py", item["Team"], str(item["N_Number"]), channel, stat], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if (two_n == None) and (team != 'all'):
        message = "I don't know that team, " + random.choice(human_arr) +  ". Do `2n add {team_name} {n_number}` to add your team."
        post(channel, message, '2n bot', token, icon_emoji=':robot:')
    if team == 'all':
        cur.execute("SELECT * FROM 2n_Teams")
        all_n = cur.fetchall()
        for i in all_n:
            subprocess.Popen(["python", get_shades_path() + "two_n.py", i["Team"], str(i["N_Number"]), channel, stat], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def msg_sean(message, token):
    """messages sean about something"""
    post("D040WDA0X", message, "shades McStatus", token)

def get_im(user_id, token):
    imurl = "https://slack.com/api/im.open?token=" + token + "&user=" + user_id
    chan_id = requests.get(imurl, timeout=5)
    chan_id = chan_id.json()['channel']['id']
    return chan_id

def get_user_id(name_nick, cur):
    sql = "SELECT * FROM Users WHERE Name LIKE %s OR Nick LIKE %s"
    query = cur.execute(sql, (like(name_nick), like(name_nick)))
    if query > 0:
        return cur.fetchone()
    else:
        return None

def message_user(nick, message, token, cur, name="shades McGee", emoji=":shades:"):
    user_id = get_user_id(nick, cur)
    if user_id != None:
        dm_channel = get_im(user_id, token)
        post(dm_channel, message, name, token, icon_emoji=emoji)

def get_name(user_id, token):
    """runs api call to retrieve a users' name"""
    u_url = "https://slack.com/api/users.info?token=" + token + "&user=" + user_id + "&pretty=1"
    namereq = requests.get(u_url, timeout=5)
    namereq = namereq.json()
    if namereq[u'user'][u'profile'][u'real_name_normalized'] != '':
        try:
            return [to_u(namereq[u'user'][u'name']), to_u(namereq[u'user'][u'profile'][u'real_name_normalized'])]
        except:
            return [to_u(namereq[u'user'][u'name']), "None"]
    else:
        return [to_u(namereq[u'user'][u'name']), "None"]

def get_channel(channel_id, token, full_object=False):
    """runs api call to retrieve channel name"""
    c_url = "https://slack.com/api/channels.info?token=" + token + "&channel=" + channel_id + "&pretty=1"
    chan_resp = requests.get(c_url, timeout=5)
    chan_resp = chan_resp.json()
    if full_object == False:
        return to_u(chan_resp[u'channel'][u'name'])
    else:
        return chan_resp

def renew(token):
    """this function opens an rtm connection with slack to receive events"""
    renew_resp = requests.get(url="https://slack.com/api/rtm.start?token=" + token + "&pretty=1")
    wsurl = to_u(renew_resp.json()[u'url'])
    return create_connection(wsurl)

def cupbop_stalk(token):
    url = ("https://api.instagram.com/v1/users/1160261459/media/recent/"
           "?client_id=bd804ee2f5c64c2fb986328f1e4504c3&count=1")

    cupbop_post = requests.get(url)

    if cupbop_post.status_code == requests.codes.ok:
        cupbop_json = cupbop_post.json()["data"][0]
        tags = cupbop_json["tags"]
        inst_url = cupbop_json["link"]
        caption = cupbop_json["caption"]
        created_time = caption["created_time"]
        caption_text = caption["text"]
        if ("overstock" in tags or "Overstock Oldmill" in caption_text):
            message = ":cupbop: is at overstock today! Link: {}".format(inst_url)
        else:
            message = ":cupbop: ain't at overstock today :("
        msg_sean(message, token)
    else:
        message = "Insta api didn't want to show me cupbop's instagram :("
        msg_sean(message, token)

def colorize(cdict, colornumber, highlight=False):
    """colorizes terminal output from the script"""
    colors = [F.GREEN,F.YELLOW,F.BLUE,F.MAGENTA,F.CYAN]
    colored_message = ''
    current_color = colors[colornumber]
    lastkey = cdict.keys()[-1]
    for i in cdict.keys():
        if 'message' in i:
            x_msg = json.dumps(cdict[i])
            x_msg = ast.literal_eval(x_msg)
            xlastkey = x_msg.keys()[-1]
            for item in x_msg.keys():
                key = to_u(item)
                value = to_u(x_msg[item])
                if item != xlastkey:
                    colored_message = colored_message  + F.RED + key + ': ' + current_color + value + ', ' + F.RESET
                else:
                    colored_message = colored_message  + F.RESET
        else:
            key = to_u(i)
            value = to_u(cdict[i])
            if highlight == False:
                colored_message = colored_message + F.RED + key + ': ' + current_color + value
            else:
                if (key == 'text') or (key == 'user'):
                    if key == 'text':
                        colored_message = colored_message + F.RED + key + ': ' + F.BLACK + B.WHITE + value
                    if key == 'user':
                        colored_message = colored_message + F.RED + key + ': ' + F.BLACK + B.CYAN + value
                else:
                    colored_message = colored_message + F.RED + key + ': ' + current_color + value
        if i != lastkey:
            colored_message = colored_message  + B.RESET + ', ' + F.RESET
        else:
            colored_message = colored_message  + B.RESET + F.RESET
    colored_message = '{' + to_u(colored_message) + '}'
    return colored_message
