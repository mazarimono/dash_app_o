import json
import datetime
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
import dash_canvas
import dash_bio as dashbio
import dash_cytoscape as cyto

import plotly
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import skimage
import six.moves.urllib.request as urlreq


from dash_canvas.components import image_upload_zone
from dash_canvas.utils import (
    parse_jsonstring,
    superpixel_color_segmentation,
    image_with_contour,
    image_string_to_PILImage,
    array_to_data_url,
)
from dash_canvas.components import image_upload_zone

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# style

external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro&display=swap",
    "https://fonts.googleapis.com/css?family=Noto+Sans+JP&display=swap",
]

title_font = {"fontSize": 60, "fontWeight": "bold", "marginLeft": "3%", "padding": 10}

title_style = {"backgroundColor": "#fbffb9"}


tabs_styles = {"height": "60px"}

tab_style = {
    "borderBottom": "1px solid #d6d6d6",
    "padding": "3px",
    "fontWeight": "bold",
}

tab_selected_style = {
    "borderTop": "1px solid #d6d6d6",
    "borderBottom": "1px solid #d6d6d6",
    "backgroundColor": "#75d701",
    "color": "white",
    "padding": "6px",
}

index_link_style = {"textDecoration": "none", "marginLeft": "10%", "marginTop": "5%"}

mkd_style = {
    "fontSize": 40,
    "width": "80%",
    "margin": "auto",
    "backgroundColor": "white",
    "padding": "3%",
    "borderRadius": 10,
}
mkd_outside_style = {
    "width": "80%",
    "margin": "auto",
    "backgroundColor": "#cbe86e",
    "padding": "3%",
    "borderRadius": 15,
}

# mapbox_accesstoken

mapbox_accesstoken = "pk.eyJ1IjoibWF6YXJpbW9ubyIsImEiOiJjanA5Y3IxaWsxeGtmM3dweDh5bjgydGFxIn0.3vrfsqZ_kGPGhi4_npruGg"


# back_to_index

back_to_index = html.Div(
    [dcc.Link("back_to_index", href="/")],
    style={"fontSize": 30, "marginLeft": "3%", "fontStyle": "Noto Sans JP"},
)

# data_read
# 自動車クイズ解答
df_quiz_car = pd.read_csv("assets/japan_car_own.csv")
quiz_car_xaxis = [1957, 1962, 1967, 1972, 1977, 1982] + [i for i in range(1990, 2020)]

# 3部門クイズ
three_sectors = pd.read_csv("assets/jp-flow.csv", index_col=0)
three_sectors_before_1990 = three_sectors[three_sectors["year"] <= 1990]
three_sectors_after_1990 = three_sectors[three_sectors["year"] >= 1990]
three_sectors_bar = (
    three_sectors[three_sectors["year"] >= 1990].groupby("variable").sum()
)
# プロダクティビティクイズ
productivity_quiz = pd.read_csv("assets/productivity_quiz_data.csv", index_col=0)

# 都道府県GDPクイズ
gdp_index = pd.read_csv("assets/kengdp_standard_long.csv", index_col=0)
gdp_index2 = pd.read_csv("assets/kengdp_standard1990_long.csv", index_col=0)
gdp_index_1975 = gdp_index[gdp_index["variable"] <= 1990]
gdp_index_1990 = gdp_index2[gdp_index2["variable"] >= 1990]

# 家計調査
kakeichosa = pd.read_csv("assets/kakeichosa2000_2019.csv", index_col=0)
kakeichosa_long = pd.read_csv("assets/kakeichosa_long.csv", index_col=0)
# gapminderのグラフ用
gapminder = plotly.data.gapminder()

# 北九州避難所
kitakyushu_hinanjo = pd.read_csv("assets/fukuoka_hinanjo.csv", encoding="shift-jis")

# cytoscape

nodes = [
    {
        "data": {"id": short, "label": label},
        "position": {"x": 20 * lat, "y": -20 * long},
    }
    for short, label, long, lat in (
        ("la", "Los Angeles", 34.03, -118.25),
        ("nyc", "New York", 40.71, -74),
        ("to", "Toronto", 43.65, -79.38),
        ("mtl", "Montreal", 45.50, -73.57),
        ("van", "Vancouver", 49.28, -123.12),
        ("chi", "Chicago", 41.88, -87.63),
        ("bos", "Boston", 42.36, -71.06),
        ("hou", "Houston", 29.76, -95.37),
    )
]

edges = [
    {"data": {"source": source, "target": target}}
    for source, target in (
        ("van", "la"),
        ("la", "chi"),
        ("hou", "chi"),
        ("to", "mtl"),
        ("mtl", "bos"),
        ("nyc", "boston"),
        ("to", "hou"),
        ("to", "nyc"),
        ("la", "nyc"),
        ("nyc", "bos"),
    )
]

elements = nodes + edges

# Dash bio
model_data = urlreq.urlopen(
    "https://raw.githubusercontent.com/plotly/dash-bio-docs-files/master/mol3d/model_data.js"
).read()
styles_data = urlreq.urlopen(
    "https://raw.githubusercontent.com/plotly/dash-bio-docs-files/master/mol3d/styles_data.js"
).read()
model_data = json.loads(model_data)
styles_data = json.loads(styles_data)

# 京都のホテルデータ
df_kyoto_hotels = pd.read_csv("assets/kyoto_hotel_comp.csv", index_col=0)
df_kyoto_hotels_groupby = pd.read_csv("assets/kyoto_hotel_groupby.csv", index_col=0)

# 自動車事故
df_car_accident = pd.read_csv("assets/car_accident_long.csv", index_col=0)
df_car_accident_one = df_car_accident[df_car_accident["variable"] != "死者数"]
df_car_accident_two = df_car_accident[df_car_accident["variable"] == "死者数"]


# canvas_image
filepath = "assets/iam2.jpg"
filename = array_to_data_url(skimage.io.imread(filepath))


# app

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.config.suppress_callback_exceptions = True

server = app.server

app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

# index_page

index_page = html.Div(
    [
        html.Div([html.H1("Today's Menu", style=title_font)], style=title_style),
        html.Div([dcc.Link("1. Introduction", href="/intro", style=index_link_style)]),
        html.Div(
            [dcc.Link("2. About_Dash", href="/about-dash", style=index_link_style)]
        ),
        html.Div(
            [
                dcc.Link(
                    "3. About_Japanese_Economy",
                    href="/about-japanese-economy",
                    style=index_link_style,
                )
            ]
        ),
        html.Div(
            [dcc.Link("4. Epilogue", href="/epilogue", style=index_link_style)]
        ),
        html.Div([
            html.P("今日の資料: https://pyconjp.herokuapp.com", style=index_link_style),
            html.P("Today's Material: https://pyconjp-en.herokuapp.com", style=index_link_style),
            html.P("twitter: @ogawahideyuki", style=index_link_style)
        ])
    ],
    style={"fontSize": 50},
)

# intro_page

