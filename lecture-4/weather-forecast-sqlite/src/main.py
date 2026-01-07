import requests
import sqlite3

area_list = [
    ("010000", "北海道"),
    ("020000", "青森県"),
    ("030000", "岩手県"),
    ("040000", "宮城県"),
    ("050000", "秋田県"),
    ("060000", "山形県"),
    ("070000", "福島県"),
    ("080000", "茨城県"),
    ("090000", "栃木県"),
    ("100000", "群馬県"),
    ("110000", "埼玉県"),
    ("120000", "千葉県"),
    ("130000", "東京都"),
    ("140000", "神奈川県"),
    ("150000", "新潟県"),
    ("160000", "富山県"),
    ("170000", "石川県"),
    ("180000", "福井県"),
    ("190000", "山梨県"),
    ("200000", "長野県"),
    ("210000", "岐阜県"),
    ("220000", "静岡県"),
    ("230000", "愛知県"),
    ("240000", "三重県"),
    ("250000", "滋賀県"),
    ("260000", "京都府"),
    ("270000", "大阪府"),
    ("280000", "兵庫県"),
    ("290000", "奈良県"),
    ("300000", "和歌山県"),
    ("310000", "鳥取県"),
    ("320000", "島根県"),
    ("330000", "岡山県"),
    ("340000", "広島県"),
    ("350000", "山口県"),
    ("360000", "徳島県"),
    ("370000", "香川県"),
    ("380000", "愛媛県"),
    ("390000", "高知県"),
    ("400000", "福岡県"),
    ("410000", "佐賀県"),
    ("420000", "長崎県"),
    ("430000", "熊本県"),
    ("440000", "大分県"),
    ("450000", "宮崎県"),
    ("460100", "鹿児島県"),
    ("471000", "沖縄県"),
]

# --- DBとテーブルの準備 ---
conn = sqlite3.connect("../weather.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS area (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER,
    date TEXT,
    text TEXT,
    FOREIGN KEY(area_id) REFERENCES area(id)
)
""")
conn.commit()
conn.close()

# --- 各都道府県分をループ ---
for area_code, area_name in area_list:
    url = f"https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area_code}.json"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        date = data["reportDatetime"]
        text = data["text"]
    except Exception as e:
        print(f"{area_name}（{area_code}） でエラー: {e}")
        continue

    conn = sqlite3.connect("../weather.db")
    cur = conn.cursor()
    # areaテーブル登録
    cur.execute("SELECT id FROM area WHERE code = ?", (area_code,))
    row = cur.fetchone()
    if row:
        area_id = row[0]
    else:
        cur.execute("INSERT INTO area (code, name) VALUES (?, ?)", (area_code, area_name))
        area_id = cur.lastrowid
    # forecast登録
    cur.execute(
        "INSERT INTO forecast (area_id, date, text) VALUES (?, ?, ?)",
        (area_id, date, text)
    )
    conn.commit()
    conn.close()

# --- 表示（JOINで） ---
conn = sqlite3.connect("../weather.db")
cur = conn.cursor()
cur.execute("""
    SELECT f.id, a.name, f.date, f.text
    FROM forecast f
    JOIN area a ON f.area_id = a.id
    ORDER BY a.code, f.date DESC
""")
rows = cur.fetchall()
conn.close()
for row in rows:
    print(f"{row[1]} ({row[2]})")
    print(row[3])
    print("="*40)