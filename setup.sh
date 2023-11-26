# clone repo

mkdir production
cd production
git clone git@github.com:jamieconn65/isthedartrunning.git

# update apt-get

sudo apt-get update

# install sqlite:

sudo apt-get install sqlite3

# install libpng-dev:

sudo apt-get install libpng-dev


# install pip:

sudo apt-get install python-pip python2-dev build-essential 

# upgrade pip:

sudo pip2 install --upgrade pip

# install virtualenv:

sudo pip2 install --upgrade virtualenv

# create and activate virtualenv:

virtualenv ENV --python=python2.7


source ENV/bin/activate

# install python dependancies:

pip2 install -r requirements.txt

# setup SQL databases:

python2 python/setup.py

# deactivate virtualenv:**

deactivate

# set up crontab
crontab crontab.txt
