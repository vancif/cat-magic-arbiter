from cat.mad_hatter.decorators import tool, hook, plugin
import requests
import urllib.parse
from cat.log import log
from pydantic import BaseModel
import threading


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
    """Replies to 'ingest the rules'. Input is always None."""
    thread = threading.Thread(target=ingestion_function, args=(cat,))
    thread.start()
    return "The ingestion has been started and will continue in the background."



def ingestion_function(cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    cat.rabbit_hole.ingest_file(cat,settings['Rules_URL'])
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

    # Declarative memory vector length
    memory_len = len(cat.memory.vectors.declarative.get_all_points())

    # Some logging
    log.info("Rules URL set: " + str("Rules_URL" in settings))
    log.info("Rules ingestion: " + str(settings['Activate_rule_ingestion_on_startup']))
    log.info(f"Declarative memory is of size {memory_len}")

    if (memory_len == 0 and "Rules_URL" in settings and settings['Activate_rule_ingestion_on_startup']):
        log.info("Doing rules ingestion")
        cat.rabbit_hole.ingest_file(cat,settings['Rules_URL'])
    else:
        log.info("Skipping rules ingestion")
    return