intro = html.Div(
    [
        dcc.Tabs(
            id="Tabs",
            children=[
                dcc.Tab(
                    label="title",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Img(
                                    src="assets/chomoku-logo2.png",
                                    style={"width": "20%", "marginLeft": "75%"},
                                ),
                                html.P("Dashとオープンデータで", style={"textAlign": "center"}),
                                html.P(
                                    "日本経済をインタラクティブに可視化する", style={"textAlign": "center"}
                                ),
                            ],
                            style={"marginTop": "5%", "fontSize": 80},
                        ),
                        html.Div(
                            [
                                html.P(
                                    "合同会社 長目　小川　英幸",
                                    style={"textAlign": "right", "fontSize": 50},
                                ),
                                html.P(
                                    "@Pyconjp2019",
                                    style={"textAlign": "right", "fontSize": 50},
                                ),
                            ],
                            style={"margin": "5%", "marginTop": "10%"},
                        ),
                        back_to_index,
                    ],
                ),
                # 自己紹介
                dcc.Tab(
                    label="self_introduce",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [html.H1("こんにちは！", style=title_font)], style=title_style
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            id="my_picture",
                                            src="/assets/iam2.jpg",
                                            style={"width": "80%", "margin": "auto"},
                                        ),
                                        back_to_index,
                                    ],
                                    style={
                                        "width": "40%",
                                        "height": 1300,
                                        "float": "left",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.P("名前: 小川 英幸　@ogawahideyuki"),
                                        html.P("会社: 合同会社 長目（ちょうもく）"),
                                        html.P("資格: 証券アナリスト"),
                                        html.P("頑張ってること: 禁酒"),
                                        html.Img(
                                            src="/assets/hannaripython.PNG",
                                            style={
                                                "width": "60%",
                                                "textAlign": "center",
                                                "marginLeft": "20%",
                                                "marginRight": "20%",
                                            },
                                        ),
                                        html.Img(
                                            src="/assets/pythonkansai.PNG",
                                            style={
                                                "width": "50%",
                                                "textAlign": "center",
                                                "marginLeft": "25%",
                                                "marginRight": "25%",
                                            },
                                        ),
                                    ],
                                    style={
                                        "width": "60%",
                                        "float": "right",
                                        "height": 900,
                                        "fontSize": 40,
                                    },
                                ),
                            ],
                            style={"width": "80%", "margin": "auto"},
                        ),
                    ],
                ),
                # コアとなる哲学
                dcc.Tab(
                    label="core_philosophy",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.H1(
                                    id="overview", children="根本にある哲学", style=title_font
                                )
                            ],
                            style=title_style,
                        ),
                        html.Div(
                            [
                                dcc.Markdown(
                                    """
                - データは可視化するとよく分かる
                - 現在のプレゼンツールはデータを扱いにくい
                - データは時間をかけて分析する価値がある

                """,
                                    style={"fontSize": 50, "margin": "5%"},
                                )
                            ]
                        ),
                        back_to_index,
                    ],
                ),
                # 本日の概要
                dcc.Tab(
                    label="overview",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.H1(
                                    id="overview", children="本日の概要", style=title_font
                                )
                            ],
                            style=title_style,
                        ),
                        html.Div(
                            [
                                dcc.Markdown(
                                    """
                - 経済クイズ
                - 可視化分析フレームワークDash
                    - 今日のプレゼンテーション資料はDashで作成
                    - インタラクティブな可視化により多くのデータが見れる
                    - データの分析、監視、報告がこれひとつでできる
                - 日本経済
                    - 日本の道路は安全になった（今日は話しません）
                    - 気になる！お隣さんのお財布事情！
                - まとめ

                """,
                                    style={"fontSize": 50, "margin": "5%"},
                                )
                            ]
                        ),
                        back_to_index,
                    ],
                ),
                # 消費税クイズ
                dcc.Tab(
                    label="quiz1",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.H1(
                                    id="tax_quiz",
                                    children="問題1",
                                    n_clicks=1,
                                    style=title_font,
                                )
                            ],
                            style=title_style,
                        ),
                        html.Div(
                            children=[
                                dcc.Markdown(
                                    """
                10月から消費税が増税されますが、食料品には軽減税率が適用されます。次のうち軽減税率が適用される商品はいくつあるでしょう？

                ミネラルウォーター、リボビタンD、みりん

                １．３つ

                ２．２つ

                ３．１つ


                """,
                                    style=mkd_style,
                                )
                            ],
                            style=mkd_outside_style,
                        ),
                        html.Div(id="tax_answer", style={"marginTop": "5%"}),
                        back_to_index,
                    ],
                ),
                # 自動車クイズ
                dcc.Tab(
                    label="quiz2",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.H1(
                                    id="quiz-car",
                                    children="問題2",
                                    n_clicks=1,
                                    style=title_font,
                                )
                            ],
                            style=title_style,
                        ),
                        html.Div(
                            id="quiz-car2",
                            n_clicks=1,
                            children=[
                                dcc.Markdown(
                                    """
                1990年（バブルの絶頂期）から2018年の日本の自動車保有台数は？

                1.  30%以上増加した

                2.  横ばい

                3.  30％以上減少した　

                [データソース:　e-Stat 国土交通省　自動車輸送統計月報](https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00600330&kikan=00600&tstat=000001017236&cycle=1&year=20190&month=11010303&stat_infid=000031848511&result_back=1&result_page=1&tclass1val=0)
                """,
                                    style=mkd_style,
                                )
                            ],
                            style=mkd_outside_style,
                        ),
                        html.Div(
                            id="car-graph-quiz-div",
                            children=[
                                dcc.Graph(id="car-graph-quiz", style={"fontSize": 30}),
                                dcc.Interval(
                                    id="car-graph-quiz-interval",
                                    n_intervals=0,
                                    max_intervals=30,
                                    interval=300,
                                ),
                            ],
                            hidden=True,
                            style={"width": "80%", "margin": "auto"},
                        ),
                        back_to_index,
                        #         html.Div(
                        #             [
                        #                 html.H1(
                        #                     id="quiz-deposit",
                        #                     children="問題2",
                        #                     n_clicks=1,
                        #                     style=title_font,
                        #                 )
                        #             ],
                        #             style=title_style,
                        #         ),
                        #         html.Div(
                        #             id="quiz-deposit2",
                        #             n_clicks=1,
                        #             children=[
                        #                 dcc.Markdown(
                        #                     """
                        # スイス、南アフリカ、日本。1990年から2018年の雇用者1人当たり生産性の伸びの日本の順位は？
                        # 1.  1位
                        # 2.  2位
                        # 3.  3位
                        # """,
                        #                     style=mkd_style,
                        #                 )
                        #             ],
                        #             style=mkd_outside_style,
                        #         ),
                        #         html.Div(
                        #             id="deposit-quiz-graph-div",
                        #             children=[
                        #                 dcc.Graph(
                        #                     id="deposit-quiz-graph",
                        #                     figure=px.bar(productivity_quiz, x="Country", y="value", animation_frame="Time", color="Country", range_y=[80, 140]),
                        #                 )
                        #             ],
                        #             style={"width": "80%", "margin": "5% auto 5%"},
                        #         ),
                        #         html.Div([
                        #             html.Button(id="fact-button",
                        #             children="Fact-button",
                        #             n_clicks=0,
                        #             style={"marginLeft":"10%"}
                        #             )
                        #         ]),
                        #         html.Div(id="fact-button-div"),
                        #         back_to_index,
                    ],
                ),
                # 都道府県GDPクイズ
                dcc.Tab(
                    label="quiz3",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.H1(
                                    id="quiz-gdp",
                                    children="問題3",
                                    n_clicks=1,
                                    style=title_font,
                                )
                            ],
                            style=title_style,
                        ),
                        html.Div(
                            id="quiz-gdp2",
                            n_clicks=1,
                            children=[
                                dcc.Markdown(
                                    """
                1990年から2014年の成長率が最も高かった都道府県は？

                1.  徳島     

                2.  大阪    

                3.  沖縄    　

                [データソース: 内閣府統計表（県民経済計算）](https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/files_kenmin.html)
                """,
                                    style=mkd_style,
                                )
                            ],
                            style=mkd_outside_style,
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id="todofuken_gdp_graph",
                                    figure={
                                        "data": [
                                            go.Box(
                                                x=gdp_index_1975["variable"],
                                                y=gdp_index_1975["value"],
                                                hoverlabel={"font": {"size": 30}},
                                            )
                                        ],
                                        "layout": go.Layout(
                                            height=800,
                                            hovermode="closest",
                                            xaxis={"tickfont": {"size": 30}},
                                            title={
                                                "text": "都道府県別GDP（1975年:100 | 1990年まで）",
                                                "font": {"size": 50},
                                            },
                                        ),
                                    },
                                    clickData={"points": [{"x": 1975}]},
                                ),
                                html.Div(
                                    [dcc.Graph(id="todofuken_gdp_bar")],
                                    style={"padding": "2%"},
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            id="show_answer_button",
                                            children="Show answer",
                                            n_clicks=1,
                                            style={"height": 50, "width": 300},
                                        )
                                    ],
                                    style={"margin": "3%"},
                                ),
                            ],
                            style={"marginTop": "3%"},
                        ),
                        back_to_index,
                        html.Div(
                            [dcc.Link("Go_to_about_dash", href="/about-dash")],
                            style={
                                "fontSize": 30,
                                "textAlign": "right",
                                "marginRight": "5%",
                            },
                        ),
                    ],
                ),
                # はんなりPythonの会
                # dcc.Tab(
                #     label="hannari_python",
                #     style=tab_style,
                #     selected_style=tab_selected_style,
                #     children=[
                #         html.Div(
                #             [
                #                 html.Div(
                #                     [html.H2("はんなりPythonの会", style=title_font)],
                #                     style=title_style,
                #                 ),
                #                 html.Img(
                #                     src="/assets/hannaripython.PNG",
                #                     style={
                #                         "width": "60%",
                #                         "textAlign": "center",
                #                         "marginLeft": "20%",
                #                         "marginRight": "20%",
                #                     },
                #                 ),
                #                 html.Div(
                #                     [
                #                         dcc.Markdown(
                #                             """
                # 京都のPythonの勉強会です！
                # 毎月第3金曜日ははんなりPythonの日です。
                # 関西に来られる際はぜひご参加を！！
                # 運営参加も募集中。条件：多く参加！
                # """,
                #                             style=mkd_style,
                #                         )
                #                     ],
                #                     style=mkd_outside_style,
                #                 ),
                #                 back_to_index,
                #             ],
                #             style={"width": "80%", "margin": "auto"},
                #         )
                #     ],
                # ),
                # # Python Kansai
                # dcc.Tab(
                #     label="Python_kansai",
                #     style=tab_style,
                #     selected_style=tab_selected_style,
                #     children=[
                #         html.Div(
                #             [
                #                 html.Div(
                #                     [html.H2("Python Kansai", style=title_font)],
                #                     style=title_style,
                #                 ),
                #                 html.Img(
                #                     src="/assets/pythonkansai.PNG",
                #                     style={
                #                         "width": "50%",
                #                         "textAlign": "center",
                #                         "marginLeft": "25%",
                #                         "marginRight": "25%",
                #                     },
                #                 ),
                #                 html.Div(
                #                     [
                #                         dcc.Markdown(
                #                             """
                # 関西で大きめのPythonのイベントがないので作りました。
                # 3か月に1回くらいのペースで開催します。
                # 1回目にして100人以上の集客！スポンサー募集中！
                # """,
                #                             style=mkd_style,
                #                         )
                #                     ],
                #                     style=mkd_outside_style,
                #                 ),
                #                 back_to_index,
                #                                         html.Div(
                #             [dcc.Link("Go_to_about_dash", href="/about-dash")],
                #             style={"textAlign": "right", "marginRight": "5%"}),
                #             ]
                #         )
                #     ],
                # ),
                # 本日の内容
                # dcc.Tab(
                #     label="Today's Menu",
                #     style=tab_style,
                #     selected_style=tab_selected_style,
                #     children=[
                #         html.Div(
                #             [
                #                 html.Div(
                #                     [html.H1("本日の内容", style=title_font)],
                #                     style=title_style,
                #                 ),
                #                 html.H2("１．可視化分析フレームワークDash", style={"margin": "5%"}),
                #                 html.H2("２．日本って、そんなに悪くないよ（でも頑張ろう！）"),
                #             ],
                #             style={"textAlign": "center"},
                #         ),
                #         html.Div(
                #             [dcc.Link("Go_to_about_dash", href="/about-dash")],
                #             style={"textAlign": "right", "marginRight": "5%"},
                #         ),
                #     ],
                # ),
            ],
            style=tabs_styles,
        )
    ]
)

