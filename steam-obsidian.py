import vdf, os, requests, re, logging, sys, time, argparse
from pathlib import Path
from steamgrid import SteamGridDB, PlatformType, MimeType
from settings import *
# This is just the file where I'm keeping my personal API Keys during development
from secrets import *

# Set up logging
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# Setting up Arguments
parser = argparse.ArgumentParser(prog='Steam-Obsidian-Auto-Note', description='A program that automatically creates notes from your Steam games as you play. ' \
'Any missing flags will fall back to what you have configured in settings.py')

parser.add_argument('-s', '--service', action='store_true', help='Run the program as a continuously running service')
parser.add_argument('-in', '--interval', help='The frequency in minutes the program will run in service mode', type=int)
parser.add_argument('-i', '--icon', action='store_true', help='Enable retreiving icon art from SteamGridDb.')
parser.add_argument('-b', '--banner', action='store_true', help='Enable retreiving banner art from SteamGridDb.')
parser.add_argument('-c', '--cover', action='store_true', help='Enable retreiving cover art from SteamGridDb.')
parser.add_argument('-r', '--release', action='store_true', help='Get release date from SteamGridDb')
parser.add_argument('-f', '--full', action='store_true', help='Perform full scan of all games currently on system. I\'m not fulle sure how Steam stores data  \
                    in localconfig.vdf, but this will likely only pull games that you have played on the system you\'re running the program on. \
                        EXTREMELY RECOMMENDED to do a test-run with \'--test\' before using this')
parser.add_argument('-t', '--test', action='store_true', help='Get a list of the games that will be added without actually adding them.')
parser.add_argument('-sgapi', '--steamapi', help='REQUIRED. Your SteamGridDb API Key. Can also be set in settings.py')
parser.add_argument('-oapi', '--obsidianapi', help='REQUIRED. Your Obsdian Local REST API Key. Can also be set in settings.py')
parser.add_argument('-u', '--url', help='REQUIRED. Your SteamGridDb API Key. Can also be set in settings.py')
parser.add_argument('-d', '--dir', help='Directory in your Obsidian vault to create notes in. Default is the root directory')
parser.add_argument('-e', '--exclude', help='A comma-separated list of games to exclude from the scan. Format example: [\'Retroach\', \'Proton\']')
parser.add_argument('-g', '--game', help='The Steam ID of a single game you\'d like to scan instead of letting the program decide.')

args = parser.parse_args()
# Set Variables from CLI arguments
RUN_AS_SERVICE = args.service

if args.interval is not None:
    RUN_INTERVAL = args.interval
    logging.info('Running with flag: interval = ' + str(RUN_INTERVAL))

if args.icon is True:
    GET_ICON = args.icon
    logging.info('Running with flag: icon = ' + str(GET_ICON))

if args.banner is True:
    GET_BANNER = args.banner
    logging.info('Running with flag: banner = ' + str(GET_BANNER))
    
if args.cover is True:
    GET_COVER = args.cover
    logging.info('Running with flag: cover = ' + str(GET_COVER))

if args.release is True:
    GET_RELEASE_DATE = args.release
    logging.info('Running with flag: release = ' + str(GET_RELEASE_DATE))

if args.full is True:
    FULL_BACKLOG = args.full
    logging.info('Running with flag: full = ' + str(FULL_BACKLOG))
    
if args.steamapi is not None:
    STEAM_GRID_API_KEY = args.steamapi
    logging.info('Running with flag: steamapi = ' + STEAM_GRID_API_KEY)
    
if args.obsidianapi is not None:
    OBSIDIAN_API_KEY = args.obsidianapi
    logging.info('Running with flag: obsidianapi = ' + OBSIDIAN_API_KEY)
    
if args.url is not None:
    OBSIDIAN_API_URL = args.url
    logging.info('Running with flag: url = ' + OBSIDIAN_API_URL)
    
if args.dir is not None:
    OBSIDIAN_DIRECTORY = args.dir
    logging.info('Running with flag: dir = ' + OBSIDIAN_DIRECTORY)

if args.exclude is not None:
    EXCLUSIONS = args.exclude
    logging.info('Running with flag: exclude = ' + EXCLUSIONS)

if args.game is not None:
    ONLY_GAME = args.game
    logging.info('Running with flag: game = ' + ONLY_GAME)
    

if args.test is True:
    DRY_RUN = True
    logging.info('Running with flag: dryrun = ' + str(DRY_RUN))
    





