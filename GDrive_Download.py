import io
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']


class GDriveDownloader:
    # borrowed heavily from https://stackoverflow.com/questions/39003409/how-to-download-specific-google-drive-folder-using-python  # noqa
    def __init__(self):
        creds = self.authenticate()
        self.service = build("drive", "v3", credentials=creds)

    @staticmethod
    def authenticate():
        # 1) create a google application here https://developers.google.com/drive/api/v3/quickstart/python
        # 2) Keep the "credendials.json" file it gives you. Put it next to this script.
        # 2) run this script on the command line once. It will ask for permission to access your files. say yes.
        # 3) take the pickle file created, include it with the rest of the build files.
        creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as filehandle:
                creds = pickle.load(filehandle)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as filehandle:
                pickle.dump(creds, filehandle)
        return creds

    def list_folder_contents(self, file_id):
        results = self.service.files().list(
            pageSize=1000, q=f"'{file_id}' in parents",
            fields="nextPageToken, files(id, name, mimeType)").execute()
        folder = results.get('files', [])
        return folder

    def download_file(self, file_id, name, dest_path):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(os.path.join(dest_path, name), 'wb')
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

    def walk_folder_tree(self, starting_id, dest_path):
        for entry in self.list_folder_contents(starting_id):
            if str(entry['mimeType']) == str('application/vnd.google-apps.folder'):
                if not os.path.isdir(os.path.join(dest_path, entry['name'])):
                    os.mkdir(path=os.path.join(dest_path, entry['name']))
                print(entry['name'])
                self.walk_folder_tree(entry['id'], dest_path + "/" + entry['name'])
            else:
                self.download_file(entry['id'], entry['name'], dest_path)


if __name__ == "__main__":
    starting_drive_id = os.environ.get("DRIVE_ID", "1n3kkS3KR31KUegn42yk3-e6JkZvf0Caa")
    test_path = os.environ.get("OUTPUT_PATH", "/tmp")
    GDownloader = GDriveDownloader()
    GDownloader.walk_folder_tree(starting_drive_id, test_path)
