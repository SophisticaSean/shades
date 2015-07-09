import MySQLdb as mdb, MySQLdb.cursors, requests, os, time, json, ast, random, subprocess, re, sys
import MySQLdb.cursors
new_tables = False


rtm_conf_path = '/configs/rtm.config'

temp = open(rtm_conf_path, 'r')
config_lines = temp.readlines()
gif_ct = ast.literal_eval(config_lines[0].replace('\r\n', ''))
channels = ast.literal_eval(config_lines[1].replace('\r\n', ''))
users = ast.literal_eval(config_lines[2])
two_n = ast.literal_eval(config_lines[3])
temp.close()

con = mdb.connect('localhost', os.getenv('dbuser1'), os.getenv('dbuser2'), 'rtm', cursorclass=MySQLdb.cursors.DictCursor)
with con:
    cur = con.cursor()
    #for key, value in two_n.iteritems():
    #   print key, value

    #for key, value in users.iteritems():
    #   slack_id = key
    #   name = value.decode("utf8","ignore")
    #   print slack_id, name
    #   sql = ("INSERT INTO 2n_Teams "
    #       "(Team, N_Number) "
    #       "VALUES(%s, %s)")
    #   cur.execute(sql, (key, value))
    #cur.execute("SELECT * FROM Users WHERE Name LIKE '%sean%'")
    #rows = cur.fetchall()
    #for row in rows:
    #   print row


    if new_tables == True:
        cur.execute("DROP TABLE Users")
        cur.execute("CREATE TABLE Users(Id INT PRIMARY KEY AUTO_INCREMENT, Name VARCHAR(50), Nick VARCHAR(50), Slack_Id VARCHAR(10) UNIQUE KEY)")
        cur.execute("DROP TABLE Channels")
        cur.execute("CREATE TABLE Channels(Id INT PRIMARY KEY AUTO_INCREMENT, Name VARCHAR(50), Slack_Id VARCHAR(10) UNIQUE KEY)")
        cur.execute("DROP TABLE Gif_Whitelist")
        cur.execute("CREATE TABLE Gif_Whitelist(Id INT PRIMARY KEY AUTO_INCREMENT, Channel VARCHAR(50), Slack_Id VARCHAR(10))")
        cur.execute("DROP TABLE 2n_Teams")
        cur.execute("CREATE TABLE 2n_Teams(Id INT PRIMARY KEY AUTO_INCREMENT, Team VARCHAR(50), N_Number INT)")
        cur.execute("DROP TABLE 2n_Nicks")
        cur.execute("CREATE TABLE 2n_Nicks(Id INT PRIMARY KEY AUTO_INCREMENT, Team VARCHAR(50), Nick VARCHAR(50))")
        cur.execute("DROP TABLE Monikers")
        cur.execute("CREATE TABLE Monikers(ID INT PRIMARY KEY AUTO_INCREMENT, Slack_Id VARCHAR(10), Moniker VARCHAR(50), Network VARCHAR(15))")
        cur.execute("DROP TABLE 2n_data")
        cur.execute("CREATE TABLE 2n_data(ID INT PRIMARY KEY AUTO_INCREMENT, Team VARCHAR(50), N_Number INT, Count INT, Date INT)")
        cur.execute("DROP TABLE Tasks")
        cur.execute("CREATE TABLE Tasks(ID INT PRIMARY KEY AUTO_INCREMENT, Command VARCHAR(200), Weekday VARCHAR(10), Hour INT, Min INT)")
        cur.execute("DROP TABLE League")
        cur.execute("CREATE TABLE League(ID INT PRIMARY KEY AUTO_INCREMENT, Slack_Id VARCHAR(10), Name VARCHAR(30), S_ID VARCHAR(30) UNIQUE KEY, Level INT(2), Rank VARCHAR(30)")
    #i = 0
    #while i < 25:
    #   cur.execute("INSERT INTO test(Name) VALUES('Sean %i')" % (i))
    #   i = i + 1
