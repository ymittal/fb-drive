from __future__ import print_function
import httplib2
import json
import os
import io

from fbrecog import recognize

from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/fb-drive.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
FB_CONFIG_FILE = 'fb.json'
APPLICATION_NAME = 'Drive and FB Image'
DATA_FILE = 'data.json'

with open(FB_CONFIG_FILE) as fb_config_file:
    config = json.load(fb_config_file)
    access_token = config['access_token']
    cookie = config['cookie']
    fb_dtsg = config['fb_dtsg']

with open(DATA_FILE, 'a+') as data_file:
    try:
        classify_data = json.load(data_file)
    except ValueError:
        classify_data = {}


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'fb-drive.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def download_file(drive_service, file_id, filename):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print ("Download %d%%." % int(status.progress() * 100))


def recognize_pic(pic_name):
    result = recognize(pic_name, access_token, cookie, fb_dtsg)
    print (result)
    return result


def classify_pic(service, pic_id, pic_name):
    if pic_id not in classify_data:
        download_file(service, pic_id, pic_name)
        classify_data[pic_id] = recognize_pic(pic_name)
    else:
        print ('%s already classified' % pic_name)


def classify_pics(service, picTuples):
    """
    """
    try:
        for picTuple in picTuples:
            classify_pic(service, picTuple[0], picTuple[1])
    finally:
        with open(DATA_FILE, 'w') as data_file:
            json.dump(classify_data, data_file)


def retrieve_pics(drive_service):
    """
    """
    picTuples = []
    page_token = None
    while True:
        response = drive_service.files().list(q="mimeType='image/jpeg'",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()

        for file in response.get('files', []):
            if file.get('id') not in classify_data:
                picTuples.append((file.get('id'), file.get('name')))
                # print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))

        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    print ('Found %s pictures' % len(picTuples))
    return picTuples


def main():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    picTuples = retrieve_pics(service)
    classify_pics(service, picTuples)


if __name__ == '__main__':
    main()