# GLOBAL VARIABLES
STEAM_PATH = Path(os.path.expanduser(STEAM_PATH))


# Read localconfig.vdf to get a list of the three most recently played games
def read_local_config(games):
    logging.info('Reading localconfig.vdf...')
    
    # Open localconfig.vdf
    local_config_path = Path(STEAM_PATH / 'userdata/' / str(STEAM_USER) / 'config/localconfig.vdf')
    with open(local_config_path, 'r', encoding='UTF-8') as f:
        local_config = vdf.load(f)

        # IF running in single game mode, just get that game and skip the loop        
        if args.game is not None:
            all_games = local_config['UserLocalConfigStore']['Software']['Valve']['Steam']['apps'][str(ONLY_GAME)]
            games.update({str(ONLY_GAME) : all_games})
            return games
            
        else:
            # Extract down to the 'apps' level of the vdf file
            all_games = local_config['UserLocalConfigStore']['Software']['Valve']['Steam']['apps']

        
    # for each game, get the last played time and create a new list of the game id and playtime, sorted
    # by last played time
    latest_games = {}
    game_ids = {}
    game_played = {}
    x = 0

    # get last played time if it's available
    logging.info('Getting last played times...')
    
    
    for k, v in all_games.items():
        
        try:
            last_played = v['LastPlayed']
        except:
            continue

        # Construct indexed lists of game IDs and playtimes to match up after sorting
        game_ids.update({str(x) : k})
        game_played.update({str(x) : int(last_played)})
        x += 1

    # Sort the last played times descending
    playtimes = list(game_played.values())
    playtimes.sort()
    playtimes.reverse()

    # loop through the playtimes to get the indexed number of that playtime
    # then get that same index from game ids and match them back together
    sorted_games = {}
    games_found = 0
    for time in playtimes:
        for k, v in game_played.items():
            found = False
            # When a playtime matches the list, get the index and match it to the
            # same index in the game ids list
            if time == v:
                for key, value in game_ids.items():
                    if k == key:
                        sorted_games.update({value : time})
                        games.update({value : all_games[value]})
                        found = True
                        games_found += 1
                        break
            
            if found == True:
                break
        # Limit the list to only 3 games
        if FULL_BACKLOG == False:
            if games_found == 3:
                break
        else:
            for k, v in all_games.items():
                all_games.update({k : {'cover' : '', 'banner' : '', 'icon' : '', 'Playtime' : '', "release_date" : ''}})
            games.update(all_games)
            
            
    return games

# Sanitize names of illegal characters
def sanitize_names(name):
    clean_name = re.sub(r'[\\\/:*?"<>|]', '', name).strip()
    return clean_name


# TODO: Connect to SteamGridDb to get more game details
def get_game_title(games):
    
    del_games = []
    
    logging.info('Fetching data and images from SteamGridDb...')
    sgdb = SteamGridDB(STEAM_GRID_API_KEY)
    # For each game in our games shortlist, query SteamGridDb to get the game title
    for game in games.keys():

        # Get game title and make it filename-safe
        try:
            game_item = sgdb.get_game_by_steam_appid(int(game))
        except:
            logging.warning('Game with ID ' + game + ' not found in SteamGridDb, skipping...')
            del_games.append(game)
            continue
        game_title = sanitize_names(game_item.name)

        # Add game title to the games dictionary
        games[game].update({'title' : game_title})

        if game not in existing_games:
            if GET_RELEASE_DATE == True:
                games[game].update({'release_date' : game_item.release_date})
            else:
                games[game].update({'release_date' : ''})


            ### Optionally get certain image urls
            # Get Icon
            if GET_ICON == True:
                icons = sgdb.get_icons_by_platform(game_ids=[int(game)], platform=PlatformType.Steam)

                # Skip .ico files. This should be doable with the SteamGridDb API but doesn't seem to be working (mimetype error) 
                if icons is not None:
                    for icon in icons:
                        if icon.url.endswith('.ico'):
                            continue
                        else:
                            icon_url = icon.url
                            break
                
                    games[game].update({'icon' : icon_url})
                
                else:
                    logging.warning('No icon found for ' + game_title)
                    games[game].update({'icon' : ''})
            else:
                games[game].update({'icon' : ''})



            # Get Banner
            if GET_BANNER == True:
                banner = sgdb.get_heroes_by_platform(game_ids=[int(game)], platform=PlatformType.Steam)
                if banner is not None:
                    banner_url = banner[0].url
                    games[game].update({'banner' : banner_url})
                else:
                    logging.warning('No Banner found for ' + game_title)
                    games[game].update({'banner' : ''})
            else:
                games[game].update({'banner' : ''})


            # Get Cover
            if GET_COVER == True:
                cover = sgdb.get_grids_by_platform(game_ids=[int(game)], platform=PlatformType.Steam)
                if cover is not None:
                    cover_url = cover[0].url
                    games[game].update({'cover' : cover_url})
                else:
                    logging.warning('No Cover found for ' + game_title)
                    games[game].update({'cover' : ''})
                    
            else:
                    games[game].update({'cover' : ''})
        
        logging.debug ('Note for ' + game_title + ' alreadying exists, skipping image scraping...')


    for game in del_games:
        games.pop(game)
    return games


