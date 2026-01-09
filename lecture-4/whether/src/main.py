import flet as ft
import requests
import sqlite3

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
WEATHER_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

ken_codes = {
    "北海道": "010000", "青森県": "020000", "岩手県": "030000", "宮城県": "040000",
    "秋田県": "050000", "山形県": "060000", "福島県": "070000",
    "茨城県": "080000", "栃木県": "090000", "群馬県": "100000", "埼玉県": "110000",
    "千葉県": "120000", "東京都": "130000", "神奈川県": "140000", "新潟県": "150000",
    "富山県": "160000", "石川県": "170000", "福井県": "180000", "山梨県": "190000",
    "長野県": "200000", "岐阜県": "210000", "静岡県": "220000", "愛知県": "230000",
    "三重県": "240000", "滋賀県": "250000", "京都府": "260000", "大阪府": "270000",
    "兵庫県": "280000", "奈良県": "290000", "和歌山県": "300000", "鳥取県": "310000",
    "島根県": "320000", "岡山県": "330000", "広島県": "340000", "山口県": "350000",
    "徳島県": "360000", "香川県": "370000", "愛媛県": "380000", "高知県": "390000",
    "福岡県": "400000", "佐賀県": "410000", "長崎県": "420000", "熊本県": "430000",
    "大分県": "440000", "宮崎県": "450000", "鹿児島県": "460100", "沖縄県": "471000"
}

# ★↓↓↓↓【追加：DB初期化＆保存関数】
def init_db():
    conn = sqlite3.connect('weather_app.sqlite3')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pref_code TEXT,
            area_code TEXT,
            area_name TEXT,
            date TEXT,
            day_index INTEGER,
            weather TEXT,
            t_max TEXT,
            t_min TEXT
        )
    ''')
    conn.commit()
    conn.close()

def store_weather(pref_code, area_code, area_name, date, day_index, weather, t_max, t_min):
    conn = sqlite3.connect('weather_app.sqlite3')
    c = conn.cursor()
    c.execute('''
        INSERT INTO weather (pref_code, area_code, area_name, date, day_index, weather, t_max, t_min)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pref_code, area_code, area_name, date, day_index, weather, t_max, t_min))
    conn.commit()
    conn.close()
# ★↑↑↑↑【ここまでDB機能追加】

def weather_to_icon(description):
    if "晴" in description:
        return "☀️"
    elif "曇" in description:
        return "☁️"
    elif "雨" in description:
        return "🌧️"
    elif "雪" in description:
        return "❄️"
    else:
        return "🌈"

def extract_temp(area_code, forecast_data, day_index=0):
    for series in forecast_data.get("timeSeries", []):
        area = next((a for a in series.get("areas", []) if a["area"].get("code") == area_code), None)
        if not area and series.get("areas"):
            area = series["areas"][0]
        if area:
            if "temps" in area:  # 一部都市のみ
                temps = area["temps"]
                t_min = temps[day_index * 2] if len(temps) > day_index * 2 else "--"
                t_max = temps[day_index * 2 + 1] if len(temps) > day_index * 2 + 1 else "--"
                return t_max, t_min
            elif "tempsMax" in area and "tempsMin" in area:
                t_max = area["tempsMax"][day_index] if len(area["tempsMax"]) > day_index else "--"
                t_min = area["tempsMin"][day_index] if len(area["tempsMin"]) > day_index else "--"
                return t_max, t_min
    return "--", "--"

