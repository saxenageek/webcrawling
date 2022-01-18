#!/bin/bash
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
	google_chrome=$(google-chrome --version)
elif [[ "$OSTYPE" == "darwin"* ]]; then
	google_chrome=$(/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version)
fi    

if [[ google_chrome ]]; then
	echo ""
else
	echo "Installing Google Chrome"
	curl https://intoli.com/install-google-chrome.sh | bash
fi

#python_version=$(python --version | cut -f 2 -d " ")

#if [[ "$python_version" =~ ^3.*$ ]]; then
#    curl -O https://bootstrap.pypa.io/get-pip.py
#    python3 get-pip.py
#    python3 -m pip install --upgrade pip
#    python3 -m venv .
#    echo "Virtual Environment Created."
#    source bin/activate
#    echo "Virtual Environment Activated."
    
#    pip install selenium Pillow requests boto3 webdriver-manager
#else
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
python3 -m venv .
./bin/python3 -m pip install --upgrade pip
echo "Virtual Environment Created."
source bin/activate
echo "Virtual Environment Activated."
#pip install selenium Pillow requests boto3 webdriver-manager xlrd==1.2.0 openpyxl pandas mysqlclient
pip install -r ./requirements.txt
