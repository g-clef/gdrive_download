import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
SCOPES = ['https://www.googleapis.com/auth/drive']


def make_creds(token_pickle_path="./token.pickle"):
    # 1) create a google application here https://developers.google.com/drive/api/v3/quickstart/python
    # 2) Keep the "credendials.json" file it gives you. Put it next to this script.
    # 2) run this script on the command line once. It will ask for permission to access your files. say yes.
    # 3) take the pickle file created, include it with the rest of the build files.
    creds = None
    if os.path.exists(token_pickle_path):
        with open(token_pickle_path, "rb") as filehandle:
            creds = pickle.load(filehandle)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_pickle_path, "wb") as filehandle:
            pickle.dump(creds, filehandle)


if __name__ == "__main__":
    make_creds()