def main(page: ft.Page):
    # ★DB初期化（最初に1回だけ）
    init_db()

    page.title = "都道府県ごとエリア天気"
    page.bgcolor = "#e3f2fd"
    page.padding = 0

    left_controls = ft.Column(
        [
            ft.Container(
                content=ft.Text("都道府県エリア天気アプリ", weight="bold", size=28, color="white"),
                bgcolor="blue",
                padding=18,
                border_radius=18,
                margin=ft.margin.Margin(0,0,0,12),
                width=320,
                alignment=ft.alignment.center
            ),
        ],
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=340,
        expand=False
    )

    ken_menu = ft.Dropdown(
        label="都道府県を選択",
        width=260,
        options=[ft.dropdown.Option(ken) for ken in ken_codes.keys()],
        autofocus=True,
    )
    left_controls.controls.append(
        ft.Card(
            content=ft.Container(
                content=ken_menu,
                padding=12,
                bgcolor="#fff",
                border_radius=14,
                alignment=ft.alignment.center
            )
        )
    )

    output_col = ft.Column(
        spacing=14,
        scroll="always",
        width=700,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    root_row = ft.Row(
        [
            left_controls,
            ft.Container(content=output_col, expand=True, padding=20, bgcolor="#e3f2fd")
        ],
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START
    )
    page.add(root_row)

    try:
        area_json = requests.get(AREA_URL, timeout=20).json()
        class10s = area_json["class10s"]
        code_to_parent = {code: info["parent"] for code, info in class10s.items()}
        code_to_name = {code: info["name"] for code, info in class10s.items()}
    except Exception as e:
        output_col.controls.clear()
        output_col.controls.append(ft.Text(f"エリアデータ取得失敗: {e}", color="red", size=20))
        page.update()
        return

    def on_ken_select(e):
        ken = ken_menu.value
        if not ken:
            output_col.controls.clear()
            output_col.controls.append(ft.Text("都道府県名を選択してください。", color="red", size=20))
            page.update()
            return

        output_col.controls.clear()
        output_col.controls.append(ft.Text(f"{ken}の天気取得中…", color="blue", size=18))
        page.update()

        pref_code = ken_codes[ken]
        area_list = [
            (code, data["name"])
            for code, data in class10s.items()
            if data["parent"] == pref_code
        ]
        if not area_list:
            output_col.controls.clear()
            output_col.controls.append(ft.Text("この都道府県の地域エリアが見つかりません", color="red", size=20))
            page.update()
            return

        try:
            forecast_data = requests.get(WEATHER_URL.format(pref_code), timeout=20).json()[0]
        except Exception as e:
            output_col.controls.clear()
            output_col.controls.append(ft.Text(f"天気データ取得失敗: {repr(e)}", color="red", size=20))
            page.update()
            return
        try:
            weather_areas = forecast_data["timeSeries"][0]["areas"]
        except Exception as e:
            output_col.controls.clear()
            output_col.controls.append(ft.Text(f"天気・気温データ解析失敗: {repr(e)}", color="red", size=20))
            page.update()
            return

        area_weather = {w['area']['name']: w.get('weathers',[None])[0] or "情報なし" for w in weather_areas}
        area_weather_tomorrow = {}
        for w in weather_areas:
            ws = w.get('weathers', [])
            if len(ws) >= 2:
                area_weather_tomorrow[w['area']['name']] = ws[1]
            else:
                area_weather_tomorrow[w['area']['name']] = "情報なし"

        tiles = []
        from datetime import datetime, timedelta
        # 予報作成日時から日付取得
        date_today = forecast_data['reportDatetime'][:10]  # "YYYY-MM-DD"
        # 明日
        dt_tomorrow = datetime.strptime(date_today, "%Y-%m-%d") + timedelta(days=1)
        date_tomorrow = dt_tomorrow.strftime("%Y-%m-%d")

        for i, (code, name) in enumerate(area_list):
            # --- 今日 ---
            t_max_today, t_min_today = extract_temp(code, forecast_data, day_index=0)
            weather_str_today = area_weather.get(name, "情報なし")
            icon_today = weather_to_icon(weather_str_today)

            # --- 明日 ---
            t_max_tomorrow, t_min_tomorrow = extract_temp(code, forecast_data, day_index=1)
            weather_str_tomorrow = area_weather_tomorrow.get(name, "情報なし")
            icon_tomorrow = weather_to_icon(weather_str_tomorrow)

            # ★↓↓↓↓DB保存処理ここで呼ぶ
            store_weather(pref_code, code, name, date_today, 0, weather_str_today, t_max_today, t_min_today)
            store_weather(pref_code, code, name, date_tomorrow, 1, weather_str_tomorrow, t_max_tomorrow, t_min_tomorrow)
            # ★↑↑↑↑

            bgcols = ["#ffe0b2", "#e3f2fd", "#f1f8e9"]
            tile_bg = bgcols[i % len(bgcols)]

            tiles.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(name, weight="bold", color="black", size=21),
                            ft.Row([
                                ft.Text("今日", size=16, weight="bold"), ft.Text(icon_today, size=20), ft.Text(weather_str_today, size=16),
                                ft.Text(f"{t_min_today}°", color="blue", size=16, weight="bold"),
                                ft.Text("/", size=16),
                                ft.Text(f"{t_max_today}°", color="red", size=16, weight="bold"),
                            ], alignment=ft.MainAxisAlignment.START),
                            ft.Row([
                                ft.Text("明日", size=16, weight="bold"), ft.Text(icon_tomorrow, size=20), ft.Text(weather_str_tomorrow, size=16),
                                ft.Text(f"{t_min_tomorrow}°", color="blue", size=16, weight="bold"),
                                ft.Text("/", size=16),
                                ft.Text(f"{t_max_tomorrow}°", color="red", size=16, weight="bold"),
                            ], alignment=ft.MainAxisAlignment.START),
                        ], spacing=4),
                        bgcolor=tile_bg,
                        border_radius=13,
                        padding=16,
                        margin=8,
                        width=620,
                    )
                )
            )

        output_col.controls.clear()
        output_col.controls.append(
            ft.Text(f"{ken} 各エリアの今日・明日の天気と気温", weight="bold", size=22, color="black")
        )
        output_col.controls.extend(tiles)
        page.update()

    ken_menu.on_change = on_ken_select

if __name__ == "__main__":
    ft.app(target=main)