import sys
import os
import ftplib

module_path = os.path.abspath(os.path.join('../python'))

if module_path not in sys.path:
    sys.path.append(module_path)

    
def ftp_upload(filename): 
    from local_info import ftp_url, ftp_pass, ftp_user, ftp_dir
    ftp = ftplib.FTP(ftp_url)
    ftp.login(ftp_user, ftp_pass)
    if ftp_dir is not None:
        ftp.cwd(ftp_dir)

    ext = os.path.splitext(filename)[1]
    if ext in (".txt", ".htm", ".html"):
        ftp.storlines("STOR " + filename, open(filename))
    else:
        ftp.storbinary("STOR " + filename, open(filename), 1024)






if len(sys.argv) < 2:
    print "No file given"
    sys.exit()

for i in range(1, len(sys.argv)):
    ff = sys.argv[i]
    if not os.path.isfile(ff):
        print ff + " is not a file"
    else:
        ftp_upload(ff)
    