# 消費税クイズ


@app.callback(Output("tax_answer", "children"), [Input("tax_quiz", "n_clicks")])
def show_tax_answer(n_clicks):
    if n_clicks >= 3:
        return html.Div(
            [
                dcc.Markdown(
                    """
                答え　３．１つ
                
                ミネラルウォーター　８％

                リボビタンD　10％　医薬部外品のため。ちなみにレッドブル、モンスターは炭酸飲料なので８％！

                みりんはお酒が入っているので10％。みりん風調味料はお酒が入っていないので8％。

                """,
                    style=mkd_style,
                )
            ],
            style=mkd_outside_style,
        )


# 自動車クイズコールバック
# 今のままだとクリックミスで動かなくなる。この辺りをどうするか。クリックポイントを分けて誰でも動かせなくしておくのは凄く良い。
# リセットボタンは分かりやすく作っておいても良いかもしれない。エマージェンシーみたいな感じで。


@app.callback(Output("car-graph-quiz-div", "hidden"), [Input("quiz-car", "n_clicks")])
def quiz_car_show_graph(n_clicks):
    if n_clicks == 1:
        return True
    else:
        return False


@app.callback(
    Output("car-graph-quiz", "figure"),
    [Input("quiz-car2", "n_clicks"), Input("car-graph-quiz-interval", "n_intervals")],
)
def quiz_car_update_graph(n_clicks, n_intervals):

    if n_clicks <= 2:
        dff = df_quiz_car[df_quiz_car["年度"] <= 1990]
        return {
            "data": [go.Bar(x=df_quiz_car["年度"], y=dff["合計"])],
            "layout": go.Layout(width=1500, height=800, title="日本の自動車保有台数"),
        }
    elif n_clicks == 3:
        n = 1990 + n_intervals
        dff = df_quiz_car[df_quiz_car["年度"] <= n]
        return {
            "data": [go.Bar(x=quiz_car_xaxis, y=dff["合計"])],
            "layout": go.Layout(width=1500, height=800, title="日本の自動車保有台数"),
        }
    else:
        return {
            "data": [go.Bar(x=df_quiz_car["年度"], y=df_quiz_car["合計"])],
            "layout": go.Layout(
                width=1500,
                height=800,
                title="日本の自動車保有台数",
                annotations=[
                    {
                        "x": 1990,
                        "y": df_quiz_car[df_quiz_car["年度"] == 1990]["合計"].values[0],
                        "text": "1990: {}".format(
                            df_quiz_car[df_quiz_car["年度"] == 1990]["合計"].values[0]
                        ),
                        "font": {"size": 30, "color": "red"},
                        "ay": 100,
                        "arrowhead": 2,
                    },
                    {
                        "x": 2018,
                        "y": df_quiz_car[df_quiz_car["年度"] == 2018]["合計"].values[0],
                        "text": "2018: {}".format(
                            df_quiz_car[df_quiz_car["年度"] == 2018]["合計"].values[0]
                        ),
                        "font": {"size": 30, "color": "blue"},
                        "arrowhead": 2,
                    },
                ],
            ),
        }


@app.callback(
    Output("car-graph-quiz-interval", "n_intervals"), [Input("quiz-car2", "n_clicks")]
)
def reset_car_n_intervals(n_clicks):
    if n_clicks > 0:
        return 0


@app.callback(Output("fact-button-div", "children"), [Input("fact-button", "n_clicks")])
def show_the_fact(n_clicks):
    if n_clicks % 2 == 1:
        return html.Div(
            [
                dcc.Markdown(
                    """
                ちなみに、日本の1990年からの雇用者1人当たりの労働生産性の伸びは、
                OECDでデータが取れる29か国中、下から6番目。


                """,
                    style=mkd_style,
                )
            ],
            style=mkd_outside_style,
        )


# 3部門クイズコールバック


# @app.callback(
#     Output("deposit-quiz-graph", "figure"), [Input("quiz-deposit2", "n_clicks")]
# )
# def deposit_quiz_callback(quiz_click):
#     if quiz_click % 3 == 2:

#         return {
#             "data": [
#                 go.Scatter(
#                     x=three_sectors_after_1990[
#                         three_sectors_after_1990["variable"] == i
#                     ]["year"],
#                     y=three_sectors_after_1990[
#                         three_sectors_after_1990["variable"] == i
#                     ]["value"],
#                     name=i,
#                     mode="lines",
#                     hoverlabel={"font": {"size": 30}},
#                 )
#                 for i in three_sectors_after_1990["variable"].unique()
#             ],
#             "layout": go.Layout(
#                 height=800,
#                 title={"text": "1990年以降のフロー", "font": {"size": 30}},
#                 xaxis={"tickfont": {"size": 30}},
#             ),
#         }
#     elif quiz_click % 3 == 0:
#         return {
#             "data": [
#                 go.Bar(
#                     x=three_sectors_bar.index,
#                     y=three_sectors_bar["value"],
#                     hoverlabel={"font": {"size": 30}},
#                 )
#             ],
#             "layout": go.Layout(
#                 height=800,
#                 title={"text": "1990年以降の資金余剰", "font": {"size": 30}},
#                 xaxis={"tickfont": {"size": 30}},
#             ),
#         }

#     else:
#         return {
#             "data": [
#                 go.Scatter(
#                     x=three_sectors_before_1990[
#                         three_sectors_before_1990["variable"] == i
#                     ]["year"],
#                     y=three_sectors_before_1990[
#                         three_sectors_before_1990["variable"] == i
#                     ]["value"],
#                     hoverlabel={"font": {"size": 30}},
#                     name=i,
#                     mode="lines",
#                 )
#                 for i in three_sectors_before_1990["variable"].unique()
#             ],
#             "layout": go.Layout(
#                 height=800,
#                 title={"text": "1990年までのフロー", "font": {"size": 30}},
#                 xaxis={"tickfont": {"size": 30}},
#             ),
#         }


# 都道府県GDPクイズ
@app.callback(
    Output("todofuken_gdp_bar", "figure"),
    [
        Input("todofuken_gdp_graph", "clickData"),
        Input("show_answer_button", "n_clicks"),
    ],
)
def ken_gdp_show(clickData, n_clicks):

    click_year = clickData["points"][0]["x"]
    if n_clicks % 2 == 1:
        dff = gdp_index[gdp_index["variable"] == int(click_year)].sort_values("value")
        return {
            "data": [
                go.Bar(x=dff["都道府県"], y=dff["value"], hoverlabel={"font": {"size": 30}})
            ],
            "layout": go.Layout(
                xaxis={"tickfont": {"size": 30}},
                title={"text": "各都道府県の{}年のGDPの成長率".format(click_year), "font": {"size": 35}},
            ),
        }

    else:
        dff = gdp_index2[gdp_index2["variable"] == int(click_year)].sort_values("value")
        return {
            "data": [
                go.Bar(x=dff["都道府県"], y=dff["value"], hoverlabel={"font": {"size": 30}})
            ],
            "layout": go.Layout(
                xaxis={"tickfont": {"size": 30}},
                title={"text": "各都道府県の{}年のGDPの状態".format(click_year), "font": {"size": 35}},
            ),
        }


@app.callback(
    [
        Output("todofuken_gdp_graph", "figure"),
        Output("todofuken_gdp_graph", "clickData"),
    ],
    [Input("show_answer_button", "n_clicks")],
)
def show_todofuken_gdp_answer(n_clicks):

    if n_clicks % 2 == 0:
        return (
            {
                "data": [
                    go.Box(
                        x=gdp_index_1990["variable"],
                        y=gdp_index_1990["value"],
                        hoverlabel={"font": {"size": 30}},
                    )
                ],
                "layout": go.Layout(
                    height=800,
                    hovermode="closest",
                    xaxis={"tickfont": {"size": 30}},
                    title={
                        "text": "都道府県別GDP（1990年:100 | 2014年まで）",
                        "font": {"size": 50},
                    },
                ),
            },
            {"points": [{"x": 1990}]},
        )
    else:
        return (
            {
                "data": [
                    go.Box(
                        x=gdp_index_1975["variable"],
                        y=gdp_index_1975["value"],
                        hoverlabel={"font": {"size": 30}},
                    )
                ],
                "layout": go.Layout(
                    height=800,
                    hovermode="closest",
                    xaxis={"tickfont": {"size": 30}},
                    title={
                        "text": "都道府県別GDP（1975年:100 | 1990年まで）",
                        "font": {"size": 50},
                    },
                ),
            },
            {"points": [{"x": 1975}]},
        )


# about_dash