# get the template file and replace variables with values for each game
def get_template(game_id, game):

    logging.debug('Getting the base note template from \'template.txt\'')
    # open and read the template file
    template_file = Path(__file__).parent / 'template.txt'
    with open(template_file, 'r', encoding='UTF-8') as t:
        template = t.read()
        try:
            release_date = str(game['release_date']).split(' ')[0]
        except:
            release_date = ''
        title = sanitize_names(game['title'])

        # Replace all the placeholders with their actual values
        template = template.replace("{title}", title)
        template = template.replace("{cover}", game['cover'])
        template = template.replace("{banner}", game['banner'])
        template = template.replace("{icon}", game['icon'])
        template = template.replace("{id}", game_id)
        template = template.replace("{playtime}", game['Playtime'])
        template = template.replace("{release_date}", release_date)

        return template


def get_existing(games):
    
    existing_games = []
    
    for game in games.items():
        if game in EXCLUSIONS:
            continue

        # Set up the Obsidian search URL and Auth header
        obsidian_search = OBSIDIAN_API_URL + 'search/'
        game_id = game[0]
        if 'Playtime' not in games[game_id]:
            playtime = ''
            
        else:
            playtime = games[game_id]['Playtime']



        headers = {'Authorization' : 'Bearer ' + OBSIDIAN_API_KEY, 'Content-Type' : 'application/vnd.olrapi.jsonlogic+json'}

        # Set query to look for 'steamId' in the frontmatter
        data = {
            "===": [
            {'var' : 'frontmatter.steamId'},
             int(game_id),
            ]
        }

        # make the request and return json
        r = requests.post(obsidian_search, headers=headers, json=data)
        obsidian_file = r.json()
        
        if obsidian_file != []:
            existing_games.append(game_id )
            
    return existing_games



# TODO: Check obsidian to see if a note for each game exists
def create_note(games, existing_games):
    if DRY_RUN == True:
        logging.info('This is a dry run.')
        logging.info('The Following would have been done:')
        
        
    for game in games.items():

        game_id = game[0]
        
        playtime = games[game_id]['Playtime']



        filename = OBSIDIAN_DIRECTORY + '/' + games[game_id]['title'] + '.md'


        # Check if a note for that game already exists
        if not game_id in existing_games:
            logging.debug('Note: ' + filename + ' doesn\'t exist, creating one...')

            create_url = OBSIDIAN_API_URL + 'vault/' + filename
            create_headers = {'Authorization' : 'Bearer ' + OBSIDIAN_API_KEY, 'Content-Type' : 'text/markdown'}
            
            template = get_template(game_id, games[game_id])
            if DRY_RUN == True:
                logging.info('Create Note: ' + filename)
            else:
                c = requests.post(create_url, headers=create_headers, data=template)
                logging.debug('Note: ' + filename + ' successfully created!')

        else:
            filename = OBSIDIAN_DIRECTORY + '/' + games[game_id]['title'] + '.md'


            
            if UPDATE_PLAYTIME == True:
                if playtime == 0:
                    logging.debug('Note: ' + filename + ' exists! Playtime is 0 (likely a non-steam game), skipping update...')
                else:
                    logging.debug('Note: ' + filename + ' exists! Updating playtime...')
                    update_note(filename, playtime)

    logging.info('Done!')
                


