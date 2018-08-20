import json

# Purpose
# The purpose of this task is to find bots inside huge log file.
# Lots of bots logged in to our service. They all do same thing very quickly: they log in, change password and log off; all of these actions are establishing within one second. Our task is to find them in log file.
# Please write command that will show all profiles meeting following criteria:
# - user logged in, user changed password, user logged off within same second (all 3 actions have to be done within 1 second);
# - those actions (log in, change password, log off) happened one after another with no other entires in between.

logs="""Mon, 22 Aug 2016 13:15:39 +0200|178.57.66.225|fxsciaqulmlk| - |user logged in| -
Mon, 22 Aug 2016 13:15:39 +0200|178.57.66.225|fxsciaqulmlk| - |user changed password| -
Mon, 22 Aug 2016 13:15:39 +0200|178.57.66.225|fxsciaqulmlk| - |user logged off| -
Mon, 22 Aug 2016 13:15:42 +0200|178.57.66.225|faaaaaa11111| - |user logged in| -
Mon, 22 Aug 2016 13:15:40 +0200|178.57.66.215|terdsfsdfsdf| - |user logged in| -
Mon, 22 Aug 2016 13:15:49 +0200|178.57.66.215|terdsfsdfsdf| - |user changed password| -
Mon, 22 Aug 2016 13:15:49 +0200|178.57.66.215|terdsfsdfsdf| - |user logged off| -
Mon, 22 Aug 2016 13:15:59 +0200|178.57.66.205|erdsfsdfsdf| - |user logged in| -
Mon, 22 Aug 2016 13:15:59 +0200|178.57.66.205|erdsfsdfsdf| - |user logged in| -
Mon, 22 Aug 2016 13:15:59 +0200|178.57.66.205|erdsfsdfsdf| - |user changed password| -
Mon, 22 Aug 2016 13:15:59 +0200|178.57.66.205|erdsfsdfsdf| - |user logged off| -
Mon, 22 Aug 2016 13:17:50 +0200|178.57.66.205|abcbbabab| - |user logged in| -
Mon, 22 Aug 2016 13:17:50 +0200|178.57.66.205|abcbbabab| - |user changed password| -
Mon, 22 Aug 2016 13:17:50 +0200|178.57.66.205|abcbbabab| - |user changed profile| -
Mon, 22 Aug 2016 13:17:50 +0200|178.57.66.205|abcbbabab| - |user logged off| -
Mon, 22 Aug 2016 13:19:19 +0200|178.56.66.225|fxsciaqulmla| - |user logged in| -
Mon, 22 Aug 2016 13:19:19 +0200|178.56.66.225|fxsciaqulmla| - |user changed password| -
Mon, 22 Aug 2016 13:17:50 +0200|178.57.66.205|abcbbabab| - |user changed profile| -
Mon, 22 Aug 2016 13:19:19 +0200|178.56.66.225|fxsciaqulmla| - |user logged off| -
Mon, 22 Aug 2016 13:20:42 +0200|178.57.67.225|faaaa0a11111| - |user logged in| -
"""
content = []

for line in logs.splitlines():
    content.append(line)
results = {}

#read the logs
for i in content:
    try:
        user = i.split('|')[2]
    except:
        pass
        
    if user not in results:
        results[user] = []
        
    results[user].append(i)

#Regroup by user
print json.dumps(results, indent=4)


nodes = {}

nodes["user logged in"] = "N1"
nodes["user changed password"] = "N2"
nodes["user logged off"] = "N3"

paths = [] 

paths.append(("N1","N2"))
paths.append(("N2","N2"))
paths.append(("N2","N3"))


def is_path_detected(left, right):
    
    result = False
    
    if (left, right) in paths:
        result = True
    
    return result

bots_suspect = []

for user, logs in results.iteritems():
    
    print ".. Detecting user %s" % user

    index = -1
    size = len(logs)
    
    is_ok_continue = True
    
    while is_ok_continue:
        
        index = index + 1
        
        is_login_detected = False
        is_changepassword_detected = False
        is_logout_detected = False
        
        for i in range(index, size):
            
            try:
                
                current_log = logs[i]
                next_log = logs[i+1]
                
                #print "------------------------"
                #print "+%s" % current_log
                #print "+%s\n" % next_log
                
                current_node = nodes[current_log.split("|")[4]]
                next_node = nodes[next_log.split("|")[4]]
                    
                if current_node == "N1":
                    is_login_detected = True
                    
                if current_node == "N2":
                    is_changepassword_detected = True
                
                if next_node == "N3":
                    is_logout_detected = True
                
                is_valid = is_path_detected(current_node, next_node)
                
                if is_valid:
                    if is_login_detected and is_changepassword_detected and is_logout_detected:
                        
                        print "...... %s -> is a suspected bot\n" % user
                        
                        bots_suspect.append(user)
                        
                        is_ok_continue = False
                        
                        break

            except:
                    pass
                    
        if index == size:
            is_ok_continue = False               
                 
keywords = ["user logged in", "user changed password","user logged off"]

for key, val in results.iteritems():

    temp = {}

    for k in keywords:
        temp[k] = []

    if key in bots_suspect:
        
        for entry in val:
            token = entry.split('|')
            date = token[0]
            command = token[4]

            for j in keywords:
                if command.find(j) > -1:
                    temp[j].append(date)
        
    results[key] = temp


print "Rewrite Bots..."
print json.dumps(results, indent=4)

print "\n\n"
print "++++++++++++++++++++++++"
print "Detected bots users"
print "++++++++++++++++++++++++"

for user, val in results.iteritems():

    values = list(set(val[keywords[0]]))

    temp = {}

    if len(values) > 0:
        for date in values:
            if date in val[keywords[1]] and date in val[keywords[2]]:
                if user not in temp:
                    temp[user] = []
                
                temp[user].append(date)
            
    
        for u, d in temp.iteritems():
            actions = " , ".join(keywords)
            dates = " and ".join(d)
        
            
            print  "bot user: %s" %(u)
            print  "time attack: %s" %(dates)
            print "actions: %s" %(actions)        
            print "----------------"
    
