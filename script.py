import json
import csv
import datetime
import operator
import sys
import os

def printE(string=""):
    # printE outputs to a README file,
    # and so this function cannot be used until we know what the
    # data folder is called so we can name this README file properly
    assert(folder_name is not None)
    with open(README_NAME, 'a') as f:
        print(string, file=f)
    # print(string)

def getAuthorString(chat):
    authorInfo = chat['message']['author']['role']
    return "user" if authorInfo == "user" else "GPT" if authorInfo == "assistant" else "SYSTEM"


def printFormat(mapping, node_id, level, target=None, toConsole=False):
    num_spaces = level * 2
    authorString = getAuthorString(mapping[node_id])
    endChar = ""
    if target and node_id == target:
        endChar = "     *"
    if toConsole:
        print(f"{' ' * num_spaces}- {authorString} {node_id}{endChar}")
    else:
        printE(f"{' ' * num_spaces}- {authorString} {node_id}{endChar}")


# root_id: id field of the root node
def depth_first(mapping, node_id, index, level, write, writer, feedback, comparison_feedback):
    printFormat(mapping, node_id, level)
    write(writer, mapping[node_id], feedback, comparison_feedback, level, index)
    for index, child in enumerate(mapping[node_id]['children']):
        depth_first(mapping, child, index, level + 1, write, writer, feedback, comparison_feedback)


def depth_first_print_only(mapping, node_id, index, level, target=None):
    printFormat(mapping, node_id, level, target=target, toConsole=True)
    for index, child in enumerate(mapping[node_id]['children']):
        depth_first_print_only(mapping, child, index, level + 1, target=target)


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


csv_header_columns = ['message_id', 'author', 'level_indicator', 'lvl', 'create_time', 'rating', 'tags', 'text_feedback', 'is_original_message', 'comparison_type', 'comparison_choice', 'message_contents', 'parent', 'children']
def write_message_to_csv(writer, chat, feedbackObject, comparisonFeedbackObject, level, index):
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
    comparisonFeedback = comparisonFeedbackObject.get(chat['id'])
    comparisonType = comparisonFeedback['comparison_type'] if comparisonFeedback else ""
    comparisonChoice = comparisonFeedback['choice'] if comparisonFeedback else ""

    parent = chat['parent']
    children = chat['children']

    writer.writerow([chat['id'], author, level_indicator, level, create_time, rating, tags, text_feedback, is_original_message, comparisonType, comparisonChoice, message_contents, parent, children])


def get_UTC_timestamp(epoch_time):
    return datetime.datetime.utcfromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')


def get_comparison_feedback(conversation_id):
    comparisonDict = {}
    for comparison in comparisonFeedbackJSON:
        if comparison['input']['conversation_id'] == conversation_id:
            relevant_message_id = comparison['output']['feedback_step_2']['new_turn'][0]['id']

            if comparison['output']['feedback_step_2']['new_completion_placement'] == "not-applicable":
                # this means a response was regenerated using the "Regenerate response" button
                # This feedback is the dialogue box on ChatGPT after pressing regenerate
                # Where it asks Was this response better or worse? (or same)
                comparison_type = 'regen'
                feedback_translation = {
                    "new": "better",
                    "original": "worse",
                    "same": "same"
                }

            else:
                # this means that the user has the pairwise comparison interface in front of them
                # where they can see both responses and choose which one they prefer (or if they prefer neither)
                comparison_type = 'pairwise'
                feedback_translation = {
                    "new": "preferred this",
                    "original": "preferred original",
                    "same": "preferred neither"
                }

            comparisonDict[relevant_message_id]= {
                'comparison_type': comparison_type,
                'choice': feedback_translation[comparison['output']['feedback_step_2']['completion_comparison_rating']]
            }
    return comparisonDict


# returns a dictionary containing the feedback for this conversation
# key: a message id
# value: feedback for the corresponding message
def get_conversation_feedback(conversation_id):
    feedbackDict = {}
    for feedback in messageFeedbackJSON:
        if feedback['conversation_id'] == conversation_id:
            feedbackDict[feedback['id']] = feedback
    return feedbackDict

def get_conversation(conversation_id):
    for conversation in conversationsJSON:
        if conversation['id'] == conversation_id:
            return conversation
    return None


# removes backslashes and dots to avoid python open() command when writing
def format_output_conversation_title(conversation_title):
    return conversation_title.replace("/", "-")


