"""gets all tickets associated to the passed team and does maths and reports back to slack"""
import requests, os, sys, time
import MySQLdb as mdb, MySQLdb.cursors
import resources as rs
def main():
    """main function"""
    db_msg = ""
    token = os.getenv('stoken')

    team = str(sys.argv[1])
    n_number = 2*int(sys.argv[2])
    query = str(sys.argv[3])
    channel = str(sys.argv[4])
    stat = str(sys.argv[5])

    def post(channel, message, username, icon_url='', icon_emoji=''):
        """posts a message to a channel (in slack) with the supplied parameters"""
        nurl_temp = ("https://slack.com/api/chat.postMessage?token={}&channel={}"
                     "&text={}&username={}&icon_url={}&icon_emoji={}")
        nurl = nurl_temp.format(token, channel, message, username, icon_url, icon_emoji)
        return requests.get(nurl, timeout=5)

    jiracred = (os.getenv('juser') + ':' + os.getenv('jpass')).encode('base64', 'strict')
    headers = {'Authorization': 'Basic ' + jiracred}
    if query == "None":
        base = "https://{}.atlassian.net/rest/api/2/search?jql=".format(os.getenv('jiradomain'))
        jql = (base + '(status%20%20%3D%20Open%20OR%20status%20%3D%20"In%20Progress"%20OR%20status%20%3'
               'D%20"QA"%20OR%20status%20%3D%20Feedback%20or%20status%20%3D%20"QA%20Ready")'
               '%20AND%20((type%20%3D%20"Support%20Week%'
               '20Task"%20AND%20status%20!%3D%20"QA")%20OR%20type%20%3D%20Bug)%20AND%20("Sprint%'
               '20Team"%20%3D%20%27' + team + '%27)')
        if team == 'admin':
            jql = base + 'filter%20%3D%20"Admin%202n%20Bugs"'
        if team == 'bridge':
            jql = base + "project%20in%20(ASH%2C%20BR)%20and%20issuetype%20%3D%20bug%20and%20status%20!%3D%20Closed"
        if team == 'ios':
            jql = base + "(issuetype%20%3D%20Bug%20OR%20issuetype%20%3D%20'Support%20Week%20Task')%20AND%20status%20!%3D%20Closed%20AND%20('Sprint%20Team'%20%3D%20%27ios%27)"
        if team == 'android':
            jql = base + "(issuetype%20%3D%20Bug%20OR%20issuetype%20%3D%20'Support%20Week%20Task')%20AND%20status%20!%3D%20Closed%20AND%20('Sprint%20Team'%20%3D%20%27android%27)"
    else:
        jql = query
    rs.msg_sean(str(jql), token)
    response = requests.get(jql, headers=headers)
    try:
        ticket_count = float(response.json()[u'total'])
        n_diff = ticket_count - n_number
        n_percentage = round((n_diff/n_number) * 100, 2)
        n_ratio = round(ticket_count/(n_number/2), 2)
        if stat == "True":
            con = mdb.connect('localhost', os.getenv('dbuser1'), os.getenv('dbpass1'), 'rtm',
                              cursorclass=MySQLdb.cursors.DictCursor)
            cur = con.cursor()

            now = time.time()
            sql = ("INSERT INTO 2n_data (Team, N_number, Count, Date) "
                   "VALUES('{}', '{}', '{}', '{}')").format(team, n_number, ticket_count, now)
            cur.execute(sql)
            con.commit()
            db_msg = "\r\nSuccessfully added this team and their 2n number to the db for today."
        if n_diff > 0:
            message = ("{} has {}/{} tickets that count towards 2n. "
                       "That's {}% over 2n with an N ratio of {}n.")
            message = message.format(team, int(ticket_count), n_number, n_percentage, n_ratio)
        else:
            message = "{} has {}/{} tickets that count towards 2n."
            message = message.format(team, int(ticket_count), str(n_number))
        post(channel, message + db_msg, 'shades McGee', icon_emoji=':shadesmcgee:')
    except KeyError:
        message = ("Looks like JIRA doesn't have {} as a sprint team,"
                   "please add your team to the sprint team field.")
        message = message.format(team)
        post(channel, message, 'shades McGee', icon_emoji=':shadesmcgee:')
    except Exception, e:
        message = "Oops, something went wrong. If this persists, please contact @slewis. \n" + e
        post(channel, message, 'shades McGee', icon_emoji=':shadesmcgee:')

main()
