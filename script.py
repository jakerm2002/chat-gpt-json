import json
import csv
import datetime
import operator
import sys
import os


def getAuthorString(chat):
    authorInfo = chat['message']['author']['role']
    return "user" if authorInfo == "user" else "GPT" if authorInfo == "assistant" else "SYSTEM"


def printFormat(mapping, node_id, level):
    num_spaces = level * 2
    authorString = getAuthorString(mapping[node_id])
    print(f"{' ' * num_spaces}- {authorString} {node_id}")


# root_id: id field of the root node
def depth_first(mapping, node_id, index, level, write, writer, feedback):
    printFormat(mapping, node_id, level)
    write(writer, mapping[node_id], feedback, level, index)
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
            if chat['message']['author']['role'] == "system":
                system_node_id = chat['id']
        except:
            pass
    if not system_node_id:
        raise ValueError('System node not found in conversation data. Program does not know the children and cannot proceed.')
    return system_node_id


def get_level_indicator(level):
    num_spaces = level * 2
    # return f"{'x' * level}"
    return f"{'  ' * num_spaces}x"


csv_header_columns = ['message_id', 'author', 'level_indicator', 'lvl', 'create_time', 'rating', 'tags', 'text_feedback', 'is_original_message', 'message_contents', 'parent', 'children']
def write_message_to_csv(writer, chat, feedbackObject, level, index):
    message_contents = [part for part in chat['message']['content']['parts']] if len(chat['message']['content']['parts']) > 1 else chat['message']['content']['parts'][0]
    create_time = get_UTC_timestamp(chat['message']['create_time'])
    author = getAuthorString(chat)
    level_indicator = get_level_indicator(level)
    feedback = feedbackObject.get(chat['id'])
    rating = feedback.get('rating', "") if feedback else ""
    fb_content_string = feedback.get('content', "") if feedback else None
    fb_content_object = json.loads(fb_content_string) if fb_content_string else None
    tags = fb_content_object.get('tags', "") if fb_content_object else ""
    text_feedback = fb_content_object.get('text', "") if fb_content_object else ""
    is_original_message = False if index else True
    parent = chat['parent']
    children = chat['children']

    writer.writerow([chat['id'], author, level_indicator, level, create_time, rating, tags, text_feedback, is_original_message, message_contents, parent, children])


def get_UTC_timestamp(epoch_time):
    return datetime.datetime.utcfromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')


# returns a dictionary containing the feedback for this conversation
# key: a message id
# value: feedback for the corresponding message
def get_conversation_feedback(conversation_id):
    feedbackDict = {}
    for feedback in messageFeedbackJSON:
        if feedback['conversation_id'] == conversation_id:
            feedbackDict[feedback['id']] = feedback
    return feedbackDict


# removes backslashes and dots to avoid python open() command when writing
def format_output_conversation_title(conversation_title):
    return conversation_title.replace("/", "-")


def deserialize(folder_path):
    global conversationsJSON
    global messageFeedbackJSON

    conversationsFile = open(f'{folder_path}/conversations.json')
    conversationsJSON = json.load(conversationsFile)
    conversationsJSON = sorted(conversationsJSON, key=operator.itemgetter('create_time'))

    messageFeedbackFile = open(f'{folder_path}/message_feedback.json')
    messageFeedbackJSON = json.load(messageFeedbackFile)
    messageFeedbackJSON = sorted(messageFeedbackJSON, key=operator.itemgetter('create_time'))

def create_ascii_box(word):
    box_width = len(word) + 4  # Width of the box including padding
    horizontal_line = '─' * box_width

    box_top = f'╭{horizontal_line}╮'
    box_middle = f'│  {word}  │'
    box_bottom = f'╰{horizontal_line}╯'

    ascii_box = '\n'.join([box_top, box_middle, box_bottom])
    return ascii_box

def create_description_box(text):
    lines = text.split('\n')
    max_length = max(len(line) for line in lines)
    box_width = max_length + 4  # Width of the box including padding
    horizontal_line = '─' * box_width

    box_top = f'╭{horizontal_line}╮'
    box_bottom = f'╰{horizontal_line}╯'

    padded_lines = [f'│ {line.ljust(max_length)} │' for line in lines]
    box_middle = '\n'.join(padded_lines)

    ascii_box = '\n'.join([box_top, box_middle, box_bottom])
    return ascii_box

def prompt_user_input():
    print(create_ascii_box('CONSOLE'))
    print(create_description_box('Use the console to obtain\ninformation about an object via its id.'))
    user_input = input("Enter a conversation id:")

def main(folder_path):
    # Your main program logic here
    if not os.path.isdir(folder_path):
        print("Invalid folder path!")
        sys.exit(1)

    folder_name = os.path.basename(folder_path)

    deserialize(folder_path)

    for conversation in conversationsJSON:
        conversationTitle = conversation['title']
        conversationCreateTime = get_UTC_timestamp(conversation['create_time'])
        conversationID = conversation['id']

        feedback = get_conversation_feedback(conversationID)

        printTitle = f'CONVERSATION {conversationCreateTime} {conversationTitle} {conversationID}'
        csvTitle = f'{conversationCreateTime}_{conversationID}_{format_output_conversation_title(conversationTitle)}.csv'

        print(printTitle)
        system_node_id = get_system_node_id(conversation)

        with open(csvTitle, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(csv_header_columns)
            depth_first(conversation['mapping'], system_node_id, 0, 0, write_message_to_csv, writer, feedback)

        print()
        prompt_user_input()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python [script_name].py [folder_path]")
        print("folder_path: path to a ChatGPT data export directory")
        sys.exit(1)

    folder_path = sys.argv[1]
    main(folder_path)