def deserialize(folder_path):
    global conversationsJSON
    global messageFeedbackJSON
    global comparisonFeedbackJSON

    conversationsFile = open(f'{folder_path}/conversations.json')
    conversationsJSON = json.load(conversationsFile)
    conversationsJSON = sorted(conversationsJSON, key=operator.itemgetter('create_time'))

    messageFeedbackFile = open(f'{folder_path}/message_feedback.json')
    messageFeedbackJSON = json.load(messageFeedbackFile)
    messageFeedbackJSON = sorted(messageFeedbackJSON, key=operator.itemgetter('create_time'))

    comparisonFeedbackFile = open(f'{folder_path}/model_comparisons.json')
    comparisonFeedbackJSON = json.load(comparisonFeedbackFile)
    comparisonFeedbackJSON = sorted(comparisonFeedbackJSON, key=operator.itemgetter('create_time'))

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

    padded_lines = [f'│ {line.ljust(max_length).rjust(box_width - 2)} │' for line in lines]
    box_middle = '\n'.join(padded_lines)

    ascii_box = '\n'.join([box_top, box_middle, box_bottom])
    return ascii_box

def prompt_user_input():
    print(create_ascii_box('CONSOLE'))
    print(create_description_box('Use the console to obtain\ninformation about an object via its id.'))
    print("––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––")
    print()

    while True:
        user_input = input("Enter a (conversation/message) id: ")
        if user_input.lower() == 'exit' or user_input.lower() == 'quit':
            break
        print_reference(user_input)

def get_reference(reference_id):
    return references.get(reference_id, None)


def print_reference(reference_id):
    ref = get_reference(reference_id)
    if not ref:
        print('id is not valid!')
    else:
        conv = get_conversation(ref[0])
        if ref[1] == 'conversation':
            print(create_ascii_box(f'Conversation - {conv["title"]}'))
        print(create_ascii_box(reference_id))
        print(create_ascii_box(f'type: {ref[1]}'))
        system_node_id = get_system_node_id(conv)
        if ref[1] != 'conversation':
            print(create_ascii_box(f'author: {getAuthorString(conv["mapping"][reference_id])}'))
            print(create_ascii_box(f'In conversation: {conv["title"]} {ref[0]}'))
            parent = conv["mapping"][reference_id]["parent"]
            print(create_ascii_box(f'Parent: {parent}'))
            children = conv["mapping"][reference_id]["children"] if conv["mapping"][reference_id]["children"] else "None"
            print(create_ascii_box(f'Children:'))
            if type(children) == list:
                for child in children:
                    print(f'    {child}')
            else:
                print('    None')
        print(create_ascii_box('Tree: '))
        depth_first_print_only(conv["mapping"], system_node_id, 0, 0, target=reference_id)
    print()
    print("––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––")


def main(folder_path):
    # Your main program logic here
    if not os.path.isdir(folder_path):
        print("Invalid folder path!")
        sys.exit(1)

    print()
    print("Working...")

    global folder_name
    folder_name = os.path.basename(folder_path)
    global README_NAME
    README_NAME = f'README_{folder_name}.txt'

    printE("This file contains an overview of all conversations in the target directory.")
    printE()

    deserialize(folder_path)
    
    # global dictionary
    # key: a conversation/message/feedback id
    # value: the conversation where the id is contained
    global references
    references = {}

    for conversation in conversationsJSON:
        conversationTitle = conversation['title']
        conversationCreateTime = get_UTC_timestamp(conversation['create_time'])
        conversationID = conversation['id']

        references[conversation['id']] = (conversation['id'], 'conversation')
        references.update({chat_id: (conversation['id'], 'chat') for chat_id in conversation['mapping']})

        feedback = get_conversation_feedback(conversationID)
        comparison_feedback = get_comparison_feedback(conversationID)

        printTitle = f'CONVERSATION {conversationCreateTime} {conversationTitle} {conversationID}'
        csvTitle = f'{conversationCreateTime}_{conversationID}_{format_output_conversation_title(conversationTitle)}.csv'

        printE(printTitle)
        system_node_id = get_system_node_id(conversation)

        OUTPUT_DIR = f"output_{folder_name}"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(f'{OUTPUT_DIR}/{csvTitle}', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(csv_header_columns)
            depth_first(conversation['mapping'], system_node_id, 0, 0, write_message_to_csv, writer, feedback, comparison_feedback)

        printE()

    print("CSV creation finished.")
    print()
    print(f"An overview of the data has been output to a file: '{README_NAME}'")
    print()
    prompt_user_input()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python [script_name].py [folder_path]")
        print("folder_path: path to a ChatGPT data export directory")
        sys.exit(1)

    folder_path = sys.argv[1]
    main(folder_path)