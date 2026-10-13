import streamlit as st

st.write ("We are connected")
import base64
import json
import math
from pathlib import Path

import streamlit as st

from hikingfilters import filter_hikes


BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

st.set_page_config(
    page_title="Swiss Hiking Matcher",
    page_icon="🥾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def image_data_uri(path: Path) -> str:
    """Encode a local image for a CSS background (no external hosting needed)."""
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


@st.cache_data

def load_hikes():
    with (BASE_DIR / "hikes_data.json").open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("hikes_data.json must contain a list of hikes.")
    return data


try:
    hikes = load_hikes()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
    st.error(f"Could not load hikes_data.json: {exc}")
    st.stop()

# The existing filter excludes incomplete hikes. Use the same criterion for UI limits.
required_fields = (
    "distance_km", "ascent_m", "descent_m", "duration_min",
    "technical_difficulty", "endurance_difficulty",
)
valid_hikes = [
    hike for hike in hikes
    if isinstance(hike, dict)
    and all(hike.get(field) is not None for field in required_fields)
]


def maximum_for(field: str, step: int, fallback: int) -> int:
    values = [h[field] for h in valid_hikes if isinstance(h[field], (int, float))]
    if not values:
        return fallback
    return max(step, int(math.ceil(max(values) / step) * step))


max_distance_limit = maximum_for("distance_km", 10, 100)
max_ascent_limit = maximum_for("ascent_m", 100, 4000)
max_descent_limit = maximum_for("descent_m", 100, 4000)
max_duration_hours = max(1, int(math.ceil(maximum_for("duration_min", 60, 720) / 60)))

hero_path = IMAGES_DIR / "Panoramabild_Header.jpeg"
hero_style = (
    f"background-image: linear-gradient(90deg, rgba(19,38,31,.75), rgba(19,38,31,.18)), "
    f"url('{image_data_uri(hero_path)}');"
    if hero_path.is_file()
    else "background:linear-gradient(120deg,#213d32,#71836d);"
)

st.markdown("""
<style>
.stApp { background: #f4f2ec; color: #24382d; }
.block-container { max-width: 1320px; padding-top: 1.2rem; padding-bottom: 4rem; }
#MainMenu, footer { visibility: hidden; }
.hero { min-height: 315px; background-position: center 47%; background-size: cover;
  border-radius: 20px; display: flex; align-items: center; justify-content: center;
  text-align: center; padding: 3rem 1rem; box-shadow: 0 12px 30px rgba(24,43,33,.12); }
.hero-content { border: 1px solid rgba(255,255,255,.38); background: rgba(20,38,31,.42);
  border-radius: 16px; padding: 1.4rem 2.6rem; backdrop-filter: blur(3px); }
.hero h1 { color: white; font-size: clamp(2rem, 4vw, 3.6rem); margin: 0; line-height: 1.1; }
.hero p { color: #f4f3ed; font-size: 1.1rem; margin: .7rem 0 0; }
.intro { padding: 1.5rem 0 .8rem; }
.intro h2 { font-size: 1.75rem; color: #273f33; margin: 0; }
.intro p { color: #607467; margin: .3rem 0 0; }
.card-heading { background:#e2e9df; border-radius: 14px; padding: .8rem 1rem;
  margin: .2rem 0 .8rem; min-height: 76px; }
.card-heading strong { display: block; color:#244434; font-size:1.08rem; }
.card-heading span { color:#62766a; font-size:.87rem; }
.card-photo { width:100%; height:145px; object-fit:cover; border-radius:14px; margin-bottom: .4rem; }
.future-note { background:#ece9dc; border:1px solid #dad6c5; border-radius:10px;
  padding:.75rem; color:#696c5d; margin-top:.55rem; font-size:.9rem; }
.result-header { color:#274234; margin:2rem 0 .7rem; }
.result-card { background:white; border:1px solid #e1e6dc; border-radius:14px;
  padding:1rem 1.2rem; margin-bottom:.8rem; box-shadow:0 3px 12px rgba(27,42,31,.04); }
.result-card h4 { margin:0 0 .45rem; color:#233c2e; }
.result-card p { margin:.12rem 0; color:#526556; }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
  background:#294e3a; border-color:#294e3a; border-radius:12px; font-weight:600; }
@media(max-width:700px) { .hero { min-height:240px; } .hero-content{padding:1rem;} }
</style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="hero" style="{hero_style}">'
    '<div class="hero-content"><h1>Swiss Hiking Matcher</h1>'
    '<p>Find your perfect hike.</p></div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="intro"><h2>Your next adventure starts here.</h2>'
    '<p>Set your preferences and discover hikes across Switzerland.</p></div>',
    unsafe_allow_html=True,
)

# Only the first card is connected to filtering. Other sections are clearly marked as previews.
with st.form("hiking_search"):
    hike_col, travel_col, weather_col = st.columns(3, gap="large")

    with hike_col:
        st.markdown('<div class="card-heading"><strong>🥾 Hike description</strong>'
                    '<span>Choose the kind of hike you enjoy</span></div>', unsafe_allow_html=True)
        first_image = IMAGES_DIR / "Beispielbild 1.jpeg"
        if first_image.is_file():
            st.image(str(first_image), use_container_width=True)
        min_distance, max_distance = st.slider(
            "Distance (km)", 0.0, float(max_distance_limit),
            (0.0, float(max_distance_limit)), step=0.5,
        )
        min_ascent, max_ascent = st.slider(
            "Ascent (m)", 0, max_ascent_limit, (0, max_ascent_limit), step=50,
        )
        min_descent, max_descent = st.slider(
            "Descent (m)", 0, max_descent_limit, (0, max_descent_limit), step=50,
        )
        min_duration_h, max_duration_h = st.slider(
            "Duration (hours)", 0.0, float(max_duration_hours),
            (0.0, float(max_duration_hours)), step=0.5,
        )
        difficulty_options = ["easy", "medium", "difficult"]
        selected_technical = st.multiselect("Technical difficulty", difficulty_options)
        selected_endurance = st.multiselect("Endurance difficulty", difficulty_options)
        st.caption("No difficulty selected = all levels accepted.")

    with travel_col:
        st.markdown('<div class="card-heading"><strong>🚗 How do I get there?</strong>'
                    '<span>Plan your journey to the trailhead</span></div>', unsafe_allow_html=True)
        second_image = IMAGES_DIR / "Beispielbild 2.jpeg"
        if second_image.is_file():
            st.image(str(second_image), use_container_width=True)
        st.text_input("Starting location", placeholder="e.g. Zürich", disabled=True)
        st.slider("Maximum driving time (minutes)", 0, 240, 90, disabled=True)
        st.markdown('<div class="future-note">Coming soon: car route calculations. '
                    'Travel inputs will be enabled when the routing module is connected.</div>',
                    unsafe_allow_html=True)

    with weather_col:
        st.markdown('<div class="card-heading"><strong>☀️ Weather</strong>'
                    '<span>Find suitable conditions for your hike</span></div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="height:145px;border-radius:14px;margin-bottom: .4rem;'
            'background:linear-gradient(130deg,#c4d6cb,#9cb8b2 55%,#e3dcc3);'
            'display:flex;align-items:center;justify-content:center;font-size:3.5rem">⛅</div>',
            unsafe_allow_html=True,
        )
        st.date_input("Hiking date", disabled=True)
        st.multiselect("Preferred weather", ["Sunny", "Cloudy", "Dry"], disabled=True)
        st.markdown('<div class="future-note">Coming soon: wetter_daten.json and '
                    'weather filter logic. Weather does not affect results yet.</div>',
                    unsafe_allow_html=True)

    st.write("")
    submitted = st.form_submit_button("Find my hikes →", type="primary", use_container_width=True)

if submitted:
    filtered_hikes = filter_hikes(
        hikes,
        min_distance=min_distance,
        max_distance=max_distance,
        min_ascent=min_ascent,
        max_ascent=max_ascent,
        min_descent=min_descent,
        max_descent=max_descent,
        min_duration=min_duration_h * 60,
        max_duration=max_duration_h * 60,
        selected_technical=selected_technical,
        selected_endurance=selected_endurance,
    )
    st.session_state["matching_hikes"] = filtered_hikes

if "matching_hikes" in st.session_state:
    results = st.session_state["matching_hikes"]
    st.markdown('<h2 class="result-header">Your matching hikes</h2>', unsafe_allow_html=True)
    st.metric("Matching hikes", len(results))
    st.caption("Results currently use hiking filters only; car routes and weather are not applied yet.")

    if not results:
        st.info("No hikes match your selection. Try widening the filters.")
    else:
        # Don't render hundreds of result cards at once.
        count_to_show = st.selectbox("Show first", [10, 20, 50], index=1)
        for hike in results[:count_to_show]:
            with st.container(border=True):
                st.subheader(str(hike.get("name") or "Unnamed hike"))
                metrics = st.columns(4)
                metrics[0].write(f"🥾 {hike['distance_km']} km")
                metrics[1].write(f"↗ {hike['ascent_m']} m")
                metrics[2].write(f"↘ {hike['descent_m']} m")
                metrics[3].write(f"⏱ {hike['duration_min'] / 60:.1f} h")
                st.caption(
                    f"Technical: {hike['technical_difficulty']}  ·  "
                    f"Endurance: {hike['endurance_difficulty']}"
                )
        if len(results) > count_to_show:
            st.caption(f"Showing {count_to_show} of {len(results)} matching hikes.")
else:
    st.info("Choose your preferences above and click ‘Find my hikes’ to see results.")