about_dash = html.Div(
    [
        dcc.Tabs(
            id="Tabs",
            children=[
                dcc.Tab(
                    label="Dash",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [html.H1("Dashとは", style=title_font)],
                                    style=title_style,
                                ),
                                dcc.Markdown(
                                    """
                - Dashは分析ウェブフレームワーク
                    - Pythonのみで書ける
                    - Flask、plotly.js、react.jsで作られている
                    - [Document](https://dash.plot.ly/)

                - インタラクティブにデータが可視化、共有できる
                    - たくさんのデータが見れる
                    - そのデータを共有できる
                
                - グラフ以外にもさまざまなコンポーネントが存在する
                    - Dash_table、Dash_Canvas、Dash_Bioなどがある
                    - 自作できる

                """,
                                    style={"fontSize": 50, "margin": "5%"},
                                ),
                                back_to_index,
                            ]
                        )
                    ],
                ),
                dcc.Tab(
                    label="Dash-Code",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    children=[
                                        html.Div(
                                            [
                                                html.H1(
                                                    "Dashのアプリケーションの作り方",
                                                    style=title_font,
                                                )
                                            ],
                                            style=title_style,
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    id="hello-graph",
                                                    figure={
                                                        "data": [
                                                            {
                                                                "x": [1, 2, 3],
                                                                "y": [2, 3, 4],
                                                                "type": "bar",
                                                                "name": "Kyoto",
                                                            },
                                                            {
                                                                "x": [1, 2, 3],
                                                                "y": [4, 2, 4],
                                                                "type": "bar",
                                                                "name": "Tokyo",
                                                            },
                                                            {
                                                                "x": [1, 2, 3],
                                                                "y": [3, 1, 4],
                                                                "type": "bar",
                                                                "name": "Osaka",
                                                            },
                                                        ],
                                                        "layout": {
                                                            "title": "Dash DataViz",
                                                            "height": 600,
                                                        },
                                                    },
                                                ),
                                                html.Div(id="hello-graph-callback", style={"fontSize":30}),
                                            ],
                                            style={"width": "70%", "margin": "auto"},
                                        ),
                                    ]
                                )
                            ]
                        ),
                        html.Div(
                            [
                                html.P("コード", style={"fontSize": 30}),
                                dcc.Markdown(
                                    """

            import dash     
            import dash_core_components as dcc     
            import dash_html_components as html     

            app = dash.Dash()

            \# レイアウトの作成

            app.layout = html.Div(

                children=[
                    dcc.Graph(
                        id="hello-graph",
                        figure={
                            "data": [
                                {"x": [1, 2, 3], "y": [2, 3, 4],
                                  "type": "bar", "name": "Kyoto"},
                                {"x": [1, 2, 3], "y": [4, 2, 4],
                                  "type": "bar", "name": "Tokyo"},
                                {"x": [1, 2, 3], "y": [3, 1, 4],
                                  "type": "bar", "name": "Osaka"},
                                ],
                            "layout": {"title": "Dash DataViz", "height": 800},
                        },
                    ),
                    html.Div(id="hello-graph-callback", style={"fontSize":30}),
                ]
            )

            \# コールバックの作成

            @app.callback(Output("hello-graph-callback", "children"),       
                        \[Input("hello-graph", "hoverData")\]\)         
            def hello_graph_callback(hoverData):      

                return json.dumps(hoverData)     

            app.run_server(debug=True)


            """,
                                    style={
                                        "fontSize": 30,
                                        "width": "80%",
                                        "margin": "auto",
                                        "backgroundColor": "white",
                                        "padding": "3%",
                                        "borderRadius": 10,
                                    },
                                ),
                            ],
                            style={
                                "width": "80%",
                                "margin": "auto",
                                "backgroundColor": "#cbe86e",
                                "padding": "3%",
                                "borderRadius": 15,
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [html.P("グラフモジュールの話", style=title_font)],
                                    style=title_style,
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "家計調査2000年から2019年6月まで",
                                                    style={"textAlign": "center"},
                                                ),
                                                dcc.Dropdown(
                                                    id="drop1",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in kakeichosa.columns
                                                    ],
                                                    value="世帯人員(人)",
                                                    style={
                                                        "width": "40%",
                                                        "display": "inline-block",
                                                    },
                                                ),
                                                dcc.Dropdown(
                                                    id="drop2",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in kakeichosa.columns
                                                    ],
                                                    value="世帯主の年齢(歳)",
                                                    style={
                                                        "width": "40%",
                                                        "diplay": "inline-block",
                                                    },
                                                ),
                                                dcc.RadioItems(
                                                    id="kakei-radioitems",
                                                    options=[
                                                        {
                                                            "label": "plotly.graph_objects",
                                                            "value": "plotly.graph_objects",
                                                        },
                                                        {
                                                            "label": "dash",
                                                            "value": "dash",
                                                        },
                                                        {
                                                            "label": "plotly.express",
                                                            "value": "plotly.express",
                                                        },
                                                    ],
                                                    value="plotly.graph_objects",
                                                    labelStyle={"marginRight": "2%"},
                                                    style={"fontSize": 40},
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    id="looking_for_con",
                                                    style={"fontSize": 30},
                                                )
                                            ],
                                            style={
                                                "fontSize": 30,
                                                "width": "80%",
                                                "margin": "auto",
                                            },
                                        ),
                                        html.Div(
                                            id="kakei-plot-code",
                                            style=mkd_outside_style,
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        back_to_index,
                    ],
                ),
                # Dash app samples
                dcc.Tab(
                    label="dash_apps_sample",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [html.H1("各コンポーネントを使ったアプリケーション", style=title_font)],
                                    style=title_style,
                                ),
                                # Dash_canvas
                                html.Div(
                                    [
                                        html.H3(
                                            "Dash Canvas", style={"textAlign": "center"}
                                        ),
                                        html.Div(
                                            [
                                                dash_canvas.DashCanvas(
                                                    id="canvas-bg",
                                                    width=500,
                                                    filename=filename,
                                                    lineWidth=8,
                                                    goButtonTitle="Remove background",
                                                    hide_buttons=[
                                                        "line",
                                                        "zoom",
                                                        "pan",
                                                    ],
                                                )
                                            ],
                                            style={
                                                "display": "inline-block",
                                                "marginRight": "5%",
                                            },
                                        ),
                                        html.Div(
                                            [html.Img(id="seg-image", width=500)],
                                            style={"display": "inline-block"},
                                        ),
                                        html.Div(
                                            [
                                                dcc.Link(
                                                    "Dash Canvas Document",
                                                    href="https://dash.plot.ly/canvas",
                                                )
                                            ],
                                            style={"margin": "5%"},
                                        ),
                                    ],
                                    style={"width": "60%", "margin": "3% auto 3%"},
                                ),
                                # cytoscape
                                html.Div(
                                    [
                                        html.H3(
                                            "Dash Cytoscape",
                                            style={"textAlign": "center"},
                                        ),
                                        dcc.Dropdown(
                                            id="dropdown-update-layout",
                                            value="grid",
                                            clearable=False,
                                            options=[
                                                {
                                                    "label": name.capitalize(),
                                                    "value": name,
                                                }
                                                for name in [
                                                    "grid",
                                                    "random",
                                                    "circle",
                                                    "cose",
                                                    "concentric",
                                                ]
                                            ],
                                            style={"width": "50%"},
                                        ),
                                        cyto.Cytoscape(
                                            id="cytoscape-update-layout",
                                            layout={"name": "grid"},
                                            style={"width": "100%", "height": "450px"},
                                            elements=elements,
                                        ),
                                        dcc.Link(
                                            "Dash Cytoscape Document",
                                            href="https://dash.plot.ly/cytoscape",
                                            style={"margin": "5%"},
                                        ),
                                    ],
                                    style={"width": "80%", "margin": "5% auto 5%"},
                                ),
                                # Gapminder
                                # html.Div(
                                #     [
                                #         html.P(
                                #             "Gapminder Graph", style={"fontSize": 30}
                                #         ),
                                #         dcc.Graph(
                                #             figure=px.scatter(
                                #                 gapminder,
                                #                 x="gdpPercap",
                                #                 y="lifeExp",
                                #                 size="pop",
                                #                 color="continent",
                                #                 animation_frame="year",
                                #                 hover_name="country",
                                #                 range_y=[
                                #                     gapminder["lifeExp"].min() - 10,
                                #                     gapminder["lifeExp"].max() + 10,
                                #                 ],
                                #                 log_x=True,
                                #                 size_max=60,
                                #                 height=800,
                                #             )
                                #         ),
                                #     ],
                                #     style={"width": "80%", "margin": "3% auto 3%"},
                                # ),
                                # kitakyushu
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Dash Table",
                                                    style={"textAlign": "center"},
                                                ),
                                                DataTable(
                                                    id="fukuoka-datatable",
                                                    style_cell={
                                                        "textAlign": "center",
                                                        "maxWidth": "80px",
                                                        "whiteSpace": "normal",
                                                        "minWidth": "80px",
                                                    },
                                                    fixed_rows={
                                                        "headers": True,
                                                        "data": 0,
                                                    },
                                                    style_table={
                                                        "maxHeight": 800,
                                                        "maxWidth": "100%",
                                                    },
                                                    filter_action="native",
                                                    row_selectable="multi",
                                                    sort_action="native",
                                                    sort_mode="multi",
                                                    page_size=700,
                                                    virtualization=True,
                                                    columns=[
                                                        {
                                                            "name": i,
                                                            "id": i,
                                                            "deletable": True,
                                                        }
                                                        for i in kitakyushu_hinanjo.columns
                                                    ],
                                                    data=kitakyushu_hinanjo.to_dict(
                                                        "records"
                                                    ),
                                                ),
                                            ],
                                            # データテーブルにスタイルを与え、サイズを小さくする
                                            style={
                                                "height": 400,
                                                "width": "80%",
                                                "margin": "2% auto 5%",
                                            },
                                        ),
                                        # mapboxのアクセストークンを読み込む
                                        px.set_mapbox_access_token(
                                            "pk.eyJ1IjoibWF6YXJpbW9ubyIsImEiOiJjanA5Y3IxaWsxeGtmM3dweDh5bjgydGFxIn0.3vrfsqZ_kGPGhi4_npruGg"
                                        ),
                                        # mapのコールバック先のGraphクラス
                                        dcc.Graph(id="fukuoka-map"),
                                        html.Div(
                                            [
                                                dcc.Link(
                                                    "Dash DataTable Document",
                                                    href="https://dash.plot.ly/datatable",
                                                    style={"margin": "5%"},
                                                )
                                            ]
                                        ),
                                        dcc.Link(
                                            "データソース: 北九州市　避難場所・避難所",
                                            href="https://ckan.open-governmentdata.org/dataset/401005_hinanbasyo",
                                            style={"marginLeft": "75%"},
                                        ),
                                    ]
                                ),
                                # dash_bio
                                html.Div(
                                    [
                                        html.H3(
                                            "Dash bio", style={"textAlign": "center"}
                                        ),
                                        dashbio.Molecule3dViewer(
                                            styles=styles_data,
                                            modelData=model_data,
                                            selectionType="Chain",
                                        ),
                                    ],
                                    style={
                                        "height": 800,
                                        "width": "90%",
                                        "margin": "auto",
                                    },
                                ),
                                dcc.Link(
                                    "Dash Bio Document",
                                    href="https://dash.plot.ly/dash-bio",
                                    style={"margin": "5%"},
                                ),
                                back_to_index,
                            ]
                        )
                    ],
                ),
                # Dash data sharing
                dcc.Tab(
                    label="dash_app_share",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [html.H1("Dashを使い、詳細なデータを共有し、データ分析をより深いレベルで行う", style=title_font)],
                                    style=title_style,
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "データ分析の問題点: データ分析に対する理解の隔たりとデータ分析結果の共有の難しさ",
                                            style={"fontSize": 40},
                                        ),
                                        dcc.Markdown(
                                            """
                    ### 事例（想像上）
                    - データ分析に関して      
                        - 依頼側: 人工知能がチャーっとすぐに効果が！！     
                        - 分析側:　業務のドメイン知識の共有など協力が必要      
                    - 結果などの共有      
                        - 分析側: 依頼者にしっかり報告しましたよ！      
                        - 依頼側: 見たいデータがなかった・・・      
                    """,
                                            style=mkd_style,
                                        ),
                                    ],
                                    style=mkd_outside_style,
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "Dashで詳細なデータを共有してその隔たりを埋め、データの理解を深化させましょう!",
                                            style={
                                                "fontSize": 40,
                                                "textAlign": "center",
                                                "backgroundColor": "#fbffb9",
                                                "padding": 10,
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "良くプレゼンで見るグラフ",
                                                    style={"fontSize": 40},
                                                ),
                                                html.P(
                                                    "京都の宿泊所の増加", style={"fontSize": 30}
                                                ),
                                                dcc.Graph(
                                                    figure={
                                                        "data": [
                                                            go.Bar(
                                                                x=df_kyoto_hotels_groupby[
                                                                    "year"
                                                                ],
                                                                y=df_kyoto_hotels_groupby[
                                                                    "count"
                                                                ],
                                                            )
                                                        ]
                                                    }
                                                ),
                                                dcc.Link(
                                                    "データソース: 京都市オープンデータポータルサイト　旅館業法に基づく許可施設一覧",
                                                    href="https://data.city.kyoto.lg.jp/node/100228",
                                                    style={"marginLeft": "50%"},
                                                ),
                                                html.P(
                                                    "最近増えたことは分かる",
                                                    style={"fontSize": 40},
                                                ),
                                                html.P(
                                                    "それ以外分からない => 情報不足",
                                                    style={"fontSize": 40},
                                                ),
                                            ],
                                            style={
                                                "width": "80%",
                                                "margin": "2% auto 5%",
                                            },
                                        ),
                                        html.P(
                                            "情報量を増やす",
                                            style={
                                                "fontSize": 40,
                                                "textAlign": "center",
                                                "backgroundColor": "#fbffb9",
                                                "padding": 10,
                                            },
                                        ),
                                        html.H4(
                                            id="year-number",
                                            style={"textAlign": "center"},
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    id="kyoto-hotel-bar",
                                                    figure={
                                                        "data": [
                                                            go.Bar(
                                                                x=df_kyoto_hotels_groupby[
                                                                    "year"
                                                                ],
                                                                y=df_kyoto_hotels_groupby[
                                                                    "count"
                                                                ],
                                                            )
                                                        ]
                                                    },
                                                    clickData={
                                                        "points": [{"x": "all"}]
                                                    },
                                                ),
                                                dcc.Graph(
                                                    id="kyoto-hotelmap-yearcallback"
                                                ),
                                                dcc.Link(
                                                    "データソース: 京都市オープンデータポータルサイト　旅館業法に基づく許可施設一覧",
                                                    href="https://data.city.kyoto.lg.jp/node/100228",
                                                    style={"marginLeft": "50%"},
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Markdown(
                                                            """
                        - 情報量が増えるとわかることも増える
                        - もっと掘り下げたいところが分かる
                        ### 顧客と分析者の隔たりが埋まり、データの理解が深まり、データ分析の効果が上昇する
                        """,
                                                            style=mkd_style,
                                                        )
                                                    ],
                                                    style={
                                                        "width": "80%",
                                                        "margin": "2% auto 2%",
                                                    },
                                                ),
                                            ],
                                            style=mkd_outside_style,
                                        ),
                                    ]
                                ),
                                back_to_index,
                                html.Div(
                                    [
                                        dcc.Link(
                                            "Go_to_about_japanese_economy",
                                            href="/about-japanese-economy",
                                        )
                                    ],
                                    style={
                                        "fontSize": 30,
                                        "textAlign": "right",
                                        "marginRight": "5%",
                                    },
                                ),
                            ]
                        )
                    ],
                ),
            ],
            style=tabs_styles,
        )
    ]
)

