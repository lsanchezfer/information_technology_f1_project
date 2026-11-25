import matplotlib.pyplot as plt
import psycopg2
import streamlit as st

import charts
import queries as Q
from data import run_query, what_if_disqualified

st.set_page_config(page_title="F1 Database Explorer", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
[data-testid="stSidebar"] {background: #15151E;}
[data-testid="stSidebar"] * {color: #F3F3F5 !important;}
[data-testid="stSidebar"] hr {border-color: #3A3A48;}
.hero {background: #15151E; color: #fff; border-radius: 14px;
       padding: 1.6rem 1.8rem; margin-bottom: 1.2rem; border-left: 8px solid #E10600;}
.hero h1 {color: #fff; margin: 0.2rem 0 0.4rem 0; font-size: 2.1rem;}
.hero p {color: #C9C9D1; margin: 0; font-size: 1rem;}
.kicker {color: #E10600; font-weight: 700; letter-spacing: .12em; font-size: .78rem;}
.qhead {display: flex; align-items: center; gap: .6rem; margin: .6rem 0 .1rem 0;}
.qid {background: #E10600; color: #fff; font-weight: 700; border-radius: 6px;
      padding: .15rem .55rem; font-size: .9rem;}
.qtitle {font-size: 1.35rem; font-weight: 700;}
.pill {display: inline-block; background: #F3F3F5; border: 1px solid #DCDCE2;
       border-radius: 999px; padding: .1rem .6rem; margin: 0 .3rem .3rem 0; font-size: .8rem;}
[data-testid="stMetric"] {background: #F3F3F5; border-radius: 12px; padding: .8rem 1rem;
                          border-left: 5px solid #E10600;}
[data-testid="stImage"] img, [data-testid="stPyplot"] img {border-radius: 10px;}
</style>
""", unsafe_allow_html=True)


def header(title, subtitle):
    st.markdown(f'<div class="hero"><div class="kicker">FORMULA 1, {FIRST}-{LAST}</div>'
                f'<h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner=False)
def cached(sql_text, params_items=()):
    return run_query(sql_text, dict(params_items))


def safe_query(sql_text, params=None):
    try:
        return cached(sql_text, tuple(sorted((params or {}).items())))
    except psycopg2.OperationalError:
        st.error("Cannot connect to PostgreSQL. Check that the server is running, "
                 "that the database 'f1' exists and that password.txt is correct.")
        st.stop()
    except psycopg2.Error as e:
        st.error(f"The database rejected the request: {e.pgerror or e}")
        return []


def show(qid, rows, **kwargs):
    q = Q.QUERY_BY_ID[qid]
    st.markdown(f'<div class="qhead"><span class="qid">{q["id"]}</span>'
                f'<span class="qtitle">{q["title"]}</span></div>', unsafe_allow_html=True)
    st.caption(q["question"])
    if not rows:
        st.info("No rows for the selected filters. Try a wider range.")
        return
    left, right = st.columns([3, 1.2], gap="large")
    with left:
        fig = charts.CHARTS[qid](rows, **kwargs)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with right:
        with st.container(border=True):
            st.markdown("**Why it matters**")
            st.write(q["why"])
            st.markdown(f"**Author:** {q['author']}")
            pills = "".join(f'<span class="pill">{f.strip()}</span>' for f in q["features"].split(","))
            st.markdown(pills, unsafe_allow_html=True)
            st.caption(f"{len(rows)} row(s) returned")
    with st.expander("Rows returned by PostgreSQL"):
        st.dataframe(rows, use_container_width=True, hide_index=True)
    with st.expander("SQL"):
        st.code(q["sql"].strip(), language="sql")


bounds = safe_query(Q.L_SEASON_BOUNDS)
FIRST, LAST = (bounds[0]["first"], bounds[0]["last"]) if bounds else (1950, 2024)
SEASONS = [r["year"] for r in safe_query(Q.L_SEASONS)]

st.sidebar.markdown("## F1 Explorer")
st.sidebar.caption(f"World Championship {FIRST}-{LAST}  \nPostgreSQL + psycopg2")
st.sidebar.divider()
PAGES = ["Overview", "Drivers", "Countries", "Races", "Seasons & teams", "What-if (transaction)"]
page = st.sidebar.radio("Section", PAGES, label_visibility="collapsed")

if page == "Overview":
    header("Formula 1 World Championship database",
           "Every chart in this app is one SQL query, and every filter is sent to "
           "PostgreSQL as a parameter. Pick a section on the left.")
    counts = safe_query(Q.L_TABLE_COUNTS)
    if counts:
        n = {r["table_name"]: r["n_rows"] for r in counts}
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Seasons", f"{LAST - FIRST + 1}")
        c2.metric("Races", f"{n.get('races', 0):,}")
        c3.metric("Drivers", f"{n.get('drivers', 0):,}")
        c4.metric("Lap times stored", f"{n.get('lap_times', 0):,}")
        st.markdown("#### Rows per table")
        st.dataframe(counts, use_container_width=True, hide_index=True)

elif page == "Drivers":
    header("Drivers", "Teammates, near misses, first wins and winning streaks.")
    tab1, tab2, tab3, tab4 = st.tabs(["Against his teammates (Q01)", "Points without a win (Q04)",
                                      "First win (Q05)", "Winning streaks (Q07)"])
    with tab1:
        text = st.text_input("Search a driver by name", value="Alonso", max_chars=40)
        found = safe_query(Q.L_DRIVER_SEARCH, dict(pattern=f"%{text.strip()}%"))
        if not found:
            st.warning("No driver matches that text.")
        else:
            labels = {f"{r['label']} ({r['first_season']}-{r['last_season']}, {r['starts']} starts)":
                      r["driver_id"] for r in found}
            a, b = st.columns([3, 1])
            choice = a.selectbox("Driver", list(labels))
            min_s = b.number_input("Minimum sessions together", 1, 100, 5)
            show("Q01", safe_query(Q.Q01, dict(driver_id=labels[choice], min_sessions=int(min_s))))
    with tab2:
        a, b = st.columns(2)
        min_races = a.number_input("Minimum races started", 1, 400, 20)
        top_n = b.number_input("Top N", 1, 50, 15, key="q04n")
        show("Q04", safe_query(Q.Q04, dict(min_races=int(min_races), top_n=int(top_n))))
    with tab3:
        a, b, c = st.columns([2, 1, 1])
        yr = a.slider("Season of the first win", FIRST, LAST, (FIRST, LAST), key="q05y")
        order = b.radio("Show", ["Youngest", "Oldest"], horizontal=True)
        top_n = c.number_input("Top N", 1, 50, 15, key="q05n")
        show("Q05", safe_query(Q.Q05, dict(year_from=yr[0], year_to=yr[1],
                                          oldest=(order == "Oldest"), top_n=int(top_n))))
    with tab4:
        a, b = st.columns(2)
        min_streak = a.number_input("Minimum consecutive wins", 2, 20, 4)
        top_n = b.number_input("Top N", 1, 50, 15, key="q07n")
        show("Q07", safe_query(Q.Q07, dict(min_streak=int(min_streak), top_n=int(top_n))))

elif page == "Countries":
    header("Countries", "Career points by nationality and the history of each country's Grands Prix.")
    tab1, tab2 = st.tabs(["Drivers of a nationality (Q02)", "Grands Prix of a country (Q03)"])
    with tab1:
        nats = [r["nationality"] for r in safe_query(Q.L_NATIONALITIES)]
        a, b, c = st.columns([2, 1, 1])
        nat = a.selectbox("Nationality", nats, index=nats.index("Spanish") if "Spanish" in nats else 0)
        min_pts = b.number_input("Minimum career points", 0, 5000, 1)
        top_n = c.slider("Drivers", 1, 8, 8)
        show("Q02", safe_query(Q.Q02, dict(nationality=nat, min_points=int(min_pts), top_n=top_n)))
    with tab2:
        countries = [r["country"] for r in safe_query(Q.L_CIRCUIT_COUNTRIES)]
        country = st.selectbox("Country", countries, index=countries.index("Spain") if "Spain" in countries else 0)
        show("Q03", safe_query(Q.Q03, dict(country=country)))

elif page == "Races":
    header("Races", "Comebacks from the back of the grid and what pit stops do to the result.")
    tab1, tab2 = st.tabs(["Comebacks (Q06)", "Pit stops and result (Q08)"])
    with tab1:
        a, b = st.columns([3, 1])
        yr = a.slider("Seasons", FIRST, LAST, (FIRST, LAST), key="q06y")
        top_n = b.number_input("Top N", 1, 50, 15, key="q06n")
        show("Q06", safe_query(Q.Q06, dict(year_from=yr[0], year_to=yr[1], top_n=int(top_n))))
    with tab2:
        a, b = st.columns([3, 1])
        yr = a.slider("Seasons (pit-stop data starts in 2011)", 2011, LAST, (2011, LAST), key="q08y")
        min_c = b.number_input("Minimum finishers per group", 1, 500, 20)
        show("Q08", safe_query(Q.Q08, dict(year_from=yr[0], year_to=yr[1], min_cases=int(min_c))))

elif page == "Seasons & teams":
    header("Seasons & teams", "How close each title was, which teams broke down, and how old the grid was.")
    tab1, tab2, tab3 = st.tabs(["Title margins (Q09)", "Team reliability (Q10)", "Age of the grid (Q11)"])
    with tab1:
        yr = st.slider("Seasons", FIRST, LAST, (FIRST, LAST), key="q09y")
        show("Q09", safe_query(Q.Q09, dict(year_from=yr[0], year_to=yr[1])))
    with tab2:
        a, b, c = st.columns([2, 1, 1])
        yr = a.slider("Seasons", FIRST, LAST, (2000, LAST), key="q10y")
        min_starts = b.number_input("Minimum starts", 1, 2000, 100)
        top_n = c.number_input("Top N", 1, 50, 15, key="q10n")
        show("Q10", safe_query(Q.Q10, dict(year_from=yr[0], year_to=yr[1],
                                          min_starts=int(min_starts), top_n=int(top_n))))
    with tab3:
        yr = st.slider("Seasons", FIRST, LAST, (FIRST, LAST), key="q11y")
        show("Q11", safe_query(Q.Q11, dict(year_from=yr[0], year_to=yr[1])))

elif page == "What-if (transaction)":
    q = Q.QUERY_BY_ID["Q12"]
    header("What-if", "Disqualify a driver inside a transaction, see the new standings, then roll back.")
    st.markdown(f'<div class="qhead"><span class="qid">Q12</span>'
                f'<span class="qtitle">{q["title"]}</span></div>', unsafe_allow_html=True)
    st.caption(f"{q['question']} (Author: {q['author']})")
    st.write("The application opens a transaction, runs an **UPDATE** that disqualifies the chosen "
             "driver from the chosen race, recomputes the season standings from the results in the "
             "same transaction, and then runs **ROLLBACK**. The stored data never changes.")
    a, b, c = st.columns([1, 2, 2])
    season = a.selectbox("Season", SEASONS, index=SEASONS.index(2021) if 2021 in SEASONS else 0, key="q12s")
    races = safe_query(Q.L_RACES_WITH_RESULTS, dict(season=season))
    if races:
        rl = {f"R{r['round']} - {r['name']}": r["race_id"] for r in races}
        race = b.selectbox("Race", list(rl), index=len(rl) - 1)
        drivers = safe_query(Q.L_DRIVERS_OF_RACE, dict(race_id=rl[race]))
        dl = {f"{r['position_order']}. {r['label']}": r["driver_id"] for r in drivers}
        drv = c.selectbox("Driver to disqualify", list(dl))
        if st.button("Run the what-if transaction", type="primary"):
            try:
                before, after, n = what_if_disqualified(rl[race], dl[drv], 10)
                st.success(f"UPDATE changed {n} row(s). ROLLBACK done, nothing was saved.")
                fig = charts.c12(before, after)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                l, r = st.columns(2)
                l.dataframe(before, hide_index=True, use_container_width=True)
                r.dataframe(after, hide_index=True, use_container_width=True)
            except psycopg2.Error as e:
                st.error(f"The transaction failed and was rolled back: {e.pgerror or e}")
        with st.expander("SQL"):
            st.code(q["sql"], language="sql")
        st.caption("Note: standings are recomputed as the plain sum of race and sprint points; "
                   "seasons with dropped-score rules (before 1991) can differ from the official table.")
