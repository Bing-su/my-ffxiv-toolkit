# ffxiv_ko_en_data_concat

파이널판타지14의 영어, 한국어 데이터마이닝 정보를 저장하는 두 저장소,
<https://github.com/xivapi/ffxiv-datamining>와 <https://github.com/Ra-Workspace/ffxiv-datamining-ko>에서 정보를 받아와

영어-한국어 정보를 합친 엑셀 파일을 만듭니다.

## 사용방법

json파일로 정보를 받아올 csv파일의 이름과, 해당 csv파일에서 사용할 열의 이름 정보를 지정합니다.

```shell
python main.py [-j JSON_PATH] [-p SAVE_PATH]
```

`-j, --json`: json파일의 경로, 기본값: `default.json`<br>
`-p, --path`: 파일을 저장할 경로, 기본값: `./data`