# hello-callback
@app.callback(Output("hello-graph-callback", "children"),
            [Input("hello-graph", "hoverData")])
def hello_graph_callback(hoverData):
    return json.dumps(hoverData)

# kakei callbacks


@app.callback(
    [Output("looking_for_con", "figure"), Output("kakei-plot-code", "children")],
    [
        Input("drop1", "value"),
        Input("drop2", "value"),
        Input("kakei-radioitems", "value"),
    ],
)
def update_chart(value1, value2, radiovalue):
    if radiovalue == "plotly.express":
        return [
            px.scatter(kakeichosa, x=value1, y=value2, height=600),
            dcc.Markdown(
                """
            plotly.expressでグラフを描く場合     

            px.scatter(kakeichosa, x=value1, y=value2, height=600)

            [データソース: e-Stat 家計調査](https://www.e-stat.go.jp/stat-search?page=1&toukei=00200561&survey=%E5%AE%B6%E8%A8%88%E8%AA%BF%E6%9F%BB)
        """,
                style=mkd_style,
            ),
        ]
    elif radiovalue == "plotly.graph_objects":
        dff1 = kakeichosa_long[kakeichosa_long["variable"] == value1]
        dff2 = kakeichosa_long[kakeichosa_long["variable"] == value2]
        return [
            {
                "data": [
                    go.Scatter(
                        x=dff1["value"],
                        y=dff2["value"],
                        hoverlabel={"font": {"size": 30}},
                        mode="markers",
                    )
                ],
                "layout": go.Layout(
                    height=600,
                    xaxis={"title": {"text": value1, "font": {"size": 30}}},
                    yaxis={"title": {"text": value2, "font": {"size": 30}}},
                ),
            },
            dcc.Markdown(
                """
            plotly.graph_objectsでグラフを描く場合     

            {"data": [go.Scatter(x=dff1\[\"value"\], y=dff2\[\"value"\],  mode="markers")],     
                "layout": go.Layout(height=600, xaxis={"title": value1}, yaxis={"title": value2})}     

            [データソース: e-Stat 家計調査](https://www.e-stat.go.jp/stat-search?page=1&toukei=00200561&survey=%E5%AE%B6%E8%A8%88%E8%AA%BF%E6%9F%BB)
            """,
                style=mkd_style,
            ),
        ]
    else:
        dff1 = kakeichosa_long[kakeichosa_long["variable"] == value1]
        dff2 = kakeichosa_long[kakeichosa_long["variable"] == value2]
        return [
            {
                "data": [
                    {
                        "x": dff1["value"],
                        "y": dff2["value"],
                        "hoverlabel": {"font": {"size": 30}},
                        "mode": "markers",
                    }
                ],
                "layout": {
                    "height": 600,
                    "xaxis": {"title": {"text": value1, "font": {"size": 30}}},
                    "yaxis": {"title": {"text": value2, "font": {"size": 30}}},
                    "plot_bgcolor": "ash",
                },
            },
            dcc.Markdown(
                """
            Dashでグラフを描く場合    

            {"data": [{"x": dff1\[\"value"\], "y":dff2\[\"value"\], "mode":"markers"}],     
                "layout": {"height": 600, "xaxis": {"title": value1}, "yaxis":{"title": value2}}}      

            [データソース: e-Stat 家計調査](https://www.e-stat.go.jp/stat-search?page=1&toukei=00200561&survey=%E5%AE%B6%E8%A8%88%E8%AA%BF%E6%9F%BB)
            """,
                style=mkd_style,
            ),
        ]


# kitakyushu


@app.callback(
    # 出力先はGraphクラス
    Output("fukuoka-map", "figure"),
    [
        # 入力元はデータテーブル
        Input("fukuoka-datatable", "columns"),
        Input("fukuoka-datatable", "derived_virtual_data"),
    ],
)
def update_map(columns, rows):
    # ソートした後のデータでデータテーブルを作成する
    kitakyushu_hinanjof = pd.DataFrame(rows, columns=[c["name"] for c in columns])
    # そのデータを地図に示す
    return px.scatter_mapbox(
        kitakyushu_hinanjof,
        lat="緯度",
        lon="経度",
        zoom=10,
        hover_data=["名称", "名称かな表記", "住所表記"],
        labels={"fontSize": 20},
    )


# Dash canvas callback


@app.callback(
    Output("seg-image", "src"),
    [Input("canvas-bg", "json_data"), Input("canvas-bg", "image_content")],
)
def update_figure(string, image):
    if string:
        if image is None:
            im = skimage.io.imread(filepath)
        else:
            im = image_string_to_PILImage(image)
            im = np.asarray(im)
        shape = im.shape[:2]
        try:
            mask = parse_jsonstring(string, shape=shape)
        except IndexError:
            raise PreventUpdate
        if mask.sum() > 0:
            seg = superpixel_color_segmentation(im, mask)
        else:
            seg = np.ones(shape)
        fill_value = 255 * np.ones(3, dtype=np.uint8)
        dat = np.copy(im)
        dat[np.logical_not(seg)] = fill_value
        return array_to_data_url(dat)
    else:
        raise PreventUpdate


