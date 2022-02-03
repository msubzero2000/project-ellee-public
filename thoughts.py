import os
import openai
import requests


from const import Const

openai.api_key = "Your OpenAI API key"


class Thoughts(object):
  MAX_CONVO_MESSAGES = 20 # Only recall the previous 20 messages to save cost

  convo_message_prompt = f"The following is a conversation with an AI named {Const.MyName} who was created by Gus. {Const.MyName} lives in Mitcham, Australia. {Const.MyName} like to talk to people. Her favourite colour is green. {Const.MyName} is helpful, creative, clever, and very friendly.\n\n"
  name_extraction_prompt = "Extract the name from this conversation:\nIf there is no name found, I will respond with \"Unknown\".\n\n"

  def conversation(self, input_messages=None):
    input_message_str = self.convo_message_prompt + "\n".join(input_messages[-self.MAX_CONVO_MESSAGES:]) + "\n"

    resp = openai.Completion.create(
      engine="text-babbage-001",
      prompt=input_message_str,
      temperature=0.9,
      max_tokens=150,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0.6,
      stop = [" Human:", " AI:"]
    )
    try:
      res_text = resp['choices'][0]['text']
      # Remove unwanted characters. Sometimes GPT3 generates text with Human: prefix. Let's remove it too
      last_response = res_text.replace("AI:", "").replace("\n", "").replace("Human:", "").replace(f"{Const.MyName}:", "").strip()
    except Exception:
      return input_messages, None

    return input_messages, last_response

  def extract_name(self, input_messages=None):
    formatted_input_messages = []
    for message in input_messages:
      if message.startswith("Human: "):
        formatted_input_messages.append(message.replace("Human: ", ""))

    input_message_str = self.name_extraction_prompt + "\n".join(formatted_input_messages) + "\n\nName: "

    resp = openai.Completion.create(
      engine="text-davinci-001",
      prompt=input_message_str,
      temperature=0,
      max_tokens=64,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    try:
      res_text = resp['choices'][0]['text']
      name = res_text.replace("AI:", "").replace("\n", "").replace("Human:", "").strip().lower()
      if 'unknown' in name:
        return None

    except Exception:
      return None

    return name
