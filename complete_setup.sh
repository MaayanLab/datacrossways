
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo $SCRIPT_DIR
cd $SCRIPT_DIR

git clone https://github.com/MaayanLab/datacrossways_api.git
