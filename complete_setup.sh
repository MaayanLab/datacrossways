
SCRIPT_DIR=$( dirname -- "$0"; )

echo $SCRIPT_DIR
cd $SCRIPT_DIR

rm -rf datacrossways_api
git clone https://github.com/MaayanLab/datacrossways_api.git

pip install SQLAlchemy==1.4.39
pip install Flask_SQLAlchemy==2.5.1

python3 datacrossways_api/createdb.py
