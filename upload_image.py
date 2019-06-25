#!/usr/bin/python3 -Es
import argparse
import getpass
import requests
import hashlib
import hmac
import urllib
import os
import json
from tqdm import tqdm

__author__ = 'Stefan Weiberg'
__license__ = 'EUPLv2'
__version__ = '0.0.1'
__maintainer__ = 'Stefan Weiberg'
__email__ = 'sweiberg@suse.com'
__status__ = 'Development'

desc = "uploader to add JPEGS with Alternatives to Resourcespace"
parser = argparse.ArgumentParser()

parser.add_argument("-f", dest="folder", type=str, required=True,
                    help="folder with photos")
parser.add_argument("-l", dest="link", type=str, required=True,
                    help="link to web location containing the photos")
parser.add_argument("-c", dest="collection", type=str, required=True,
                    help="name for the collection")
parser.add_argument("-a", dest="alternative", action='append', required=False, default=[],
                    help="filetypes for alternative (case-sensitive and additive)")
parser.add_argument("-e", dest="extension", type=str, required=True,
                    help="extension of primary (case-sensitive)")
parser.add_argument("-u", dest="url", type=str, required=True,
                    help="Base URL of the ResourceSpace API endpoint (https://example.com/api/?)")

args = parser.parse_args()
folder = args.folder
link = args.link
collection_name = args.collection
alternative = args.alternative
extension = args.extension
base_url = args.url

try:
    user = input("Please enter your ResourceSpace username: ")
    key = getpass.getpass(prompt="Please enter the ResourceSpace API key: ")
except Exception as error:
    print('ERROR', error)

path = urllib.parse.quote(folder + "/")

def create_photo_resource():
    query = {'user': user, 'function': 'create_resource', 'param1': '1', 'param2': '0', 'param3': link + filename, 'param4': 'false', 'param5': '', 'param6': 'true', 'param7': ''}
    return send_request(query)

def create_collection():
    query = {'user': user, 'function': 'create_collection', 'param1': collection_name}
    return send_request(query)

def add_to_collection(resource_id, collection_id):
    query = {'user': user, 'function': 'add_resource_to_collection', 'param1': resource_id, 'param2': collection_id}
    return send_request(query)

def upload_alternative(ext_filename, a):
    filesize = os.stat(path + ext_filename).st_size
    query = {'user': user, 'function': 'add_alternative_file', 'param1': resource_id, 'param2': ext_filename, 'param3': ext_filename, 'param4': ext_filename, 'param5': a, 'param6': filesize, 'param7': '', 'param8': link + ext_filename}
    return send_request(query)

def update_title(resource_id, filename_no_extension):
    query = {'user': user, 'function': 'update_field', 'param1': resource_id, 'param2': 'title', 'param3': filename_no_extension, 'param4': 'false'}
    return send_request(query)

def send_request(query):
    query_str = (urllib.parse.urlencode(query))
    query['sign'] = hashlib.sha256(key.encode('utf-8') + query_str.encode('utf-8')).hexdigest()
    with urllib.request.urlopen(base_url + urllib.parse.urlencode(query)) as x:
        data = x.read().decode('utf-8')
    return(data)

if __name__ == "__main__":
    try:
        query = {'user': user, 'function': 'get_user_collections'}
        user_collections = json.loads(send_request(query))
        collection_id = None
        for user_collection in user_collections:
            if user_collection['name'] == collection_name:
                print("Collection already exists. Using existing collection...")
                collection_id = user_collection['ref']
                break
        if collection_id is None:
            print("Collection doesn't exist yet. Creating new collection...")
            collection_id = create_collection()

        directory = os.fsencode(path)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if filename.endswith(extension):
                resource_id = create_photo_resource()
                update_title(resource_id, os.path.splitext(filename)[0])
                if not add_to_collection(resource_id, collection_id):
                    raise Exception("couldn't add to collection")
                for a in alternative:
                    ext_filename = os.path.splitext(filename)[0] + '.' + a
                    if not upload_alternative(ext_filename, a):
                        raise Exception("couldn't upload alternative")
            else:
                continue
    except Exception as error:
        print('ERROR', error)
    pass