import os
import pickle
import shutil
import tempfile
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

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
        """
        List the contents of an ID that Google Docs identified as a "folder"-like object.

        :param file_id: The google file_id of the folder
        :return: a list of files in the folder
        """
        results = self.service.files().list(
            pageSize=1000, q=f"'{file_id}' in parents",
            fields="nextPageToken, files(id, name, mimeType)").execute(num_retries=3)
        folder = results.get('files', [])
        return folder

    def download_file(self, file_id, name, dest_path):
        """
        Download a file from Google Docs. Note: this checks to see if the file already exists. If it does not
        this makes a temporary file, saves the contents into the temporary file, and then moves the temporary file
        to the new location when successful. This allows the overall download job to fail a given file, but restart
        and pick up where it left off.

        :param file_id: The google file_id to be downloaded
        :param name: The name of the file to be downloaded
        :param dest_path: the path to save the file to
        :return:
        """
        success = False
        count = 0
        output_path = os.path.join(dest_path, name)
        if os.path.exists(output_path):
            print(f"{name} already exists. Skipping")
            return
        temp_path = None
        while not success:
            _, temp_path = tempfile.mkstemp()
            with open(temp_path, "wb") as temp_handle:
                try:
                    request = self.service.files().get_media(fileId=file_id)
                    downloader = MediaIoBaseDownload(temp_handle, request, chunksize=1024*1024)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk(num_retries=3)
                        print("Download %d%%." % int(status.progress() * 100))
                    success = True
                except HttpError:
                    # for some reason, google apis sometimes return a 500 error in the middle of
                    # downloading a file. Retry the file when that happens.
                    # but don't keep doing the same thing over and over if it keeps failing.
                    os.remove(temp_path)
                    if count > 3:
                        print(f"downloading {name} failed. ")
                        raise
                    count += 1
                    print(f"error in downloading {name}. retrying.")
                    time.sleep(10)
                    continue
        if temp_path is not None:
            # should be impossible for this to still be None here, but doesn't hurt to check
            shutil.copy(temp_path, output_path)
            os.remove(temp_path)

    def walk_folder_tree(self, starting_id, dest_path):
        """
        Recursively walk the entire tree of folders at a given path. Make a mirroring directory structure in the
        destination path, and download any files into those directories as appropriate.

        :param starting_id: the starting file_id of the "folder"-like object in google docs.
        :param dest_path:  the output path to start writing files to
        :return:
        """
        for entry in self.list_folder_contents(starting_id):
            if str(entry['mimeType']) == str('application/vnd.google-apps.folder'):
                if not os.path.isdir(os.path.join(dest_path, entry['name'])):
                    os.mkdir(path=os.path.join(dest_path, entry['name']))
                print(f"entering folder {entry['name']}")
                self.walk_folder_tree(entry['id'], dest_path + "/" + entry['name'])
            else:
                print(f"downloading file {entry['name']}")
                self.download_file(entry['id'], entry['name'], dest_path)


if __name__ == "__main__":
    starting_drive_id = os.environ.get("DRIVE_ID", "1n3kkS3KR31KUegn42yk3-e6JkZvf0Caa")
    test_path = os.environ.get("OUTPUT_PATH", "/tmp/testing")
    GDownloader = GDriveDownloader()
    GDownloader.walk_folder_tree(starting_drive_id, test_path)
