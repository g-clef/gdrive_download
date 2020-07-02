# gdrive_download

These are scripts and kubernetes deploy files to download whole directories from Google Drive.

The download application is in `GDrive_Download.py`. That script assumes the existence of a `token.pickle` file,
which is created with the `make_token_pickle.py` script. For more on that, see the "Authentication" section below.

The GDrive_Download script assumes you want to download the [OP_TC data](https://github.com/FiveDirections/OpTC-data) to
`/tmp/testing`. You can provide a different path to save the files with the `OUTPUT_PATH` environment variable. Also,
the script is set up assuming it will be run in a kubernetes pod, so the assumed path for the `token.pickle` file is
`/app/token.pickle`, which you can change with the `PICKLE_PATH` environment varible. Lastly, if you want to download
a different Google Drive folder, grab it's ID from the GDrive URL, and provide that as the `DRIVE_ID` environment 
variable. (To determine the Google Drive ID, it's the end part of the google drive URL, so for 
"https://drive.google.com/drive/folders/1n3kkS3KR31KUegn42yk3-e6JkZvf0Caa", the ID would be 
"1n3kkS3KR31KUegn42yk3-e6JkZvf0Caa".)


Authentication
---------------

GDrive's authentication is set up such that you *must* authenticate, even if you are downloading something that is
shared publicly. That authentication is also based on *application* authentication, not user authentication. That
means that to download even a publicly-shared thing, you must create a user in google's framework, create an *application*
in google's framework, and authorized that application to read that user's files/folders/etc. I found that the easiest
way to do that was:
 1) Create a throwaway gmail address, 
 2) Run the [Google quickstart](https://developers.google.com/drive/api/v3/quickstart/python)
to enable the Google Drive API for that throwaway user. 
 3) Download the `credentials.json` file created in step 2.
 4) Put the `credentials.json` file in the directory with `make_token_pickle.py`, and run the `make_token_pickle.py` script.
 5) Step 4 will open a browser window ask you to authorize the demo application to access the throwaway user's files. If 
  you authorize it, and it successfully authenticates, the script will create a file called `token.pickle` in the directory
  with the script. 
 6) Use `token.pickle` to run the GDrive_Download.py script (on the command line or in the kubernetes pod). 
 
 
 Running in Kubernetes
 --------------------
 
 To run this in kubernetes, you will need a few things:
  0) A kubernetes cluster. 
  1) Somewhere for the kubernetes pod to store the resulting files. The downloader yaml file assumes an NFS mount.
   If that's what you have, then you'll just need to fill in the IP and share path in the`kubernetes/downloader-job.yaml` 
   file. If you have some other file share, you'll need to modify the yaml file to indicate what share type you do
   have, and how to mount it in the pod.
  2) The authentication `token.pickle` file from the "Authentication" section above. You will need to base-64 encode
  that file, and paste the resulting text into the `secrets.yaml` file.
  
Once you've got that set up, create the secret first (kubectl create -f secrets.yaml) then the pod, and let it run.
Since the resuling data is about 1TB of stuff, it may take a few days to download everything.
  