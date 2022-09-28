
SCRIPT_DIR=$( dirname -- "$0"; )
cd $SCRIPT_DIR

rm -rf datacrossways_api
git clone https://github.com/MaayanLab/datacrossways_api.git

cd datacrossways_api
pip install -r requirements.txt

cp -r ../secrets/ secrets
python3 datacrossways_api/createdb.py
