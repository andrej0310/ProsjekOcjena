import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
from io import BytesIO

html.Img(src='/content/logo.svg', style={'height': '80px', 'margin-right': '20px'})


# Učitavanje podataka
#file_path = "/content/2023_2024_SVE.xlsx"


#SQL
import pymssql

# 🔹 Povezivanje sa SQL Serverom
conn = pymssql.connect(
    server="infoeduka.database.windows.net",
    user="domagojRuzak",
    password="Lozink@1234",
    database="infoeduka_view"
)

# 🔹 Izvršavanje SQL upita
query = "SELECT * FROM dbo.analytics_final_studentipredmeti WHERE akademska_godina = '2023/2024'"
cursor = conn.cursor()

# 🔹 Dohvaćanje podataka
cursor.execute(query)
rows = cursor.fetchall()

# 🔹 Dohvaćanje naziva stupaca
columns = [col[0] for col in cursor.description]

# 🔹 Kreiranje Pandas DataFrame-a
df = pd.DataFrame(rows, columns=columns)

# 🔹 Zatvaranje konekcije
conn.close()


#df = pd.read_excel(file_path, sheet_name="Sheet1")

# Grupisanje podataka
df_total = df.groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_total.rename(columns={'ocjena': 'broj_studenata'}, inplace=True)

df_passed = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_passed.rename(columns={'ocjena': 'broj_studenata_prosli'}, inplace=True)

df_avg = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].mean().reset_index()
df_avg.rename(columns={'ocjena': 'prosjek_ocjena'}, inplace=True)