# cytoscape_callback


@app.callback(
    Output("cytoscape-update-layout", "layout"),
    [Input("dropdown-update-layout", "value")],
)
def update_layout(layout):
    return {"name": layout, "animate": True}


# kyoto-map-sample-chart-callbacks


@app.callback(
    [
        dash.dependencies.Output("kyoto-map", "figure"),
        dash.dependencies.Output("kyoto-title", "children"),
    ],
    [
        dash.dependencies.Input("interval-comp", "n_intervals"),
        dash.dependencies.Input("kyoto-button", "n_clicks"),
    ],
)
def update_graph(n_intervals, n_clicks):
    if n_clicks % 2 == 0:
        cnt = n_intervals % 83
        dff = df_kyoto_hotels[
            df_kyoto_hotels["year"] <= df_kyoto_hotels["year"].min() + cnt
        ]
        return (
            {
                "data": [
                    go.Scattermapbox(
                        lat=dff["ido"],
                        lon=dff["keido"],
                        mode="markers",
                        marker=dict(size=9),
                        # name=dff["hotel_name"]
                    )
                ],
                "layout": go.Layout(
                    autosize=True,
                    hovermode="closest",
                    mapbox=dict(
                        accesstoken=mapbox_accesstoken,
                        center=dict(
                            lat=np.mean(df_kyoto_hotels["ido"]),
                            lon=np.mean(df_kyoto_hotels["keido"]),
                        ),
                        pitch=90,
                        zoom=12,
                    ),
                    height=899,
                ),
            },
            "{}年の京都宿泊所状況: {}か所".format(df_kyoto_hotels["year"].min() + cnt, len(dff)),
        )

    else:
        return (
            {
                "data": [
                    go.Scattermapbox(
                        lat=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["ido"],
                        lon=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["keido"],
                        mode="markers",
                        marker=dict(size=9),
                        text=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["hotel_name"],
                        name=str(i),
                    )
                    for i in df_kyoto_hotels["age"].unique()
                ],
                "layout": go.Layout(
                    autosize=True,
                    hovermode="closest",
                    mapbox=dict(
                        accesstoken=mapbox_accesstoken,
                        center=dict(
                            lat=np.mean(df_kyoto_hotels["ido"]),
                            lon=np.mean(df_kyoto_hotels["keido"]),
                        ),
                        pitch=90,
                        zoom=12,
                    ),
                    height=899,
                ),
            },
            "{}年の京都宿泊所状況: {}か所".format(
                df_kyoto_hotels["year"].max(), len(df_kyoto_hotels)
            ),
        )


@app.callback(
    dash.dependencies.Output("interval-comp", "n_intervals"),
    [dash.dependencies.Input("kyoto-button", "n_clicks")],
)
def count_zero(n_clicks):
    return 0


# app_share_kyoto_hotels_callback


@app.callback(
    [
        Output("kyoto-hotelmap-yearcallback", "figure"),
        Output("year-number", "children"),
    ],
    [Input("kyoto-hotel-bar", "clickData")],
)
def update_map(clickData):
    data_x = clickData["points"][0]["x"]
    dff = df_kyoto_hotels[df_kyoto_hotels["year"] == data_x]
    dff_amount = df_kyoto_hotels_groupby[df_kyoto_hotels_groupby["year"] == data_x]
    if data_x == "all":
        return (
            {
                "data": [
                    go.Scattermapbox(
                        lat=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["ido"],
                        lon=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["keido"],
                        mode="markers",
                        marker=dict(size=9),
                        text=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["hotel_name"],
                        name=str(i),
                    )
                    for i in df_kyoto_hotels["age"].unique()
                ],
                "layout": go.Layout(
                    autosize=True,
                    hovermode="closest",
                    mapbox=dict(
                        accesstoken=mapbox_accesstoken,
                        center=dict(
                            lat=np.mean(df_kyoto_hotels["ido"]),
                            lon=np.mean(df_kyoto_hotels["keido"]),
                        ),
                        pitch=90,
                        zoom=12,
                    ),
                    height=600,
                ),
            },
            "京都の宿泊施設は2018年現在： {}件です".format(len(df_kyoto_hotels)),
        )
    elif data_x == 1946:
        return (
            {
                "data": [
                    go.Scattermapbox(
                        lat=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["ido"],
                        lon=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["keido"],
                        mode="markers",
                        marker=dict(size=9),
                        text=df_kyoto_hotels[df_kyoto_hotels["age"] == i]["hotel_name"],
                        name=str(i),
                    )
                    for i in df_kyoto_hotels["age"].unique()
                ],
                "layout": go.Layout(
                    autosize=True,
                    hovermode="closest",
                    mapbox=dict(
                        accesstoken=mapbox_accesstoken,
                        center=dict(
                            lat=np.mean(df_kyoto_hotels["ido"]),
                            lon=np.mean(df_kyoto_hotels["keido"]),
                        ),
                        pitch=90,
                        zoom=12,
                    ),
                    height=600,
                ),
            },
            "京都の宿泊施設は2018年現在： {}件です".format(len(df_kyoto_hotels)),
        )
    else:
        return (
            {
                "data": [
                    go.Scattermapbox(
                        lat=dff["ido"],
                        lon=dff["keido"],
                        mode="markers",
                        marker=dict(size=9),
                        text=dff["hotel_name"],
                    )
                ],
                "layout": go.Layout(
                    autosize=True,
                    hovermode="closest",
                    mapbox=dict(
                        accesstoken=mapbox_accesstoken,
                        center=dict(
                            lat=np.mean(df_kyoto_hotels["ido"]),
                            lon=np.mean(df_kyoto_hotels["keido"]),
                        ),
                        pitch=90,
                        zoom=12,
                    ),
                    height=600,
                ),
            },
            "{}年は{}件の宿泊施設ができました".format(data_x, dff_amount["count"].values[0]),
        )


dogFrame = pd.read_csv("assets/dogFrame.csv", index_col=0)
world_car_accidents = pd.read_csv("assets/road_kill_rate.csv", index_col=0)
df_elderly = pd.read_csv("assets/elderly.csv", index_col=0)
elderly_acc_ratio = df_elderly[df_elderly["Type"] == "ratio_over65"]
elderly_pop_ratio = df_elderly[df_elderly["Type"] == "elderly_pop_ratio"]
acc_age_data = pd.read_csv("assets/acc_age_data.csv", index_col=0)

shouhi_jittai = pd.read_csv("assets/shouhi_all_long2.csv", index_col=0)
oecd_annual_wage = pd.read_csv("assets/annual_wage.csv", index_col=0)
oecd_productivity = pd.read_csv("assets/productivity.csv")
houjin_tokei = pd.read_csv("assets/houjin_toke.csv", index_col=0)
jp_wages = pd.read_csv("assets/jp_wages.csv", index_col=0)

