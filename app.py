"""Dashboard interactif Valorant — Streamlit + Plotly
Lancement : streamlit run app.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

st.set_page_config(page_title="Valorant Dashboard", page_icon="🎯", layout="wide")

# ---------- Thème visuel Valorant ----------
RED, DARK, CARD, WHITE, TEAL = "#FF4655", "#0F1923", "#1F2933", "#ECE8E1", "#17E5C4"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, label {{ font-family: 'Rajdhani', sans-serif !important; }}
.stApp {{ background: radial-gradient(circle at 85% 0%, #3a1d27 0%, {DARK} 45%) fixed; }}
[data-testid="stSidebar"] {{ background: #0B131B; border-right: 2px solid {RED}; }}
h1, h2, h3 {{ font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px; text-transform: uppercase; }}
.valo-title, .valo-title * {{ font-family: 'Bebas Neue'; font-size: 4.2rem !important; line-height: .9; color: {WHITE}; margin: 0; letter-spacing: 3px; }}
.valo-title span {{ color: {RED}; }}
.valo-sub {{ font-family: 'Rajdhani'; color: {RED}; letter-spacing: 6px; font-weight: 700; font-size: 1.05rem; letter-spacing: 5px; margin-bottom: 1.2rem;
             border-left: 4px solid {RED}; padding-left: 10px; }}
[data-testid="stMetric"] {{ background: {CARD}; padding: 14px 18px; border-left: 4px solid {RED};
   clip-path: polygon(0 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%); }}
[data-testid="stMetricLabel"] p {{ text-transform: uppercase; letter-spacing: 3px; font-size: .8rem !important; color: #8B978F; }}
[data-testid="stMetricValue"] {{ font-family: 'Bebas Neue' !important; font-size: 2.8rem !important; color: {WHITE}; }}
[data-testid="stPlotlyChart"] {{ background: {CARD}; padding: 6px; border-top: 3px solid {RED};
   clip-path: polygon(0 0, calc(100% - 22px) 0, 100% 22px, 100% 100%, 0 100%); }}
[data-testid="stSidebar"] h1 {{ color: {RED}; }}
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
</style>""", unsafe_allow_html=True)

pio.templates["valo"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Rajdhani, sans-serif", color=WHITE, size=14),
    title=dict(font=dict(family="Bebas Neue, sans-serif", size=24, color=WHITE)),
    xaxis=dict(gridcolor="#2E3A45", zerolinecolor="#2E3A45"),
    yaxis=dict(gridcolor="#2E3A45", zerolinecolor="#2E3A45"),
    margin=dict(l=10, r=20, t=60, b=40), height=460,
    legend=dict(orientation="h", y=-0.18, x=0),
    hoverlabel=dict(bgcolor=DARK, bordercolor=RED, font_family="Rajdhani")))
px.defaults.template = "plotly_dark+valo"

AGENTS = {
    "Duelliste": ["Jett", "Reyna", "Raze", "Phoenix", "Neon", "Yoru", "Iso"],
    "Initiateur": ["Sova", "Skye", "Fade", "Breach", "KAY/O", "Gekko"],
    "Contrôleur": ["Omen", "Brimstone", "Viper", "Astra", "Harbor", "Clove"],
    "Sentinelle": ["Killjoy", "Cypher", "Sage", "Chamber", "Deadlock"],
}
MAPS = ["Ascent", "Bind", "Haven", "Split", "Lotus", "Sunset", "Icebox", "Pearl"]
RANKS = ["Fer", "Bronze", "Argent", "Or", "Platine", "Diamant", "Ascendant", "Immortel", "Radiant"]


@st.cache_data
def load_data(n=6000, seed=42):
    """Jeu de données simulé (reproductible) : une ligne = un match d'un joueur."""
    rng = np.random.default_rng(seed)
    role_of = {a: r for r, lst in AGENTS.items() for a in lst}
    agents = list(role_of)
    pop = rng.dirichlet(np.ones(len(agents)) * 1.5)          # popularité des agents
    df = pd.DataFrame({
        "date": pd.to_datetime("2026-01-01") + pd.to_timedelta(rng.integers(0, 270, n), unit="D"),
        "agent": rng.choice(agents, n, p=pop),
        "map": rng.choice(MAPS, n),
        "rang": rng.choice(RANKS, n, p=[.06, .12, .17, .19, .17, .13, .09, .05, .02]),
    })
    df["role"] = df["agent"].map(role_of)
    bonus = {"Duelliste": 25, "Initiateur": 0, "Contrôleur": -10, "Sentinelle": -5}
    lvl = df["rang"].map({r: i for i, r in enumerate(RANKS)})
    df["acs"] = (170 + df["role"].map(bonus) + lvl * 8 + rng.normal(0, 45, n)).clip(60, 450).round()
    df["kills"] = (df["acs"] / 13 + rng.normal(0, 3, n)).clip(0).round().astype(int)
    df["deaths"] = rng.normal(15, 3, n).clip(3).round().astype(int)
    df["kd"] = (df["kills"] / df["deaths"]).round(2)
    df["hs_pct"] = (15 + lvl * 1.8 + rng.normal(0, 5, n)).clip(3, 60).round(1)
    p_win = 1 / (1 + np.exp(-(df["kd"] - 1) * 2.2))
    df["victoire"] = rng.random(n) < p_win
    return df


