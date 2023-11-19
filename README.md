The idea of repository based on https://github.com/chaserhkj/PyMajSoul/

Python wrappers for Majsoul allow you to interact with their servers from Python scripts.

## For User

1. Install python packages from `requirements.txt`
2. `python example.py -u username -p password`

This example is working only with **Python3.7+**.

Also, you need to have an account from CN server to run this example, because only accounts from CN server has the ability to login with login and password.

If you want to login to EN or JP servers you need to write your code to authenticate via email code or social network. Protobuf wrapper from this repository contains all needed API objects for that.

## For Developer

### Requirements

1. Install python packages from `requerements.txt`
1. Install protobuf compiler `sudo apt install protobuf-compiler`

### How to update protocol files to the new version

It was tested on Ubuntu.

1. Download the new `liqi.json` file from MS (find it in the network tab of your browser) and put it to `ms/liqi.json`
1. `python generate_proto_file.py`
1. `protoc --python_out=. protocol.proto`
1. `chmod +x ms-plugin.pychmod +x ms-plugin.py`
1. `sudo cp ms-plugin.py /usr/bin/ms-plugin.py`
1. `protoc --custom_out=. --plugin=protoc-gen-custom=ms-plugin.py ./protocol.proto`

### How to update protocol files for manager API to the new version

1. Prepare new `liqi_admin.json` file from MS tournament manager panel
1. `python ms_tournament/generate_proto_file.py`
1. `protoc --python_out=. protocol_admin.proto`
1. `chmod +x ms-admin-plugin.py`
1. `sudo cp ms-admin-plugin.py /usr/bin/ms-admin-plugin.py`
1. `protoc --custom_out=. --plugin=protoc-gen-custom=ms-admin-plugin.py ./protocol_admin.proto`

### How to release new version

1. `pip install twine`
2. `python setup.py sdist`
3. `twine upload dist/*`

## メモ

とりあえず中国版で sample.py を動かすことはできた

```
poetry shell
poetry install
python example.py -u **mailAddress** -p **password**
____
wget https://game.maj-soul.com/1/v0.10.297.w/res/proto/liqi.json
```

```
2023-11-19 07:37:19 INFO: Version: {'version': '0.10.301.w', 'force_version': '0.10.0.w', 'code': 'v0.10.301.w/code.js'}
2023-11-19 07:37:19 INFO: Config: {'ip': [{'name': 'player', 'region_urls': [{'url': 'https://mjjpgs.mahjongsoul.com:8443/api/v0/recommend_list', 'ob_url': 'wss://mjjpgs.mahjongsoul.com:5330/ob'}]}], 'goods_sheleve_id': 'shelves_001', 'yo_service_url': ['https://passport.mahjongsoul.com'], 'yo_sdk_js': 'yo_acc.prod_ja.js', 'jp_shop_js': 'https://static.mul-pay.jp/ext/js/token.js', 'jp_shop_id': '9200000213740'}
```

'Traceback (most recent call last):\n File "/Users/xxx/.vscode/extensions/ms-python.python-2023.20.0/pythonFiles/lib/python/debugpy/\_vendored/pydevd/\_pydevd_bundle/pydevd_resolver.py", line 189, in \_get_py_dictionary\n attr = getattr(var, name)\n ^^^^^^^^^^^^^^^^^^\nAttributeError\n'

# kansen.py

モチベとしては、3 たまなんは時間によって土間レベルが全然違うので
3 たま南を定期的に観測して対局者の段位などを取得する（雑打ちする人を観測する）
