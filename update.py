from logging import FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info
from os import path as ospath, environ
import os, contextlib, requests
from subprocess import run as srun
from requests import get as rget
from dotenv import load_dotenv, dotenv_values
from pymongo import MongoClient

if ospath.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[FileHandler('log.txt'), StreamHandler()],
                    level=INFO)

def get_config_from_url(configurl: str):
    try:
        if os.path.isfile('config.env'):
            with contextlib.suppress(Exception):
                os.remove('config.env')
        if ' ' in configurl:
            log_info("Detected gitlab snippet url. Example: 26265 sdg6-626-g6256")
            
            snipid, apikey = configurl.split(maxsplit=1)
            main_api = f"https://gitlab.com/api/v4/snippets/{snipid}/raw"
            headers = {'content-type': 'application/json', 'PRIVATE-TOKEN': apikey}
            res = requests.get(main_api, headers=headers)
        else:
            res = requests.get(configurl)
        if res.status_code == 200:
            log_info("Config uzaktan alındı. Status 200.")
            with open('config.env', 'wb+') as f:
                f.write(res.content)
            load_dotenv('config.env', override=True)
        else:
            log_error(f"Failed to download config.env {res.status_code}")
    except Exception as e:
        log_error(f"CONFIG_FILE_URL: {e}")

if CONFIG_FILE_URL := os.environ.get('CONFIG_FILE_URL', None):
    get_config_from_url(CONFIG_FILE_URL)
else:
    log_error("Lokal config.env will be used")

try:
    if bool(environ.get('_____REMOVE_THIS_LINE_____')):
        log_error('The README.md file there to be read! Exiting now!')
        exit()
except:
    pass

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(':', 1)[0]

DATABASE_URL = environ.get('DATABASE_URL', '')
if len(DATABASE_URL) == 0:
    DATABASE_URL = None

if DATABASE_URL is not None:
    conn = MongoClient(DATABASE_URL)
    db = conn.mltb
    old_config = db.settings.deployConfig.find_one({'_id': bot_id})
    config_dict = db.settings.config.find_one({'_id': bot_id})
    if old_config is not None:
        del old_config['_id']
    if (old_config is not None and old_config == dict(dotenv_values('config.env')) or old_config is None) \
           and config_dict is not None:
        environ['UPSTREAM_REPO'] = config_dict['UPSTREAM_REPO']
        environ['UPSTREAM_BRANCH'] = config_dict['UPSTREAM_BRANCH']
    conn.close()

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
   UPSTREAM_REPO = None

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'master'

if UPSTREAM_REPO is not None:
    if ospath.exists('.git'):
        srun(["rm", "-rf", ".git"])

    update = srun([f"git init -q \
                     && git config --global user.email e.anastayyar@gmail.com \
                     && git config --global user.name mltb \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    if update.returncode == 0:
        log_info('Successfully updated with latest commit from UPSTREAM_REPO')
    else:
        log_error('Something went wrong while updating, check UPSTREAM_REPO if valid or not!')
