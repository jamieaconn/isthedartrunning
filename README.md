# isthedartrunning

# update apt-get
sudo apt-get update

# install git 
sudo apt-get install git
git config --global core.editor "vim"
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


# deactivate virtualenv
deactivate
