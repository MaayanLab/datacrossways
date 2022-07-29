
SCRIPT_DIR=$( dirname -- "$0"; )

echo $SCRIPT_DIR
cd $SCRIPT_DIR

rm -rf datacrossways_api
git clone https://github.com/MaayanLab/datacrossways_api.git

pip install -r datacrossways_api/requirements.txt

python3 datacrossways_api/createdb.py