# 日本経済に関して
economic_side = html.Div(
    [
        dcc.Tabs(
            id="Tabs",
            children=[
                dcc.Tab(
                    label="japanese-economy-title",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [html.H1("日本経済を可視化する", style=title_font)],
                                    style=title_style,
                                ),
                                dcc.Markdown(
                                    """
                - Dashを使って日本経済を可視化
                    - 日本の道路は安全になった。（今日は話しません！）
                    - 気になる！お隣さんのお財布事情！
                
                - オープンデータを利用
                    - 特定のデータが、一切の著作権、特許など制御メカニズムの制限なしで、全ての人が望むように利用・再掲載できるべきであるというアイデア（[via Wikipedia](https://ja.wikipedia.org/wiki/%E3%82%AA%E3%83%BC%E3%83%97%E3%83%B3%E3%83%87%E3%83%BC%E3%82%BF)）。
                    - 官民データ活用推進基本法（平成28年法律第103号）において、国及び地方公共団体はオープンデータに取り組むことが義務付けられた([政府CIOポータル](https://cio.go.jp/policy-opendata))。
                    - 日本の統計偽装の問題。

                """,
                                    style={"fontSize": 50, "margin": "5%"},
                                ),
                                html.Div(
                                    [
                                        html.H4(
                                            "たとえば犬の登録申請数なんてのもある",
                                            style={"textAlign": "center"},
                                        ),
                                        dcc.Graph(
                                            figure={
                                                "data": [
                                                    go.Bar(
                                                        x=dogFrame.index,
                                                        y=dogFrame["登録申請数"],
                                                    )
                                                ]
                                            }
                                        ),
                                    ],
                                    style={"width": "70%", "margin": "auto"},
                                ),
                                dcc.Link(
                                    "データソース: e-Stat 衛生行政報告例",
                                    href="https://www.e-stat.go.jp/stat-search/files?page=1&toukei=00450027&tstat=000001031469",
                                    style={"marginLeft": "75%"},
                                ),
                                back_to_index,
                            ]
                        )
                    ],
                ),
                # Japanese Road
                dcc.Tab(
                    label="about_road",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [html.H1("日本の道路は安全になった。", style=title_font)],
                                    style=title_style,
                                ),
                                dcc.Markdown(
                                    """
                - 日本の自動車保有台数は増加しています。
                - 最近はお年寄りの車の事故など、自動車がらみの報道が増えています。
                - 日本の道路は危険になっているのでしょうか？？

                """,
                                    style={"fontSize": 50, "margin": "5%"},
                                ),
                            ]
                        ),
                        html.Div(
                            id="show_accident_graph",
                            children=[
                                html.H3(
                                    "日本の自動車事故に関する数値", style={"textAlign": "center"}
                                ),
                                dcc.Graph(
                                    figure={
                                        "data": [
                                            go.Scatter(
                                                y=df_car_accident_one[
                                                    df_car_accident_one["variable"] == i
                                                ]["value"],
                                                x=df_car_accident_one[
                                                    df_car_accident_one["variable"] == i
                                                ]["year"],
                                                mode="lines",
                                                name=i,
                                            )
                                            for i in df_car_accident_one[
                                                "variable"
                                            ].unique()
                                        ],
                                        "layout": go.Layout(
                                            title={"text": "日本の事故件数、負傷者数"}
                                        ),
                                    }
                                ),
                                dcc.Graph(
                                    figure={
                                        "data": [
                                            go.Bar(
                                                x=df_car_accident_two["year"],
                                                y=df_car_accident_two["value"],
                                            )
                                        ],
                                        "layout": go.Layout(
                                            title={"text": "日本の交通事故死者数"}
                                        ),
                                    }
                                ),
                                dcc.Link(
                                    "データソース: estat 道路の交通に関する統計",
                                    href="https://www.e-stat.go.jp/stat-search/database?page=1&layout=datalist&stat_infid=000031400112",
                                    style={"marginLeft": "60%"},
                                ),
                                # 世界の自動車事故　ここは選択したらその国が見られるものにする
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "世界の10万人当たりの交通事故死亡者数",
                                                    style={"textAlign": "center"},
                                                ),
                                                dcc.Checklist(
                                                    id="world_car_checklist",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in world_car_accidents[
                                                            "Country"
                                                        ].unique()
                                                    ],
                                                    value=["Japan"],
                                                ),
                                            ],
                                            style={
                                                "width": "50%",
                                                "margin": "3% auto 3%",
                                            },
                                        ),
                                        dcc.Graph(id="world_car_accident_graph"),
                                        dcc.Link(
                                            "データソース: OECD Road fatilities by age - extract from the IRTAD database.",
                                            href="https://stats.oecd.org/Index.aspx?DataSetCode=IRTAD_CASUAL_BY_AGE",
                                            style={"marginLeft": "30%"},
                                        ),
                                        html.H3(
                                            "日本だけでなく世界中で道路は安全に！！！",
                                            style={
                                                "textAlign": "center",
                                                "backgroundColor": "#fbffb9",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/happy_schoolgirl.PNG",
                                                    style={"display": "inline-block"},
                                                ),
                                                html.Img(
                                                    src="assets/happy_schoolboy.PNG",
                                                    style={"dispaly": "inline-block"},
                                                ),
                                                html.Img(
                                                    src="assets/happy_schoolgirl.PNG",
                                                    style={"display": "inline-block"},
                                                ),
                                            ],
                                            style={"width": "100%", "margin": "auto"},
                                        ),
                                        html.Div(
                                            [
                                                html.H3("これを見るまでは・・・"),
                                                dcc.Graph(
                                                    id="elder-accidents",
                                                    figure={
                                                        "data": [
                                                            go.Box(
                                                                x=elderly_acc_ratio[
                                                                    "Year"
                                                                ],
                                                                y=elderly_acc_ratio[
                                                                    "Value"
                                                                ],
                                                            )
                                                        ],
                                                        "layout": go.Layout(
                                                            height=600,
                                                            title="世界の65歳以上の交通事故死の全体に占める割合",
                                                            clickmode="event+select",
                                                        ),
                                                    },
                                                    clickData={"points": [{"x": 1990}]},
                                                ),
                                                dcc.Graph(
                                                    id="elderly-bar",
                                                    selectedData={
                                                        "points": [{"x": "Denmark"}]
                                                    },
                                                    style={
                                                        "width": "50%",
                                                        "display": "inline-block",
                                                    },
                                                ),
                                                dcc.Graph(
                                                    id="elderly-scatter",
                                                    style={
                                                        "width": "50%",
                                                        "display": "inline-block",
                                                    },
                                                ),
                                                dcc.Link(
                                                    "データソース: OECD Road fatilities by age - extract from the IRTAD database.",
                                                    href="https://stats.oecd.org/Index.aspx?DataSetCode=IRTAD_CASUAL_BY_AGE",
                                                    style={
                                                        "marginLeft": "30%",
                                                        "marginTop": "3%",
                                                    },
                                                ),
                                                html.H3(
                                                    "日本の高齢者の交通事故死亡率、世界に比べて高過ぎ・・・",
                                                    style={
                                                        "textAlign": "center",
                                                        "backgroundColor": "#fbffb9",
                                                        "margin": "3%",
                                                    },
                                                ),
                                            ],
                                            style={"marginTop": "10%"},
                                        ),
                                        html.Div(
                                            [
                                                dcc.Markdown(
                                                    """
                    - この問題の解決が、自動車事故による死者をゼロにすることにつながるのかもしれない。
                    - しかし、以下に示すように、巷に言われるように老人の事故が多いとかそういうのはない。


                    """,
                                                    style=mkd_style,
                                                )
                                            ],
                                            style=mkd_outside_style,
                                        ),
                                        html.Div(
                                            [
                                                dcc.RadioItems(
                                                    id="acc_age_data_radio",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in acc_age_data[
                                                            "Title"
                                                        ].unique()
                                                    ],
                                                    value="事故件数【件】",
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "textAlign": "center",
                                                        "fontSize": 30,
                                                    },
                                                ),
                                                dcc.Graph(id="acc_age_data_graph"),
                                                dcc.Link(
                                                    "データソース: estat 道路の交通に関する統計",
                                                    href="https://www.e-stat.go.jp/stat-search/database?page=1&layout=datalist&stat_infid=000031400112",
                                                    style={"marginLeft": "60%"},
                                                ),
                                            ],
                                            style={"margin": "5%"},
                                        ),
                                    ]
                                ),
                                back_to_index,
                            ],
                            style={"width": "80%", "margin": "auto"},
                        ),
                    ],
                ),
                # japanese wallet
                dcc.Tab(
                    label="neighbor's wallet",
                    style=tab_style,
                    selected_style=tab_selected_style,
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [html.H1("気になる！お隣さんのお財布事情！", style=title_font)],
                                    style=title_style,
                                ),
                                dcc.Markdown(
                                    """
                                - 案外、人の財布の状況って知らない
                                - 自分の財布の状況もどうなっているか知らない人もいる
                                - そこで日本人のお財布状況はどうなっているのか調査
                                - ついでに企業のデータも調査
                                - お給料のデータも調査
                                
                                ### 扱うデータ
                                - [全国消費実態調査](https://www.e-stat.go.jp/stat-search/database?page=1&layout=normal&toukei=00200564&survey=%E6%B6%88%E8%B2%BB%E5%AE%9F%E6%85%8B%E8%AA%BF%E6%9F%BB&result_page=1)
                                - [法人企業統計](https://www.e-stat.go.jp/dbview?sid=0003060791)
                                - [毎月勤労統計調査　全国調査 就業形態別現金給与総額　指数及び増減率](https://www.e-stat.go.jp/dbview?sid=0003138239)
                                - [OECD (2019), Average annual wages](https://stats.oecd.org/Index.aspx?DataSetCode=AV_AN_WAGE)
                                """,
                                    style={"fontSize": 50, "margin": "5%"},
                                ),
                                html.Div(
                                    [
                                        # 消費実態調査
                                        html.Div(
                                            [
                                                html.H3(
                                                    "世帯収入を確認する　全国消費実態調査（1984‐2014）",
                                                    style={
                                                        "textAlign": "center",
                                                        "backgroundColor": "#fbffb9",
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Checklist(
                                                            id="jittai_check_list",
                                                            options=[
                                                                {"label": i, "value": i}
                                                                for i in shouhi_jittai[
                                                                    "variable"
                                                                ].unique()
                                                            ],
                                                            value=["平均"],
                                                        )
                                                    ],
                                                    style={
                                                        "width": "40%",
                                                        "display": "inline-block",
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Dropdown(
                                                            id="jittai_dropdown",
                                                            options=[
                                                                {"label": i, "value": i}
                                                                for i in shouhi_jittai[
                                                                    "項目"
                                                                ].unique()
                                                            ],
                                                            value="年間収入（千円）",
                                                        )
                                                    ],
                                                    style={
                                                        "width": "40%",
                                                        "display": "inline-block",
                                                        "marginLeft": "5%",
                                                    },
                                                ),
                                                dcc.Graph(id="jittai_graph"),

                                                #         # 国際的な生産性
                                                #         html.H3(
                                                #             "国際的な生産性の推移（2010 : 100）",
                                                #             style={
                                                #                 "textAlign": "center",
                                                #                 "backgroundColor": "#fbffb9",
                                                #             },
                                                #         ),
                                                #         html.Div(
                                                #             [
                                                #                 dcc.Checklist(
                                                #                     id="oecd_productivity_checklist",
                                                #                     options=[
                                                #                         {
                                                #                             "label": i,
                                                #                             "value": i,
                                                #                         }
                                                #                         for i in oecd_productivity[
                                                #                             "Country"
                                                #                         ].unique()
                                                #                     ],
                                                #                     value=["Japan"],
                                                #                 )
                                                #             ],
                                                #             style={
                                                #                 "width": "50%",
                                                #                 "margin": "auto",
                                                #             },
                                                #         ),
                                                #         dcc.Graph(
                                                #             id="oecd_productivity_graph"
                                                #         ),
                                                #     ],
                                                #     style={"margin": "5%"},
                                                # ),
                                                # 法人企業統計
                                                html.Div(
                                                    [
                                                        html.H3(
                                                            "法人企業統計を見る（全産業　除く金融保険　1960～2018年）",
                                                            style={
                                                                "textAlign": "center",
                                                                "backgroundColor": "#fbffb9",
                                                            },
                                                        ),
                                                        html.Div(
                                                            [
                                                                dcc.Dropdown(
                                                                    id="houjin_tokei_dropdown1",
                                                                    options=[
                                                                        {
                                                                            "label": i,
                                                                            "value": i,
                                                                        }
                                                                        for i in houjin_tokei.columns[
                                                                            2:
                                                                        ]
                                                                    ],
                                                                    value="年  期",
                                                                )
                                                            ],
                                                            style={
                                                                "width": "40%",
                                                                "display": "inline-block",
                                                            },
                                                        ),
                                                        html.Div(
                                                            [
                                                                dcc.Dropdown(
                                                                    id="houjin_tokei_dropdown2",
                                                                    options=[
                                                                        {
                                                                            "label": i,
                                                                            "value": i,
                                                                        }
                                                                        for i in houjin_tokei.columns[
                                                                            2:
                                                                        ]
                                                                    ],
                                                                    value="年  期",
                                                                )
                                                            ],
                                                            style={
                                                                "width": "40%",
                                                                "display": "inline-block",
                                                                "marginLeft": "5%",
                                                            },
                                                        ),
                                                        dcc.Graph(
                                                            id="houjin_tokei_graph"
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    [
                                                        html.H3(
                                                            "毎月勤労統計　日本は給料上がってた時ある？",
                                                            style={
                                                                "textAlign": "center",
                                                                "backgroundColor": "#fbffb9",
                                                            },
                                                        ),
                                                        dcc.Graph(
                                                            figure={
                                                                "data": [
                                                                    go.Scatter(
                                                                        x=jp_wages[
                                                                            "調査年"
                                                                        ],
                                                                        y=jp_wages[
                                                                            "年平均"
                                                                        ],
                                                                        mode="lines",
                                                                    )
                                                                ],
                                                                "layout": go.Layout(
                                                                    height=600
                                                                ),
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div([
                                                     html.Div(
                                                    [
                                                        # 国際的な給与水準
                                                        html.H3(
                                                            "国際的な給与の推移（米ドル建て　1990年～）",
                                                            style={
                                                                "textAlign": "center",
                                                                "backgroundColor": "#fbffb9",
                                                            },
                                                        ),
                                                        html.Div(
                                                            [
                                                                dcc.Checklist(
                                                                    id="oecd_wage_checklist",
                                                                    options=[
                                                                        {
                                                                            "label": i,
                                                                            "value": i,
                                                                        }
                                                                        for i in oecd_annual_wage[
                                                                            "Country"
                                                                        ].unique()
                                                                    ],
                                                                    value=["Japan"],
                                                                )
                                                            ],
                                                            style={
                                                                "width": "50%",
                                                                "margin": "auto",
                                                            },
                                                        ),
                                                        dcc.Graph(id="oecd_wage_graph"),
                                                        html.P("データソース: OECD (2019), Average annual wages, OECD Employment and Labour Market Statistics (database), https://doi.org/10.1787/data-00571-en (アクセスした日時 09 September 2019)")
                                                        ]),

                                                ]),
                                            ],
                                            style={"width": "90%", "margin": "auto"},
                                        )
                                    ]
                                ),
                                back_to_index,
                                html.Div(
                                    [dcc.Link("go to epilogue", href="/epilogue")],
                                    style={
                                        "fontSize": 30,
                                        "textAlign": "right",
                                        "marginRight": "5%",
                                    },
                                ),
                            ]
                        )
                    ],
                ),
            ],
            style=tabs_styles,
        )
    ]
)

