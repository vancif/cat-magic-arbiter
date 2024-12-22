# cat-magic-arbiter

`cat-magic-arbiter` is a plugin for [Cheshire Cat AI](https://cheshirecat.ai/) that enables it to retrieve information about *Magic: The Gathering* cards and set up an appropriate prompt for game interactions.

The plugin leverages the [Scryfall Public API](https://scryfall.com/docs/api) to fetch card data seamlessly.

**Tip**: For optimal performance, consider ingesting the game's rules into memory!

## Plugin Configuration

The plugin checks for memory content every time Cheshire Cat starts. If the memory is empty and the "Rule Ingestion" option is enabled, the plugin automatically ingests the rules page specified in plugin configuration.

### Steps to Set Up the Plugin

1. **Install the Plugin**: After the first installation of Cheshire Cat or after a full cleanup, install the plugin via the admin panel.  
2. **Configure Rules URL**: Navigate to the plugin settings and provide the game's rules URL. (The rules are published as a `.txt` file by Wizards of the Coast, available [here](https://magic.wizards.com/en/rules)).  
3. **Enable Rule Ingestion**: Check the option **"Activate Rule Ingestion on Startup"**.  
4. **Restart Cheshire Cat**: Restart Cheshire Cat and wait for the rule ingestion to complete.  

> **Note**: During the ingestion process, Cheshire Cat will be unavailable. Please be patient, as this operation may take a significant amount of time depending on the size of the rules file.

With these steps completed, Cheshire Cat will be fully equipped to assist with *Magic: The Gathering* gameplay and card queries.

### Special tool included in the plugin
- **Rule ingestion**: You can ask the Cat to ingest the rules anytime in any chat. If you do, the Cat will ingest the rules from the same URL specified above, but will perform this task asynchronously in the background.