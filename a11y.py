import requests, os, sys, time

def main():
    """main a11y function"""
    def get_key(item):
        return item[1]

    def ticket_list():
        jiracred = (os.getenv('juser') + ':' + os.getenv('jpass')).encode('base64', 'strict')
        headers = {'Authorization': 'Basic ' + jiracred}

        base = "https://{}.atlassian.net/rest/api/2/search?jql=".format(os.getenv('jiradomain'))
        jql = (base + '(labels%20%3D%20accessibility%20and%20(status%20!%3D%20Closed%20and%20status%20!%3D%20Done)%20and%20project%20!%3D%20"Accessibility%20Testing"%20and%20type%20!%3D%20Epic)&maxResults=1000')
        response = requests.get(jql, headers=headers)
        total = int(response.json()['total'])
        ticket_store = {}
        for item in response.json()['issues']:
            if item['fields']['customfield_10007'] != None:
                sprint_count = len(item['fields']['customfield_10007'])
            else:
                sprint_count = 0
            ticket_store[item['key']] = {'sprint_count': sprint_count, 'team': item['fields']['customfield_12700']['value']}
            #print item['key'], "sprint count: " + str(sprint_count), item['fields']['customfield_12700']['value'], total
            total = total - 1
        return ticket_store

    ticket_store = ticket_list()
    print len(ticket_store)
    temp_arr = []
    for key, value in ticket_store.iteritems():
        if value["sprint_count"] > 1:
            temp_arr.append([key, value["sprint_count"]])
    temp_arr = sorted(temp_arr, key=get_key, reverse=True)
    print "The tickets people _want_ to pretend to care about: \r\n"
    for i in temp_arr:
        print "{}, sprint count: {}, team: ".format(i[0], i[1])
main()
