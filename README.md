# google_drive_downloader
a simple script to download files from your google drive by using google drive API and curl

## Installation of dependency

```bash
sudo pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib oauth2client termcolor pycurl
```
## How to use
- Download and place your secret_key_file to this directory.
- Edit global config variable in `download_from_googledrive.py` <br>The defalut is below
```python
DEST = '/home/pi/Backup/'+TODAY+'_backup'         # The destination directory
LOG_FILE = DEST+'/success.log'                    # log of downloaded file
ERROR_LOG_FILE = DEST+'/error.log'                # log of errors
SCOPES = 'https://www.googleapis.com/auth/drive'  # the authority of API
```
- Run command `python3 download_from_googledrive.py`