df = load_data()

# ---------- Barre latérale : filtres ----------
st.sidebar.title("// FILTRES")
roles = st.sidebar.multiselect("Rôle", list(AGENTS), default=list(AGENTS))
maps = st.sidebar.multiselect("Map", MAPS, default=MAPS)
rangs = st.sidebar.select_slider("Rang", RANKS, value=(RANKS[0], RANKS[-1]))
i0, i1 = RANKS.index(rangs[0]), RANKS.index(rangs[1])
st.sidebar.caption("Données simulées à but pédagogique (inspirées de Valorant).")

d = df[df["role"].isin(roles) & df["map"].isin(maps) & df["rang"].isin(RANKS[i0:i1 + 1])]
if d.empty:
    st.warning("Aucune donnée avec ces filtres.")
    st.stop()

# ---------- En-tête + KPI ----------
st.markdown('<div class="valo-title">VALORANT <span>//</span> AGENTS</div>'
            '<div class="valo-sub">TABLEAU DE BORD TACTIQUE — PERFORMANCES 2026</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Matchs analysés", f"{len(d):,}".replace(",", " "))
c2.metric("Taux de victoire", f"{d['victoire'].mean():.1%}")
c3.metric("ACS moyen", f"{d['acs'].mean():.0f}")
c4.metric("K/D moyen", f"{d['kd'].mean():.2f}")

COLORS = {"Duelliste": RED, "Initiateur": "#F4C95D", "Contrôleur": "#9D7BFF", "Sentinelle": TEAL}

# ---------- Ligne 1 : comparaison (barres) + composition (donut) ----------
a, b = st.columns([2, 1])
agg = (d.groupby(["agent", "role"])
         .agg(matchs=("victoire", "size"), winrate=("victoire", "mean"), acs=("acs", "mean"))
         .reset_index())
top = agg.sort_values("matchs", ascending=True).tail(12)
fig = px.bar(top, x="matchs", y="agent", color="role", orientation="h",
             color_discrete_map=COLORS, title="Top 12 — agents les plus joués")
fig.update_layout(yaxis_title=None, xaxis_title="Nombre de matchs", legend_title=None,
                  yaxis={"categoryorder": "total ascending"})
a.plotly_chart(fig, use_container_width=True, theme=None)

fig = px.pie(d, names="role", hole=.55, color="role", color_discrete_map=COLORS,
             title="Répartition des matchs par rôle")
fig.update_traces(textinfo="label+percent", marker_line=dict(color=DARK, width=3))
fig.update_layout(showlegend=False)
b.plotly_chart(fig, use_container_width=True, theme=None)

# ---------- Ligne 2 : évolution (ligne) + heatmap ----------
a, b = st.columns(2)
ts = (d.set_index("date").groupby("role").resample("MS")["victoire"].mean()
        .reset_index())
fig = px.line(ts, x="date", y="victoire", color="role", color_discrete_map=COLORS,
              title="Évolution mensuelle du taux de victoire", markers=True)
fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Taux de victoire", xaxis_title=None, legend_title=None)
a.plotly_chart(fig, use_container_width=True, theme=None)

hm = d.pivot_table(index="role", columns="map", values="victoire", aggfunc="mean")
fig = px.imshow(hm, text_auto=".0%", color_continuous_scale=[[0, RED], [.5, CARD], [1, TEAL]], zmin=.4, zmax=.6,
                title="Taux de victoire par rôle et par map", aspect="auto")
fig.update_layout(xaxis_title=None, yaxis_title=None, coloraxis_showscale=False)
b.plotly_chart(fig, use_container_width=True, theme=None)

# ---------- Ligne 3 : distribution (boxplot) + relation (nuage) ----------
a, b = st.columns(2)
fig = px.box(d, x="rang", y="hs_pct", category_orders={"rang": RANKS[i0:i1 + 1]},
             color_discrete_sequence=[RED], title="Distribution du % de headshots par rang")
fig.update_layout(xaxis_title=None, yaxis_title="Headshots (%)")
a.plotly_chart(fig, use_container_width=True, theme=None)

fig = px.scatter(agg, x="acs", y="winrate", size="matchs", color="role", hover_name="agent",
                 color_discrete_map=COLORS, title="ACS moyen vs taux de victoire (taille = popularité)")
fig.update_layout(yaxis_tickformat=".0%", xaxis_title="ACS moyen", yaxis_title="Taux de victoire", legend_title=None)
b.plotly_chart(fig, use_container_width=True, theme=None)

# ---------- Tableau détaillé ----------
with st.expander("📋 Tableau détaillé par agent"):
    st.dataframe(agg.sort_values("winrate", ascending=False)
                    .style.format({"winrate": "{:.1%}", "acs": "{:.0f}"}),
                 use_container_width=True, hide_index=True)