df_ponavljaci_total = df[df["priznat_ponavlja"] == "Ponavlja"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_ponavljaci_total.rename(columns={'ocjena': 'broj_ponavljaca'}, inplace=True)

df_ponavljaci_passed = df[(df["ocjena"] > 1) & (df["priznat_ponavlja"] == "Ponavlja")].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_ponavljaci_passed.rename(columns={'ocjena': 'broj_ponavljaca_prosli'}, inplace=True)


df_priznati_total = df[df["priznat_ponavlja"] == "Priznat"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_priznati_total.rename(columns={'ocjena': 'broj_priznatih'}, inplace=True)

# Spajanje podataka
df_grouped = df_total.merge(df_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_avg, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_ponavljaci_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_ponavljaci_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_priznati_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
#df_grouped = df_grouped.merge(df[['kolegij_sifra', 'semestar']], on='kolegij_sifra', how='left')
df_semestar = df[['kolegij_sifra', 'semestar']].drop_duplicates()  # Makni duplikate
df_grouped = df_grouped.merge(df_semestar, on='kolegij_sifra', how='left')


df_grouped.fillna(0, inplace=True)

df_grouped["prolaznost"] = (df_grouped["broj_studenata_prosli"] / df_grouped["broj_studenata"]) * 100
df_grouped["prolaznost_ponavljaca"] = (df_grouped["broj_ponavljaca_prosli"] / df_grouped["broj_ponavljaca"]) * 100

df_grouped["kolegij_full"] = df_grouped["kolegij_naziv"] + " (" + df_grouped["kolegij_sifra"].astype(str) + ")"

app = dash.Dash(__name__)
server = app.server  # Ovo je potrebno za Render!

sorted_studiji = sorted(df_grouped['studij'].unique())

app.layout = html.Div([
    dcc.Dropdown(id='studij_dropdown', options=[{'label': studij, 'value': studij} for studij in sorted_studiji], value=sorted_studiji[0], style={'width': '40%'}, clearable=False),
    dcc.Dropdown(id='smjer_dropdown', options=[], style={'width': '40%'}, clearable=False),
    dcc.Dropdown(id='godina_dropdown', options=[{'label': 'Sve', 'value': 'Sve'}] + [{'label': str(godina), 'value': godina} for godina in df_grouped['skolska_godina'].unique()], value='Sve', style={'width': '40%'}, clearable=False),
    dcc.Graph(id='graf'),
    dcc.Graph(id='prolaznost_graf'),
    dcc.Graph(id='prolaznost_ponavljaci_graf')
])


image_id = "1IVYXW6Ye48OeHt6Xo89gJPp7NRySHwFH"  # Zameni svojim ID-om
image_url = f"https://lh3.googleusercontent.com/d/{image_id}"


app.layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[

    # Header s logotipom i naslovom
    html.Div([
        html.Img(src=image_url, style={'height': '80px', 'margin-right': '20px'}),
        html.H1("Analiza prolaznosti studenata", style={'color': '#fcfcfc', 'font-weight': 'bold'})
    ], style={'display': 'flex', 'align-items': 'center', 'background-color': '#151515', 'padding': '10px'}),

    # Dropdown filteri
    html.Div([
        html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='studij_dropdown', options=[{'label': studij, 'value': studij} for studij in sorted(df_grouped['studij'].unique())],
                     value=sorted(df_grouped['studij'].unique())[0],
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#be1e67', 'color': '#000000'}),

        html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='smjer_dropdown', options=[],
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#be1e67', 'color': '#000000'}),

        html.Label("Školska godina:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='godina_dropdown', options=[{'label': 'Sve', 'value': 'Sve'}] +
                     [{'label': str(godina), 'value': godina} for godina in df_grouped['skolska_godina'].unique()],
                     value='Sve',
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#be1e67', 'color': '#000000'})
    ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

    # Grafovi
    dcc.Graph(id='graf'),
    dcc.Graph(id='prolaznost_graf'),
    dcc.Graph(id='prolaznost_ponavljaci_graf')
])


@app.callback(
    Output('smjer_dropdown', 'options'),
    [Input('studij_dropdown', 'value')]
)
def set_smjer_options(selected_studij):
    smjerovi_for_studij = df_grouped[df_grouped['studij'] == selected_studij]['smjer'].unique()
    return [{'label': smjer, 'value': smjer} for smjer in smjerovi_for_studij]

@app.callback(
    [Output('graf', 'figure'),
     Output('prolaznost_graf', 'figure'),
     Output('prolaznost_ponavljaci_graf', 'figure'),
     Output('graf', 'style'),
     Output('prolaznost_graf', 'style'),
     Output('prolaznost_ponavljaci_graf', 'style')],
    [Input('studij_dropdown', 'value'),
     Input('smjer_dropdown', 'value'),
     Input('godina_dropdown', 'value')]
)
def update_graph(selected_studij, selected_smjer, selected_godina):
    filtered_df = df_grouped[
        (df_grouped['studij'] == selected_studij) &
        (df_grouped['smjer'] == selected_smjer if selected_smjer else True) &
        ((df_grouped['skolska_godina'] == selected_godina) if selected_godina != 'Sve' else True)
    ]

    num_kolegija = len(filtered_df)
    height = 300 + num_kolegija * 30

     # 🔹 Definiraj prilagođene boje za semestar
    semestar_colors = {"Zimski semestar": "#1f77b4", "Ljetni semestar": "#ff7f0e"}  # Plava za zimski, narančasta za ljetni


    fig1 = px.bar(filtered_df,
                  x="prosjek_ocjena",
                  y="kolegij_full",
                  orientation="h",
                  title="Prosječna ocjena po kolegiju",
                  text=filtered_df["prosjek_ocjena"].round(2),
                  hover_data={"broj_studenata": True, "broj_studenata_prosli":True, "broj_ponavljaca": True, "broj_priznatih": True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )
    fig2 = px.bar(filtered_df,
                  x="prolaznost",
                  y="kolegij_full",
                  orientation="h",
                  title="Prolaznost po kolegiju (%)",
                  text=filtered_df["prolaznost"].round(2),
                  hover_data={"broj_studenata": True, "broj_studenata_prosli":True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )
    fig3 = px.bar(filtered_df,
                  x="prolaznost_ponavljaca",
                  y="kolegij_full",
                  orientation="h",
                  title="Prolaznost ponavljača (%)",
                  text=filtered_df["prolaznost_ponavljaca"].round(2),
                  hover_data={"broj_ponavljaca": True, "broj_ponavljaca_prosli":True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )

    for fig in [fig1, fig2, fig3]:
        fig.update_traces(marker=dict(line=dict(width=2)), textposition='outside', textfont_size=12)
        fig.update_layout(yaxis_title="Naziv kolegija (Šifra)", 
                          height=height,
                          title={
                                "font": {
                                "family": "Arial",
                                "size": 30,
                                "color": "darkblue",
                                "weight": "bold"
                                },
                                "x": 0.5,
                                "xanchor": "center"
    })

    fig1.update_layout(xaxis_title="Prosječna ocjena")
    fig2.update_layout(xaxis_title="Prolaznost (%)")
    fig3.update_layout(xaxis_title="Prolaznost ponavljača (%)")

    return fig1, fig2, fig3, {'height': f'{height}px'}, {'height': f'{height}px'}, {'height': f'{height}px'}

if __name__ == '__main__':
    app.run_server(debug=True)