# If the note exists, update the information as necessary
def update_note(filename, playtime):
    # Define URL and headers
    update_url = OBSIDIAN_API_URL + 'vault/' + filename
    headers = {'Authorization' : 'Bearer ' + OBSIDIAN_API_KEY, 'Content-Type' : 'application/json', 'Target-Type' : 'frontmatter', 'Operation': 'replace', 'Target' : 'playtime'}
    
    logging.debug('Updating ' + filename)
    logging.debug('New playtime is ' + playtime)

    # Update the note
    if DRY_RUN == True:
        logging.info('Update Playtime: ' + filename)
    else:
        u = requests.patch(update_url, headers=headers, data=playtime)


# Handle Non-Steam Games
def non_steam_app(games):
    logging.info('Adding non-steam games...')

    nonsteam_config_path = Path(STEAM_PATH / 'userdata/' / str(STEAM_USER) / 'config/shortcuts.vdf')
    all_app_names = []
    # shortcuts.vdf is binary, so we're going to open this in binary mode and do binary_load
    # to get the contents
    if Path(nonsteam_config_path).is_file():
        with open(nonsteam_config_path, 'rb') as f:
            shortcuts_file = vdf.binary_load(f)
            all_shortcuts = shortcuts_file['shortcuts']

        # Add all the game titles to a list
        for app in all_shortcuts.items():
            all_app_names.append(app[1]['appname'])
            
        # Get the SteamGridDb Information for the non-steam game
        get_non_steam(all_app_names, games)

    else:
        logging.warning('No shortcuts.vdf file found. Attempting to process Steam games only...')

# Query SteamGridDb for info on non-steam games, searching by game title
def get_non_steam(all_app_names, games):

    # Search OBsidian for all files in the games directory
    obsidian_search = OBSIDIAN_API_URL + 'vault/' + OBSIDIAN_DIRECTORY + '/'
    headers = {'Authorization' : 'Bearer ' + OBSIDIAN_API_KEY, 'Content-Type' : 'application/json'}
    # Returns a dictionary with a 'files' key and a list of all games as a value
    r = requests.get(obsidian_search, headers=headers)

    # Extract the list of games
    all_games = r.json()['files']
    #initialize SteamGridDb connection
    sgdb = SteamGridDB(STEAM_GRID_API_KEY)
    for app in all_app_names:

        # Exclude the games listed in the EXCLUSIONS variable in settings.py
        if app in EXCLUSIONS:
            continue

        app_file = sanitize_names(app) + '.md' 
        
        if not app_file in all_games:                     
            # Get Game ID
            game = sgdb.search_game(app)
            game_title = sanitize_names(app)
            game_id = int(game[0].id)
            


            release_date = ''
            icon_url = ''
            banner_url = ''
            cover_url = ''

            # Get Release Date, Icon, Banner, and Cover
            if GET_RELEASE_DATE == True:
                game_details = sgdb.get_game_by_gameid(game_id)
                release_date = game_details.release_date


            if GET_ICON == True:
                icon = sgdb.get_icons_by_gameid(game_ids=[game_id], mimes=[MimeType.PNG])
                if not icon == None:
                    icon_url = icon[0].url


            if GET_BANNER == True:
                banner = sgdb.get_heroes_by_gameid(game_ids=[game_id])
                if not banner == None:
                    banner_url = banner[0].url


            if GET_COVER == True:
                cover = sgdb.get_grids_by_gameid(game_ids=[game_id])
                if not cover == None:
                    cover_url = cover[0].url



            # Update the main list with the non-steam games
            games.update({str(game_id) : {'title' : game_title, 'release_date' : release_date,
                                 'Playtime' : '0', 'icon' : icon_url, 'banner' : banner_url, 'cover' : cover_url}})

            

        else:
            logging.debug('Note for non-steam app ' + app_file + ' already exists. Skipping...')


        
def wait():
    time.sleep(RUN_INTERVAL * 60)
  
RUN_AS_SERVICE = True
if RUN_AS_SERVICE == True:
    while True:
        try:
            games = {}
            games = read_local_config(games)
            existing_games = get_existing(games)
            games = get_game_title(games)
            
            if args.game == None:
                non_steam_app(games)
            create_note(games, existing_games)
            logging.info('Run completed! Waiting ' + str(RUN_INTERVAL) + ' minutes for the next run...')
            wait()
            
        except Exception as err:
            logging.error('Run failed: ' + err)
            logging.error('Waiting ' + str(RUN_INTERVAL) + ' minutes for the next run...')

else:
    games = {}
    games = read_local_config(games)
    existing_games = get_existing(games)

    games = get_game_title(games)
    non_steam_app(games)
    create_note(games, existing_games)