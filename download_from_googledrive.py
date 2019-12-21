from __future__ import print_function
from termcolor import colored
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload
from datetime import datetime
import os
import pycurl

TODAY = str(datetime.now())[:-7].replace('-','').replace(' ','_').replace(':','.')
DEST = '/home/pi/Backup/'+TODAY+'_backup'
LOG_FILE = DEST+'/success.log'
ERROR_LOG_FILE = DEST+'/error.log'
SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage(os.path.dirname(os.path.abspath(__file__))+'/storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets(os.path.dirname(os.path.abspath(__file__))+'/client_secrets.json', SCOPES)
    creds = tools.run_flow(flow, store)

drive_service = discovery.build('drive', 'v3', http=creds.authorize(Http()))


GOOGLE_MIME = {
        'application/vnd.google-apps.presentation':{'office_mime':'application/vnd.openxmlformats-officedocument.presentationml.presentation','extension':'.docx'},
        'application/vnd.google-apps.spreadsheet':{'office_mime':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','extension':'.pptx'},
        'application/vnd.google-apps.document':{'office_mime':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','extension':'.xlsx'},
        }

def now_time():
    return str(datetime.now())

def write_log(log_path, log):
    with open(log_path, 'a') as f:
        f.writelines(now_time()+'   '+log+'\n')

def download_by_curl(file_info, dst_dir):
    mime_type_to_link_dict = {
            'application/vnd.google-apps.presentation':'https://docs.google.com/presentation/d/'+file_info['id']+'/export/pptx',
            'application/vnd.google-apps.spreadsheet':'https://docs.google.com/spreadsheets/d/'+file_info['id']+'/export/xlsx',
            'application/vnd.google-apps.document':'https://docs.google.com/document/d/'+file_info['id']+'/export/docx',
            }
    extend_file_name = dst_dir + GOOGLE_MIME[file_info['mimeType']]['extension']
    try:
        google_link = mime_type_to_link_dict[file_info['mimeType']]
        with open(extend_file_name, 'wb') as fp:
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL, google_link)
            curl.setopt(pycurl.WRITEDATA, fp)
            curl.perform()
            curl.close()
        print(colored('Downloaded '+extend_file_name+' by curl', 'green'))
        write_log(LOG_FILE,'file saved(curl) as '+extend_file_name)
        return True
    except:
        write_log(ERROR_LOG_FILE,'failed to download (by curl) '+extend_file_name)
        return False

def download_by_api(file_info, dst_dir):
    if file_info['mimeType'] in GOOGLE_MIME:
        request = drive_service.files().export_media(fileId=file_info['id'],
            mimeType=GOOGLE_MIME[file_info['mimeType']]['office_mime'])
        extend_file_name = dst_dir + GOOGLE_MIME[file_info['mimeType']]['extension']
    else:
        request = drive_service.files().get_media(fileId=file_info['id'])
        extend_file_name = dst_dir

    #fh = io.BytesIO()
    # https://github.com/googleapis/google-api-python-client/blob/master/googleapiclient/http.py
    # https://stackoverflow.com/questions/47771004/python-google-drive-authentification-and-folder
    # ここを参照
    #print('processing',extend_file_name)
    try:
        with open(extend_file_name, 'wb') as fp:
            downloader = MediaIoBaseDownload(fp, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%."% int(status.progress() * 100))
        print(colored('Downloaded '+extend_file_name+' by google API','blue'))
        write_log(LOG_FILE,'file saved(io stream) as '+extend_file_name)
        return True
    except:
        # 普段はAPIによるファイルのダウンロードのエラーを記録しない
        #write_log(ERROR_LOG_FILE,'failed to download (by api) '+extend_file_name)
        print(colored('Passing file '+extend_file_name, 'red'))
        return False



def download_file_recursively(parent_id, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)

    file_list = drive_service.files().list(q='"{}" in parents and trashed = false'.format(parent_id)).execute().get('files', [])

    for f in file_list:
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            download_file_recursively(f['id'], os.path.join(dst_dir, f['name']))
        else:
            dst_path = os.path.join(dst_dir, f['name'])
            # to download the file
            download_status = download_by_api(file_info=f, dst_dir=dst_path)
            if download_status == False:
                if ['mimeType'] in GOOGLE_MIME:
                    download_status = download_by_curl(file_info=f, dst_dir=dst_path)
                else:
                    error_msg = 'Unknown error occured while processing '+f['name']
                    write_log(ERROR_LOG_FILE, error_msg)
            else:
                pass
            print('Downloading {} to {}'.format(f['name'],dst_path))

if __name__ == '__main__':
    parent_id = 'root'
    download_file_recursively(parent_id, DEST)

    
