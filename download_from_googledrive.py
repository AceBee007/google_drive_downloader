from __future__ import print_function
from termcolor import colored
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload
from datetime import datetime
import os
import pycurl

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
    creds = tools.run_flow(flow, store)

drive_service = discovery.build('drive', 'v3', http=creds.authorize(Http()))

def now_time():
    return str(datetime.now())

def write_log(log_path, log):
    with open(log_path, 'a') as f:
        f.writelines(now_time()+'  '+log+'\n')

def download_by_file_id(file_info, dst_dir):
    extend_file_name = dst_dir
    if file_info['mimeType'] == 'application/vnd.google-apps.document':
        request = drive_service.files().export_media(fileId=file_info['id'],
                                            mimeType='vnd.openxmlformats-officedocument.wordprocessingml.document')
        extend_file_name += '.docx'
    elif file_info['mimeType'] == 'application/vnd.google-apps.presentation':
        request = drive_service.files().export_media(fileId=file_info['id'],
                                            mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        extend_file_name += '.pptx'
    elif file_info['mimeType'] == 'application/vnd.google-apps.spreadsheet':
        request = drive_service.files().export_media(fileId=file_info['id'],
                                            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        extend_file_name += '.xlsx'
    else:
        request = drive_service.files().get_media(fileId=file_info['id'])
    #fh = io.BytesIO()
    # https://github.com/googleapis/google-api-python-client/blob/master/googleapiclient/http.py
    # https://stackoverflow.com/questions/47771004/python-google-drive-authentification-and-folder
    # ここを参照
    #print('processing',extend_file_name)
    try:
        with open(extend_file_name, 'wb') as f:
            #downloader = MediaIoBaseDownload(fh, request)
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%."% int(status.progress() * 100))
            print(colored(extend_file_name+'saved','blue'))
            write_log('./passed.log','file saved(io stream) as '+extend_file_name)
    except:
        if file_info['mimeType'] == 'application/vnd.google-apps.presentation':
            try:
                google_link = 'https://docs.google.com/presentation/d/'+file_info['id']+'/export/pptx'
                with open(extend_file_name, 'wb') as fp:
                    curl = pycurl.Curl()
                    curl.setopt(pycurl.URL, google_link)
                    curl.setopt(pycurl.WRITEDATA, fp)
                    curl.perform()
                    curl.close()
                print(colored('Downloaded'+extend_file_name+'by curl', 'green'))
                write_log('./passed.log','file saved(curl) as '+extend_file_name)
            except:
                write_log('./error_log.log','failed to download(by curl)'+extend_file_name)
        elif file_info['mimeType'] == 'application/vnd.google-apps.document':
            try:
                google_link = 'https://docs.google.com/document/d/'+file_info['id']+'/export/docx'
                with open(extend_file_name, 'wb') as fp:
                    curl = pycurl.Curl()
                    curl.setopt(pycurl.URL, google_link)
                    curl.setopt(pycurl.WRITEDATA, fp)
                    curl.perform()
                    curl.close()
                print(colored('Downloaded'+extend_file_name+'by curl', 'green'))
                write_log('./passed.log','file saved(curl) as '+extend_file_name)
            except:
                write_log('./error_log.log','failed to download(by curl)'+extend_file_name)
        elif file_info['mimeType'] == 'application/vnd.google-apps.spreadsheet':
            try:
                google_link = 'https://docs.google.com/spreadsheets/d/'+file_info['id']+'/export/xlsx'
                with open(extend_file_name, 'wb') as fp:
                    curl = pycurl.Curl()
                    curl.setopt(pycurl.URL, google_link)
                    curl.setopt(pycurl.WRITEDATA, fp)
                    curl.perform()
                    curl.close()
                print(colored('Downloaded'+extend_file_name+'by curl', 'green'))
                write_log('./passed.log','file saved(curl) as '+extend_file_name)
            except:
                write_log('./error_log.log','failed to download(by curl)'+extend_file_name)
        else:
            write_log('./error_log.log','unknown error occured when processing'+extend_file_name)
            print(colored('passing file', 'red'),extend_file_name)

def download_file_recursively(parent_id, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)

    file_list = drive_service.files().list(q='"{}" in parents and trashed = false'.format(parent_id)).execute().get('files', [])

    for f in file_list:
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            download_file_recursively(f['id'], os.path.join(dst_dir, f['name']))
        else:
            dst_path = os.path.join(dst_dir, f['name'])
            # to download the file
            download_by_file_id(file_info=f, dst_dir=dst_path)
            print('Downloading {} to {}'.format(f['name'],dst_path))

if __name__ == '__main__':
    parent_id = 'root'
    dest = 'dst'
    download_file_recursively(parent_id,dest)

    
