# telegram-bot-helper
Some utils to ease the connection with Telegram bot API

They include a TelegramAPIHelper class that will help you to manage retrieving and sending messages through the Telegram API. A Emoji class that should (when added more) give you a easy way to send emoticons. And a MessageProcessor/Job classes that will help you to handle some common bot answering.

JOB DESCRIPTION
===============

The kind of jobs that this library would handle should be described in a JSON file this way:
<pre>
[
{
    "job_id": "info",
    "message_type": "command",
    "keywords": ["start", "info"],
    "countdown": 3,
    "minutes_timeout": 20,
    "job_action": "phrase",
    "data": "We are working on it. In the meanwhile you will have to look at the code."
}
]
</pre>

* **job_id**: is an optional field to name the job
* **message_type**: Indicates the type of messages that would trigger the action. There are three currently suported message types
 * *user_message*: After a user has written a message
 * *command*: After anyone has invoked our bot command /command
 * *repeated_message*: After a user(s) has(ve) written a message some number of times
* **keywords**: The command or text we are looking for
* **minutes_timeout**: For *repeated_message* the number of minutes within the keywords have to been written
* **countdown**: For *repeated_message* the number of times the keywords have to appear
* **frequency**: Return the job result only this % of times
* **job_action**: The action triggered. There are currently two kind of job_actions suported:
 * *phrase*: Returns the data string
 * *random_phrase*: Returns a random string from the data strings list
 * *blog_link*: Returns a non used (in 24 hours) blog link from the RSS present at data field
* **data**: The data used to return a value
