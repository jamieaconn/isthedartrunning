# isthedartrunning

# update apt-get
sudo apt-get update

# install git 
sudo apt-get install git
git config --global core.editor "vim"

# clone repository
git clone git@github.com:jamieconn65/isthedartrunning.git

# install sqlite
sudo apt-get install sqlite3

# install libpng-dev
sudo apt-get install libpng-dev

# make a few folders
mkdir image
mkdir image/radar
mkdir image/forecast

# install pip
sudo apt-get install python-pip python-dev build-essential 

# upgrade pip
sudo pip install --upgrade pip

# install virtualenv
sudo pip install --upgrade virtualenv

# create and activate virtualenv
virtualenv ENV
source ENV/bin/activate

# install python dependancies
pip install -r requirements.txt

# setup SQL databases
python setup.py

# deactivate virtualenv
deactivate

# install wget
sudo apt-get install wget

# get latest data file

# download relevant gdrive from https://github.com/prasmussen/gdrive
chmod +x gdrive-linux-386
mv {filename} ~/gdrive
~/gdrive about 

# ....follow instructions...

~/gdrive list
~/gdrive download {data.db filename}


