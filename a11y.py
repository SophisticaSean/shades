import requests, os, sys, time
#import MySQLdb as mdb, MySQLdb.cursors
#import resources as rs

def main():
    """main a11y function"""
    base = "https://{}.atlassian.net/rest/api/2/search?jql=".format(os.getenv('jiradomain'))
    a11y_base_jql = '(labels%20%3D%20accessibility%20and%20(status%20!%3D%20Closed%20and%20status%20!%3D%20Done)%20and%20project%20!%3D%20"Accessibility%20Testing"%20and%20type%20!%3D%20Epic'

    def construct_jql(jql):
        """craft our jql with our known beginning and known end"""
        return base + jql + ')&maxResults=1000'

    def get_key(item):
        return item[1]

    def a11y_json(jql):
        jiracred = (os.getenv('juser') + ':' + os.getenv('jpass')).encode('base64', 'strict')
        headers = {'Authorization': 'Basic ' + jiracred}

        response = requests.get(jql, headers=headers)
        total = int(response.json()['total'])
        return response.json()

    def a11y_list():
        a11y_list_jql = construct_jql(a11y_base_jql)
        json = a11y_json(a11y_list_jql)['issues']
        ticket_store = {}
        for item in json:
            if item['fields']['customfield_10007'] != None:
                sprint_count = len(item['fields']['customfield_10007'])
            else:
                sprint_count = 0
            ticket_store[item['key']] = {'sprint_count': sprint_count, 'team': item['fields']['customfield_12700']['value']}
        return ticket_store

    def priorized_tickets():
        print "useless right now"
        priority_dict = {1: '11163', 2: '11105', 3: '11106'}
        #need to loop thru this and compare the returned issues to the total issues and list out the unprioritized ones

    ticket_store = a11y_list()
    print len(ticket_store)
    temp_arr = []
    for key, value in ticket_store.iteritems():
        if value["sprint_count"] > 1:
            temp_arr.append([key, value["sprint_count"]])
    temp_arr = sorted(temp_arr, key=get_key, reverse=True)
    print "The tickets people _want_ to pretend to care about: \r\n"
    for i in temp_arr:
        print "{}, sprint count: {}".format(i[0], i[1])
main()
