import json
import csv
import datetime
import operator


conversationsFile = open('dataExport/conversations.json')
conversationsJSON = json.load(conversationsFile)
conversationsJSON = sorted(conversationsJSON, key=operator.itemgetter('create_time'))

messageFeedbackFile = open('dataExport/message_feedback.json')
messageFeedbackJSON = json.load(messageFeedbackFile)
messageFeedbackJSON = sorted(messageFeedbackJSON, key=operator.itemgetter('create_time'))

def getAuthorString(chat):
    authorInfo = chat['message']['author']['role']
    return "user" if authorInfo == "user" else "GPT" if authorInfo == "assistant" else "SYSTEM_ROOT"

def printFormat(mapping, node_id, level):
    num_spaces = level * 2
    authorString = getAuthorString(mapping[node_id])
    # print((" " * num_spaces) + " - " + messageAuthor + node_id)
    print(f"{' ' * num_spaces}- {authorString} {node_id}")

# root_id: id field of the root node
def depth_first(mapping, node_id, index, level, write, writer, feedback):
    printFormat(mapping, node_id, level)
    write(writer, mapping[node_id], feedback, index)
    for index, child in enumerate(mapping[node_id]['children']):
        depth_first(mapping, child, index, level + 1, write, writer, feedback)


# the structure of the tree goes
#           root
#             |
#           system
#            /  \
#   prompt v1    prompt v2
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

def write_message_to_csv(writer, chat, feedbackObject, index):
    # message_contents = [part for part in chat['message']['content']['parts']] if len(chat['message']['content']['parts']) > 1 else chat['message']['content']['parts'][0]
    create_time = get_UTC_timestamp(chat['message']['create_time'])
    author = getAuthorString(chat)
    feedback = feedbackObject.get(chat['id'])
    rating = feedback.get('rating', "") if feedback else ""
    contentString = feedback.get('content', "") if feedback else None
    contentObject = json.loads(contentString) if contentString else None
    tags = contentObject.get('tags', "") if contentObject else ""
    is_original_message = False if index else True

    writer.writerow([chat['id'], author, create_time, rating, tags, is_original_message])

def get_UTC_timestamp(epoch_time):
    return datetime.datetime.utcfromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')

csv_header_columns = ['message_id', 'author', 'create_time', 'rating', 'tags', 'is_original_message']

# returns a dictionary containing the feedback for this conversation
# key: a message id
# value: feedback for the corresponding message
def get_conversation_feedback(conversation_id):
    feedbackDict = {}
    for feedback in messageFeedbackJSON:
        if feedback['conversation_id'] == conversation_id:
            feedbackDict[feedback['id']] = feedback
    return feedbackDict

def main():
    for conversation in conversationsJSON:
        conversationTitle = conversation['title']
        conversationCreateTime = get_UTC_timestamp(conversation['create_time'])
        conversationID = conversation['id']

        feedback = get_conversation_feedback(conversationID)

        csvTitle = conversationCreateTime + ' ' + conversationTitle + ' ' + conversationID
        print(csvTitle)
        system_node_id = get_system_node_id(conversation)

        # open the file in the write mode
        with open(f'{conversationTitle}_{conversationID}.csv', 'w') as f:
            # create the csv writer
            writer = csv.writer(f)

            writer.writerow(csv_header_columns)
            # write a row to the csv file
            # writer.writerow(["Hello"])
            depth_first(conversation['mapping'], system_node_id, 0, 0, write_message_to_csv, writer, feedback)

if __name__ == "__main__":
    main()