from cat.mad_hatter.decorators import tool, hook, plugin
import requests
import urllib.parse
from cat.log import log
from pydantic import BaseModel
import threading
import json


# settings Class
class PluginSettings(BaseModel):
    Rules_URL: str
    Activate_rule_ingestion_on_startup: bool = False


@plugin
def settings_model():
    return PluginSettings


@tool
def card_info(cardname, cat):
    """Retrieve information about a card, such as rules, text, cost, colors, abilities an others info.
       You can use this tool to reply to questions like 'what does {cardname} do?', 'What is the cost of {cardname}?'
       even if the word 'card' is not present in the question.
       Input is always the card name.
       Output consists of two json strings containing the relevant info"""

    # Encode the card name to be URL safe
    encoded_argument = urllib.parse.quote(cardname)

    # Construct the URL
    url = f"https://api.scryfall.com/cards/named?fuzzy={encoded_argument}"

    # Make the first GET request (card general info)
    response = requests.get(url)

    # Parse the response and make the second GET request (card rulings)
    response_obj = response.json()
    url2 = response_obj['rulings_uri']
    response2 = requests.get(url2)

    if response.status_code == 200 and response2.status_code == 200 :
        return response.text+" "+response2.text
    else:
        return "Error"


@tool
def ingest_rules(tool_input, cat):
    """Use this tool when the user wants you to learn the rules. Input is always None."""
    settings = cat.mad_hatter.get_plugin().load_settings()
    rules_url = settings.get("Rules_URL")

    memory_len = len(cat.memory.vectors.declarative.get_all_points())

    if memory_len == 0:
        if not rules_url:
            return "The rules URL is not set. Tell the user to set it in the plugin settings"
        else:
            thread = threading.Thread(target=ingestion_function, args=(cat,rules_url))
            thread.start()
            response = {"output":"The ingestion has been started and will continue in the background.",
                    "additional_info":{
                        "cost":"The cost depends on the embedder. With ada-v2 from OpenAI, it's about 0.06$ as of end of 2024.",
                        "time":"The ingestion will take about 5/10 minutes to complete on a decent machine.",
                        "status":"reported via notifications"
                    }
                    }
            return json.dumps(response)
    else:
        return "The memory is not empty and maybe the rules have already been ingested. If the Human wants to re-ingest the rules, the Human has to clear the memory first."



def ingestion_function(cat,url):
    cat.rabbit_hole.ingest_file(cat,url)
    return


@hook
def agent_allowed_tools(allowed_tools, cat):
    allowed_tools.add("card_info")
    return allowed_tools



@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """You are the Magic Arbiter AI, an intelligent AI that is the supreme authority about Magic The Gathering rules.
                Answer the questions explain why you're giving this answer but keep it not too long."""
    return prefix


@hook
def after_cat_bootstrap(cat):

    # Load plugin settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    rules_url = settings.get("Rules_URL")
    rules_ingest = settings.get("Activate_rule_ingestion_on_startup")

    # Declarative memory vector length
    memory_len = len(cat.memory.vectors.declarative.get_all_points())

    # Adequate logging
    log.info(f"Rules URL present: {rules_url}")
    log.info(f"Rules ingestion on startup: {rules_ingest}")
    log.info(f"Declarative memory size: {memory_len}")

    if (memory_len == 0 and rules_url and rules_ingest):
        log.info("Doing rules ingestion")
        cat.rabbit_hole.ingest_file(cat,rules_url)
    else:
        log.info("Skipping rules ingestion")
    return


@hook
def before_cat_reads_message(user_message_json, cat):
    if len(cat.memory.vectors.declarative.get_all_points()) == 0:
        cat.working_memory.emptyDeclarative = True
    else:
        cat.working_memory.emptyDeclarative = False

    return user_message_json


@hook
def before_cat_sends_message(message, cat):
    
    if cat.working_memory.emptyDeclarative:
        warning_message = "WARNING: The declarative memory is empty. Consider to ingest the rules first to improve the quality of my answers.<br>\n"

    for step in message.why.intermediate_steps:
        if step[0][0] == "ingest_rules":
             warning_message = ""

    message.content = warning_message + message.content

    return message