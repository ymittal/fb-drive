from __future__ import print_function
import httplib2
import json
import os
import io

from Queue import Queue
from threading import Thread
from fbrecog import recognize

from apiclient import discovery
from apiclient import errors
from apiclient.http import HttpRequest
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

APPLICATION_NAME = 'Drive and FB Image'
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'

CLIENT_SECRET_FILE = 'client_secret.json'
FB_CONFIG_FILE = 'fb.json'
DATA_FILE = 'data.json'

MAX_THREADS = 8

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# gets all config details needed to use fbrecog.recognize
with open(FB_CONFIG_FILE) as fb_config_file:
    config = json.load(fb_config_file)
    access_token = config['access_token']
    cookie = config['cookie']
    fb_dtsg = config['fb_dtsg']

# creates file if does not exist already
with open(DATA_FILE, 'a+') as data_file:
    try:
         # load already classified data if file exists
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


def download_file(file_id, filename):
    """Attempts to download file with given file_id

    :param file_id      file id
    :param filename     file name
    :return boolean denoting whether file was downloaded successfully
    """
    # httplib2 library is not thread-safe, need a new http for each thread
    drive_service = discovery.build('drive', 'v3', http=getHttp())
    request = drive_service.files().get_media(fileId=file_id)

    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
        except Exception as ex:
            print ("User rate limit exceeded for %s" % filename)
            return False
        print ("Download %d%%." % int(status.progress() * 100))
    return True


def recognize_pic(path):
    """Uses recognize function to determine which friends are in the
    picture

    :param path         image path
    :return a dict containing filename and friends identified in the pic
    """
    results = recognize(path, access_token, cookie, fb_dtsg)

    names = [str(result['name']) for result in results]
    print ('%s contains %s' % (path, names))

    return {
        "filename": path,
        "friends": names
    }


def classify_pic(pic_id, pic_name, picQ):
    """Classifies pic by first downloading the pic and then using FB
    Face Recognition to figure who's in the pic

    :param pic_id       pic id
    :param pic_name     pic title
    :param picQ         a queue of pics yet to be classified
    """
    if pic_id not in classify_data:
        is_success = download_file(pic_id, pic_name)
        if is_success:
            classify_data[pic_id] = recognize_pic(pic_name)
        else:
            # add pic to the queue on unsuccessful download
            picQ.put((pic_id, pic_name))
        os.remove(pic_name)  # delete pic from local directory
    else:
        print ('%s already classified' % pic_name)


def classify_pics(picQ):
    """Loops through all pics to be classified in groups of threads,
    writing data for "recognized" pics to DATA_FILE

    :param picQ         a queue of pics yet to be classified
    """
    while not picQ.empty():
        try:
            print ("Starting a batch of threads...")
            threads = []
            for i in range(MAX_THREADS):
                if not picQ.empty():
                    picTuple = picQ.get()
                    t = Thread(target=classify_pic,
                               args=(picTuple[0], picTuple[1], picQ))
                    threads.append(t)
                    t.start()

            for t in threads:
                t.join()

        finally:
            # write to DATA_FILE even when process is interrupted
            with open(DATA_FILE, 'w') as data_file:
                print ("Rewriting %s with %s entries" %
                       (DATA_FILE, len(classify_data)))
                json.dump(classify_data, data_file)


def retrieve_pics(drive_service):
    """Fetches a list of images in the Drive of authenticated user and
    creates a queue of tuples of format (image_id, image_name) for images yet
    to be "classified"

    :param drive_service    Google Drive API service
    :return a queue of tuples of format (image_id, image_name)
    """
    picQ = Queue()
    page_token = None
    while True:
        response = drive_service.files().list(q="mimeType='image/jpeg'",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()

        for file in response.get('files', []):
            if file.get('id') not in classify_data:
                picQ.put((file.get('id'), file.get('name')))

        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    print ('Found %s pictures' % picQ.qsize())  # prints no. of new pics found
    return picQ


def getHttp():
    """Returns a new http client using user auth details"""
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    return http


def main():
    """Retrieves all image files from Google Drive and attempts to 
    classify all of them, storing data after regular intervals
    """
    service = discovery.build('drive', 'v3', http=getHttp())

    picQ = retrieve_pics(service)
    classify_pics(picQ)


if __name__ == '__main__':
    main()
