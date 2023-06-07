#!/usr/bin/env python3

import scratchattach as scratch3
import openai
import time
import math

with open("username", "r") as file:
    username = file.read().rstrip()
with open("password", "r") as file:
    password = file.read().rstrip()
with open("project_id", "r") as file:
    project_id = file.read().rstrip()
with open("api_key", "r") as file:
    api_key = file.read().rstrip()

openai.api_key = api_key
#print(openai.Completion.create(
#    #model="gpt-3.5-turbo",
#    model="text-davinci-003",
#    prompt="Find the next number in this sequence: 2, 3, 5, 7, 11, 13, 17",
#    temperature=0.6
#))
#print(openai.ChatCompletion.create(
#    model="gpt-3.5-turbo",
#    messages=[
#        { "role": "system", "content": "You are a helpful AI assistant." },
#        { "role": "user", "content": "In Scratch, how can I make a program run multiple times?" },
#    ],
#    temperature=0.6
#))
#exit()

events = scratch3.CloudEvents(project_id)
session = scratch3.login(username, password)
conn = session.connect_cloud(project_id)

charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + \
          "!@#$%^&*()-_+=[]{}\\|;':\",./<>?`~ "

users = {}

# Time stamps are in milliseconds
start_time = math.floor(time.time() * 1000)
past_msgs = set()

def encode(string):
    ret = ""
    for c in string:
        ret += str(charset.find(c) + 1).zfill(2)
    return ret

@events.event
def on_set(event):
    if event.var != "sender":
        return
    print("Sender changed!")
    if event.timestamp < start_time:
        return
    print("It's new!")
    # We need this because past changes can call on_set again
    if event.timestamp in past_msgs:
        return
    print("It's unique!")
    print(event.value)
    past_msgs.add(event.timestamp)
    message_id = event.value[0:10]
    user_id = int(message_id[0:6])
    question_num = int(message_id[7:10])
    decoded = ""
    for i in range(len(message_id), len(event.value), 2):
        decoded += charset[int(event.value[i:i+2])-1]

    print(decoded)
    print(user_id, question_num)

    if question_num == 0:
        users[user_id] = [
            { "role": "system", "content": "You are a helpful AI assistant.  Responses should contain only characters from a standard US QWERTY keyboard and should not contain any newline characters."}
        ]
    elif not user_id in users:
        print("Unknown user %s" % user_id)
        return
    users[user_id].append({ "role": "user", "content": decoded })
    response_json = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=users[user_id],
        temperature=0.6
    )
    print(response_json)
    users[user_id].append(response_json["choices"][0]["message"])
    response = response_json["choices"][0]["message"]["content"]

    # Scratch has a limit of 256 characters per cloud variable :(
    conn.set_var("receiver", (message_id + encode(response))[0:256])

events.start()
