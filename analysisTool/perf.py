import json
import os
import sys

def get_dependency (webpage):
    #get webpage from commmand line arguments
    # webpage = sys.argv[1] 
    webpage = webpage.replace("/","")

    #appends http to webpage if not present as a failsafe, hopefully won't have to
    if (webpage[:4] != "http"):
        webpage = "http://" + webpage

    print ("DEPENDENCY WEBPAGE", webpage)

    if os.system("node perf.js " + webpage):
        raise RuntimeError("couldnt execute script")

    split_webpage = webpage.split(".")

    #open trace.json file
    json_file = split_webpage[1] + "trace.json"
    with open(json_file, "r") as traces:
        data = json.load(traces)

    nodesList = []

    #parse file and get trace data pertaining to javascript and functions
    for i in data['traceEvents']:
        #profile/stack trace
        if i['name'] == "ProfileChunk":
            #actual data with parents and children stored in nodes, can be used to build a call tree
            if 'nodes' in i['args']['data']['cpuProfile']:
                for j in i['args']['data']['cpuProfile']['nodes']:
                    nodesList.append(j)
                    # print (j)


    dependecies = []
    index = 0
    #all the nodes/list access is O(1), index of list is given by ID, use ID
    for i in reversed(nodesList):
        if (i['id'] == 1):
            # print("root")
            continue
        else:
            # print (i)
            #check first 4 characters to see if it matches http --> implies non-native function
            if ('url' in i['callFrame'] and i['callFrame']['url'][:4] == "http"):
                #parent isn't 0 indexed
                index = i['parent'] - 1

                #skip nodes with root as parent
                if index == 0:
                    continue

                #CALLED SCRIPT, --LIST OF CALLING SCRIPTS
                #check first 4 characters to see if it matches http --> implies non-native function
                # if nodesList[index]['callFrame']['url'][:4] == "http":
                #     #check if urls are different...
                #     if i['callFrame']['url'] != nodesList[index]['callFrame']['url']:
                #         #if not key not in dependencies dictionary
                #         if i['callFrame']['url'] not in dependecies:
                #             #add to dictionary, key: called script, value: list of calling scripts
                #             dependecies[i['callFrame']['url']] = [nodesList[index]['callFrame']['url']]
                #         else:
                #             #only add to dictionary if not in dictonary already
                #             if (nodesList[index]['callFrame']['url'] not in dependecies[i['callFrame']['url']]):
                #                 dependecies[i['callFrame']['url']].append(nodesList[index]['callFrame']['url'])

                #CALLING SCRIPT, --LIST OF CALLED SCRIPTS
                try:
                    if nodesList[index]['callFrame']['url'][:4] == "http":
                        #check if urls are different...
                        if ('url' in nodesList[index]['callFrame'] and i['callFrame']['url'] != nodesList[index]['callFrame']['url']):
                            #if not key not in dependencies dictionary
                            if (nodesList[index]['callFrame']['url'], i['callFrame']['url']) not in dependecies:
                                #tuples of calling, called pairs
                                dependecies.append((nodesList[index]['callFrame']['url'], i['callFrame']['url']))
                                #add to dictionary, key: calling script, value: list of called scripts
                                # dependecies[nodesList[index]['callFrame']['url']] = [i['callFrame']['url']]
                            # else:
                            #     #only add to dictionary if not in dictonary already
                            #     if (i['callFrame']['url'] not in dependecies[nodesList[index]['callFrame']['url']]):
                            #         dependecies[nodesList[index]['callFrame']['url']].append(i['callFrame']['url'])
                except:
                    continue



    # print (dependecies)

    dep_matrix = []

    temp = []

    cnt = 0
    for d in dependecies:
        cnt += 1
        tmp = []

        if ".js" not in d[0] or ".js" not in d[1]:
            continue

        # name1 = d[0].split("/")[-1].split("?")[0]
        # name2 = d[1].split("/")[-1].split("?")[0]
        name1 = d[0]
        name2 = d[1]
        found = False

        # print ("1", cnt, dep_matrix)

        for a in dep_matrix:  
            # print (name1, name2, a)              
            if name1 in a:
                found = True
                if name2 not in a and name2 not in temp:
                    a.append(name2)
                    temp.append(name2)
                break
            elif name2 in a:
                found = True
                if name1 not in a and name1 not in temp:
                    a.append(name1)
                    temp.append(name1)
                break

        if not found and name1 not in temp and name2 not in temp:
            tmp.append(name1)
            tmp.append(name2)
            temp.append(name1)
            temp.append(name2)
            dep_matrix.append(tmp)

        # print ("2", cnt, dep_matrix) 

    for a in dep_matrix:
        print (a)

    return dep_matrix
# for i in dependecies:
#     print (i)
    
#     for j in dependecies[i]:
#         print ("\t--", j)


# from treelib import Tree, Node
# tree = Tree()

# uniqueNodes = []
# ids = []

# for i in nodesList:
#     if (i['id'] == 1):
#         uniqueNodes.append(i)
#         ids.append(i['id'])
#         continue
#     else:
#         pIndex = i['parent'] - 1

#         #parent is root
#         if pIndex == 0:
#             continue
        
#         #for other parents
#         if ('url' not in nodesList[pIndex]['callFrame'] and 'url' not in i['callFrame']):
#             uniqueNodes.append(i)
#             ids.append(i['id'])

#         if ('url' in i['callFrame'] and 'url' not in nodesList[pIndex]['callFrame']):
#             uniqueNodes.append(i)
#             ids.append(i['id'])

#         if ('url' in i['callFrame'] and 'url' in nodesList[pIndex]['callFrame']):
#             if (i['callFrame']['url'] != nodesList[pIndex]['callFrame']['url']):
#                 uniqueNodes.append(i)
#                 ids.append(i['id'])

#         if ('url' in nodesList[pIndex]['callFrame'] and 'url' not in i['callFrame']):
#             uniqueNodes.append(i)
#             ids.append(i['id'])


# print (uniqueNodes)
# print (ids)

# def find_ancestor(i, nodes, ids):
#     if i['parent'] not in ids:
#         ancestor = nodes[i['parent'] - 1]
        
#         if (ancestor['id'] not in ids):
#             return (find_ancestor(ancestor, nodes, ids))
#         else:
#             return ancestor['id']
#     else:
#         return i['parent']


# for i in uniqueNodes:
#     if (i['id'] == 1):
#         tree.create_node("Root", i['id'])
#     else:
#         if 'url' not in i['callFrame'] or i['callFrame']['url'][:4] != "http":
#             parent = find_ancestor(i, nodesList, ids)
#             tree.create_node("Native", i['id'], parent=parent)
#         else: 
#             scriptName = i['callFrame']['url'].split("/")[-1]
            
#             if scriptName == '':
#                 scriptName = i['callFrame']['url']
            
#             parent = find_ancestor(i, nodesList, ids)
#             tree.create_node(scriptName, i['id'], parent=parent)            
# tree.show()
