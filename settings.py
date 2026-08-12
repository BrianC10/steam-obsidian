# The Path of your Steam install
STEAM_PATH = '~/.local/share/Steam'


# Optional Game Content to pull
GET_ICON = True
GET_BANNER = True
GET_COVER = True
GET_RELEASE_DATE = True

# Whether or not to Update playtime on existing notes. This will overwrite the 'playtime'
# frontmatter field no matter what. This is also the only function of this program that does
# any editing or overwriting of existing content. It should only ever affect the frontmatter
# field 'playtime' and nothing else, but it will update whether the playtime has changed or
# not, thus updating the modified time of each note it updates.
UPDATE_PLAYTIME = True

# Enable this to have the program scan every possible game it can find in your local instance
# of Steam. Leave it False to only scan the 3 most recently played games. All non-steam shortcuts
# are scanned each time due to lack of last-played data.
FULL_BACKLOG = False

# Add your API keys and Obsidian REST API URL here.
# Go to https://wwww.steamgriddb.com/profile/preferences/api to find your API Key
STEAM_GRID_API_KEY = ''

# In Obsidian: Settings -> Community Plugins -> Local REST API -> Options
OBSIDIAN_API_KEY = ''
OBSIDIAN_API_URL = ''

# The directory in your Obsidian Vault to place your game notes in. Use '' for root
OBSIDIAN_DIRECTORY = 'Games'

# A comma-separated list of games or apps to be excluded from the scan. Example: ['RetroArch', 'Proton Experimental']
EXCLUSIONS = ['RetroArch', 'ProtonPlus', 'Proton Experimental']

# The Rescan frequency if running the program as a service
RUN_INTERVAL = 30

# Log Level: INFO, DEBUG, WARNING
LOG_LEVEL = 'DEBUG'

# Set True to run the script and view the logs to see what it would do, without actually doing it
DRY_RUN = False