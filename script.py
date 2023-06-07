import json
import csv
import datetime
import operator

# for each conversation
file = open('dataExport/conversations.json')
conversationsJSON = json.load(file)
conversationsJSON = sorted(conversationsJSON, key=operator.itemgetter('create_time'))

def printFormat(mapping, node_id, num_spaces):
    authorInfo = mapping[node_id]['message']['author']['role']
    authorString = "USER" if authorInfo == "user" else "GPT" if authorInfo == "assistant" else "SYSTEM_ROOT"
    # print((" " * num_spaces) + " - " + messageAuthor + node_id)
    print(f"{' ' * num_spaces}- {authorString} {node_id}")

# root_id: id field of the root node
def depth_first(mapping, node_id, level):
    # if mapping[node_id]['children']:
    printFormat(mapping, node_id, level * 2)
    for child in mapping[node_id]['children']:
        # printFormat(mapping, child, level * 2)
        depth_first(mapping, child, level + 1)


# the structure of the tree goes
#           root
#             |
#           system
#            /  \
#    prompt v1    prompt v2
def get_system_node_id(conversation):
    system_node_id = None
    for chat in conversation['mapping'].values():
        try:
            # print(chat['message']['author']['role'])
            if chat['message']['author']['role'] == "system":
                system_node_id = chat['id']
        except:
            pass
    
    if not system_node_id:
        raise ValueError('System node (root) not found in conversation data. Program does not know the root and cannot proceed.')

    # print(system_node_id)
    return system_node_id
    # iterCount = 0


def main():
    for conversation in conversationsJSON[:1]:
        conversationTitle = conversation['title']
        conversationCreateTime = datetime.datetime.utcfromtimestamp(conversation['create_time']).strftime('%Y-%m-%d %H:%M:%S')

        csvTitle = conversationCreateTime + ' ' + conversationTitle
        print(csvTitle)
        system_node_id = get_system_node_id(conversation)
        depth_first(conversation['mapping'], system_node_id, 0)

        # do a DFS of the tree



    # # open the file in the write mode
    # with open('result.csv', 'w') as f:
    #     # create the csv writer
    #     writer = csv.writer(f)

    #     # write a row to the csv file
    #     writer.writerow(["Hello"])

if __name__ == "__main__":
    main()