# world_car_accidnet_callback
@app.callback(
    Output("world_car_accident_graph", "figure"),
    [Input("world_car_checklist", "value")],
)
def world_car_graph(country_name):
    return {
        "data": [
            go.Scatter(
                x=world_car_accidents[world_car_accidents["Country"] == i]["Year"],
                y=world_car_accidents[world_car_accidents["Country"] == i]["Value"],
                name=i,
                mode="lines",
            )
            for i in country_name
        ]
    }


# over65-acc-callback
@app.callback(
    [Output("elderly-bar", "figure"), Output("elderly-scatter", "figure")],
    [Input("elder-accidents", "clickData"), Input("elderly-bar", "selectedData")],
)
def over65_callback(clickData, selectedData):
    clickyear = clickData["points"][0]["x"]
    dff = elderly_acc_ratio[elderly_acc_ratio["Year"] == clickyear]
    dff = dff.sort_values("Value")
    cnt_list = []
    for i in range(len(selectedData["points"])):
        cnt_list.append(selectedData["points"][i]["x"])
    return (
        {
            "data": [go.Bar(x=dff["Country"], y=dff["Value"])],
            "layout": go.Layout(
                clickmode="event+select",
                title={"text": "{}年の高齢者交通事故死亡割合".format(clickyear)},
            ),
        },
        {
            "data": [
                go.Scatter(
                    x=elderly_pop_ratio[elderly_pop_ratio["Country"] == i]["Value"],
                    y=elderly_acc_ratio[elderly_acc_ratio["Country"] == i]["Value"],
                    name=i,
                    mode="markers",
                )
                for i in cnt_list
            ],
            "layout": go.Layout(
                title="人口に占める高齢者割合と事故死亡率割合",
                hovermode="closest",
                height=600,
                xaxis={"title": "pop_ratio", "range": [0.05, 0.3]},
                yaxis={"title": "road_kill_ratio", "range": [0, 0.6]},
            ),
        },
    )


# accident_age_data
@app.callback(
    Output("acc_age_data_graph", "figure"), [Input("acc_age_data_radio", "value")]
)
def acc_age_data_callback(value):
    dff = acc_age_data[acc_age_data["Title"] == value]
    return px.bar(dff, x="Year", y="Value", color="Age", title=value)


# shouhi_jittai_callback
@app.callback(
    Output("jittai_graph", "figure"),
    [Input("jittai_check_list", "value"), Input("jittai_dropdown", "value")],
)
def update_shouhi_jittai_graph(jittai_checklist_value, jittai_dropdown_value):
    dff = shouhi_jittai[shouhi_jittai["項目"] == jittai_dropdown_value]
    return {
        "data": [
            go.Scatter(
                x=dff[dff["variable"] == i]["年次"],
                y=dff[dff["variable"] == i]["value"],
                name=i,
            )
            for i in jittai_checklist_value
        ],
        "layout": go.Layout(height=800),
    }


# oecd_wage_callback
@app.callback(
    Output("oecd_wage_graph", "figure"), [Input("oecd_wage_checklist", "value")]
)
def update_oecd_wagegraph(value1):
    return {
        "data": [
            go.Scatter(
                x=oecd_annual_wage[oecd_annual_wage["Country"] == i]["Time"],
                y=oecd_annual_wage[oecd_annual_wage["Country"] == i]["Value"],
                name=i,
            )
            for i in value1
        ],
        "layout": go.Layout(height=600),
    }


# oecd_productivity_callback
@app.callback(
    Output("oecd_productivity_graph", "figure"),
    [Input("oecd_productivity_checklist", "value")],
)
def update_oecd_productivity(value2):
    return {
        "data": [
            go.Scatter(
                x=oecd_productivity[oecd_productivity["Country"] == i]["Time"],
                y=oecd_productivity[oecd_productivity["Country"] == i]["Value"],
                name=i,
                mode="lines",
            )
            for i in value2
        ]
    }


# houjin_tokei_callback
@app.callback(
    Output("houjin_tokei_graph", "figure"),
    [
        Input("houjin_tokei_dropdown1", "value"),
        Input("houjin_tokei_dropdown2", "value"),
    ],
)
def houjin_tokei_graph(value1, value2):
    return {
        "data": [
            go.Scatter(x=houjin_tokei[value1], y=houjin_tokei[value2], mode="markers")
        ],
        "layout": go.Layout(height=800),
    }


# picture
def parse_contents(contents, filename, date):
    return html.Div(
        [
            html.H1(filename[:-4], style={"textAlign": "center"}),
            html.Img(src=contents, style={"width": "100%", "margin": "auto"}),
        ]
    )


@app.callback(
    Output("output-image-upload", "children"),
    [Input("upload-image", "contents")],
    [State("upload-image", "filename"), State("upload-image", "last_modified")],
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d)
            for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
        ]
        return children


# 結論ページ

epilogue = html.Div(
    [
        html.Div([html.Div([html.H1("エピローグ", style=title_font)], style=title_style)]),
        html.Div(
            [
                dcc.Markdown(
                    """
                    [SUBARU総監督吼える　「9割の人は運転がヘタ」](https://business.nikkei.com/atcl/seminar/19/00105/00048/?P=4&mds)     

                    質問者: 「運転のうまいヘタ」って何でしょう。辰巳さんはどこを見てそうおっしゃっているのですか。判断基準を教えてください。     

                    辰巳さん: それは人をいたわるかどうかですよ。ヘタな人は、歩行者とか自転車とか、弱者をいたわらない。テクニックじゃないんです。クルマで道路を走る上で一番大事なところは、他者をいたわる気持ちです。今、日本でいろいろな問題が起きていますが、そういう教育ができていないからですよ。そもそも「運転教育」って今まで誰もしたことがないでしょう。
                    
                    
                    """,
                    style=mkd_style,
                ),
                html.Div(html.H3("私はこの話はデータ分析にも当てはまることだと思います。", style={"textAlign":"center"})),
            ],
            style=mkd_outside_style,
        ),
        html.Div([html.H1("Special Thanks: drillerさん",  style={"fontSize": 60, "fontWeight": "bold", "textAlign": "center", "padding": 10})], style=title_style),
        html.Div(
            [
                dcc.Upload(
                    id="upload-image",
                    children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                    style={
                        "width": "80%",
                        "height": "100px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "3% auto 3%",
                    },
                    multiple=True,
                )
            ]
        ),
        html.Div(id="output-image-upload"),
        back_to_index,
    ]
)

# page_routing


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def diplay_page(pathname):
    if pathname == "/intro":
        return intro
    elif pathname == "/about-dash":
        return about_dash
    elif pathname == "/about-japanese-economy":
        return economic_side
    elif pathname == "/epilogue":
        return epilogue
    else:
        return index_page

if __name__ == "__main__":
    app.run_server(debug=True)
