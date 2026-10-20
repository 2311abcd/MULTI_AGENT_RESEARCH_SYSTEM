import html
import re
import time
from urllib.parse import urlparse

import streamlit as st

from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

st.set_page_config(page_title="Relay - research with four agents", page_icon="🛰️", layout="wide")

# ------------------------------------------------------------------ styling
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Instrument+Sans:wght@400;500;600&display=swap');

:root{
  --paper:#EDEFF7; --ink:#141833; --blue:#3636F0; --mint:#1FCF9D;
  --amber:#FFB21F; --rose:#FF5D73; --muted:#6A6F8C; --card:#FFFFFF;
  --display:'Bricolage Grotesque',system-ui,sans-serif;
  --body:'Instrument Sans',system-ui,sans-serif;
}
.stApp{background:var(--paper);}
.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp div{font-family:var(--body);}
.stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4{color:var(--ink);}
#MainMenu, footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1080px; padding-top:2.2rem; padding-bottom:5rem;}

/* hero */
.hero h1{font-family:var(--display); font-weight:800; font-size:clamp(2.4rem,5.5vw,4.4rem);
  line-height:1.02; letter-spacing:-.03em; margin:0 0 .9rem 0; max-width:15ch; color:var(--ink);}
.hero p{font-size:1.15rem; color:var(--muted); max-width:52ch; margin:0 0 1.6rem 0; line-height:1.5;}

/* input */
div[data-testid="stForm"]{border:none; padding:0; background:transparent;}
.stTextInput input{font-size:1.1rem; padding:1rem 1.2rem; border-radius:16px; border:2px solid var(--ink);
  background:#fff; color:var(--ink); height:3.4rem;}
.stTextInput input:focus{border-color:var(--blue); box-shadow:0 0 0 4px rgba(54,54,240,.18);}
.stFormSubmitButton button, .stButton button{border-radius:16px; font-family:var(--display); font-weight:700;
  transition:transform .15s, background .15s, color .15s;}
.stFormSubmitButton button{background:var(--ink); color:#fff; border:none; height:3.4rem; font-size:1.05rem; width:100%;}
.stFormSubmitButton button:hover{background:var(--blue); color:#fff; transform:translateY(-2px);}
.stFormSubmitButton button p{color:#fff;}
.stButton button{background:#fff; border:1.5px solid rgba(20,24,51,.18); color:var(--ink); font-weight:500;
  font-family:var(--body); font-size:.9rem; padding:.35rem .9rem; min-height:0;}
.stButton button:hover{border-color:var(--blue); color:var(--blue); transform:translateY(-2px);}
.stButton button p{color:inherit;}

/* pipeline rail: the memorable element */
.rail{background:var(--ink); border-radius:26px; padding:1.8rem 2rem 1.5rem; margin:1.6rem 0 .8rem;
  display:flex; align-items:flex-start; gap:0;}
.node{width:150px; flex:none; text-align:center;}
.dot{width:46px; height:46px; border-radius:50%; margin:0 auto .7rem; display:grid; place-items:center;
  font-family:var(--display); font-weight:800; font-size:1.1rem; background:#2A2F52; color:#8D92B5;
  transition:background .3s, color .3s;}
.node.active .dot{background:var(--amber); color:var(--ink); animation:pulse 1.5s infinite;}
.node.done .dot{background:var(--mint); color:var(--ink);}
.node.fail .dot{background:var(--rose); color:#fff;}
.nname{font-family:var(--display); font-weight:700; font-size:1.1rem; color:#fff;}
.node.wait .nname{color:#8D92B5;}
.ndesc{font-size:.85rem; color:#9DA2C4; margin-top:.15rem;}
.ntime{font-size:.85rem; color:var(--mint); margin-top:.35rem; min-height:1.1rem; font-weight:600;}
.link{flex:1; height:4px; margin-top:21px; border-radius:2px; background:#2A2F52; min-width:20px;}
.link.done{background:var(--mint);}
.link.active{background:repeating-linear-gradient(90deg,var(--amber) 0 12px,#2A2F52 12px 24px);
  background-size:48px 4px; animation:flow .8s linear infinite;}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,178,31,.55);}70%{box-shadow:0 0 0 16px rgba(255,178,31,0);}100%{box-shadow:0 0 0 0 rgba(255,178,31,0);}}
@keyframes flow{to{background-position:48px 0;}}

.note{font-size:1rem; color:var(--muted); min-height:1.6rem; margin:.2rem 0 1.4rem .3rem;}
.stats{display:flex; gap:1.2rem; flex-wrap:wrap; margin:.4rem 0 1.4rem;}
.stat{background:#fff; border-radius:14px; padding:.55rem 1rem; font-size:.95rem; color:var(--muted);}
.stat b{font-family:var(--display); font-size:1.15rem; color:var(--ink); margin-right:.35rem;}

/* tabs */
button[data-baseweb="tab"]{font-family:var(--display); font-weight:700; font-size:1.02rem; color:var(--muted);}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--ink);}
div[data-baseweb="tab-highlight"]{background:var(--blue); height:3px;}

/* report paper */
.st-key-paper{background:#fff; border-radius:22px; padding:2.2rem 2.8rem; box-shadow:0 18px 40px -22px rgba(20,24,51,.35);}
.st-key-paper h1,.st-key-paper h2,.st-key-paper h3{font-family:var(--display); letter-spacing:-.02em;}
.st-key-paper p,.st-key-paper li{font-size:1.05rem; line-height:1.7; max-width:72ch;}

/* critic */
.verdict{display:flex; gap:2rem; align-items:center; background:#fff; border-radius:22px; padding:1.6rem 2rem; margin-bottom:1rem;}
.ring{position:relative; width:130px; height:130px; flex:none;}
.ring svg{transform:rotate(-90deg);}
.ring circle{fill:none; stroke-width:12; stroke-linecap:round;}
.ring .bg{stroke:#E4E7F3;}
.ring .fg{stroke-dasharray:326.7; animation:fill 1.3s ease-out;}
@keyframes fill{from{stroke-dashoffset:326.7;}}
.ring .num{position:absolute; inset:0; display:grid; place-items:center; font-family:var(--display);
  font-weight:800; font-size:2.1rem; color:var(--ink);}
.ring .num small{font-size:.95rem; color:var(--muted); font-weight:500;}
.vtext{font-family:var(--display); font-size:1.5rem; font-weight:700; line-height:1.25; color:var(--ink);}
.cols{display:grid; grid-template-columns:1fr 1fr; gap:1rem;}
.fb{background:#fff; border-radius:20px; padding:1.3rem 1.6rem; border-left:6px solid var(--mint);}
.fb.imp{border-left-color:var(--amber);}
.fb h4{font-family:var(--display); margin:0 0 .6rem 0; font-size:1.15rem;}
.fb ul{margin:0; padding-left:1.1rem;}
.fb li{margin-bottom:.45rem; line-height:1.5; color:var(--ink);}

/* sources */
.src{display:flex; align-items:center; gap:1rem; background:#fff; border-radius:16px; padding:.9rem 1.2rem;
  margin-bottom:.6rem; text-decoration:none !important; transition:transform .15s, box-shadow .15s;}
.src:hover{transform:translateX(6px); box-shadow:0 8px 20px -12px rgba(20,24,51,.4);}
.src .d{font-family:var(--display); font-weight:700; color:var(--ink); min-width:180px;}
.src .u{color:var(--muted); font-size:.9rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}

@media (max-width:760px){
  .rail{flex-direction:column; align-items:center; gap:1rem;} .link{display:none;}
  .verdict{flex-direction:column; text-align:center;} .cols{grid-template-columns:1fr;}
  .st-key-paper{padding:1.4rem;} .src .d{min-width:0;}
}
@media (prefers-reduced-motion:reduce){ .node.active .dot,.link.active,.ring .fg{animation:none;} }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ------------------------------------------------------------------ helpers
STAGES = [
    ("Search", "Finds fresh sources"),
    ("Read", "Opens the best page"),
    ("Write", "Drafts the report"),
    ("Review", "Scores the draft"),
]
SUGGESTIONS = [
    "Solid-state batteries in 2026",
    "How AI is changing drug discovery",
    "India's space program",
    "State of quantum computing",
]


def tracker_html(status, times):
    parts = ['<div class="rail">']
    for i, (name, desc) in enumerate(STAGES):
        s = status[i]
        mark = "✓" if s == "done" else ("!" if s == "fail" else str(i + 1))
        t = f"{times[i]:.1f}s" if times[i] is not None else ""
        parts.append(
            f'<div class="node {s}"><div class="dot">{mark}</div>'
            f'<div class="nname">{name}</div><div class="ndesc">{desc}</div>'
            f'<div class="ntime">{t}</div></div>'
        )
        if i < len(STAGES) - 1:
            nxt = status[i + 1]
            link = "done" if s == "done" and nxt != "wait" else ("active" if s == "done" and nxt == "wait" else "")
            if s == "done" and nxt == "active":
                link = "active"
            elif s == "done":
                link = "done"
            parts.append(f'<div class="link {link}"></div>')
    parts.append("</div>")
    return "".join(parts)


def extract_sources(*texts):
    seen, out = set(), []
    for t in texts:
        for u in re.findall(r"https?://[^\s\)\]>\"']+", t or ""):
            u = u.rstrip(".,;:")
            if u not in seen:
                seen.add(u)
                out.append(u)
    return out


def parse_feedback(text):
    score = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", text)
    good = re.search(r"Strengths:\s*(.*?)\s*Areas to Improve:", text, re.S)
    imp = re.search(r"Areas to Improve:\s*(.*?)\s*One line verdict:", text, re.S)
    ver = re.search(r"One line verdict:\s*(.*)", text, re.S)

    def bullets(m):
        if not m:
            return []
        return [l.lstrip("-*• ").strip() for l in m.group(1).splitlines() if l.strip()]

    return (
        float(score.group(1)) if score else None,
        bullets(good),
        bullets(imp),
        ver.group(1).strip() if ver else "",
    )


def li(items):
    return "".join(f"<li>{html.escape(x)}</li>" for x in items)


def run_pipeline(topic, rail, note):
    status, times, state = ["wait"] * 4, [None] * 4, {}

    def draw():
        rail.markdown(tracker_html(status, times), unsafe_allow_html=True)

    def search():
        r = build_search_agent().invoke(
            {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]}
        )
        state["search_results"] = r["messages"][-1].content

    def read():
        r = build_reader_agent().invoke({"messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}")]})
        state["scraped_content"] = r["messages"][-1].content

    def write():
        research = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({"topic": topic, "research": research})

    def review():
        state["feedback"] = critic_chain.invoke({"report": state["report"]})

    steps = [
        (search, "Searching the web for sources…"),
        (read, "Picking the best result and reading the page…"),
        (write, "Writing the report from everything gathered…"),
        (review, "The critic is grading the draft…"),
    ]
    start = time.time()
    draw()
    for i, (fn, msg) in enumerate(steps):
        status[i] = "active"
        draw()
        note.markdown(f'<div class="note">{msg}</div>', unsafe_allow_html=True)
        t0 = time.time()
        try:
            fn()
        except Exception:
            status[i] = "fail"
            draw()
            raise
        times[i] = time.time() - t0
        status[i] = "done"
        draw()
    note.empty()
    state["times"] = times
    state["total"] = time.time() - start
    state["topic"] = topic
    return state


# ------------------------------------------------------------------ session
st.session_state.setdefault("state", None)
st.session_state.setdefault("history", [])
st.session_state.setdefault("auto_run", False)
st.session_state.setdefault("fresh", False)
st.session_state.setdefault("topic_input", "")


def pick(s):
    st.session_state.topic_input = s
    st.session_state.auto_run = True


def load(i):
    st.session_state.state = st.session_state.history[i]
    st.session_state.fresh = False
    st.session_state.topic_input = st.session_state.history[i]["topic"]


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### Past runs")
    if not st.session_state.history:
        st.caption("Finished reports show up here so you can reopen them.")
    for i in reversed(range(len(st.session_state.history))):
        h = st.session_state.history[i]
        st.button(h["topic"][:34], key=f"h{i}", on_click=load, args=(i,), use_container_width=True)

# ------------------------------------------------------------------ hero + input
st.markdown(
    '<div class="hero"><h1>Ask once. Four agents do the reading.</h1>'
    "<p>One agent searches the web, another reads the best page, a third writes the report, "
    "and a critic grades it. Watch each hand-off happen.</p></div>",
    unsafe_allow_html=True,
)

with st.form("ask", border=False):
    c1, c2 = st.columns([5, 1.3], vertical_alignment="center")
    c1.text_input("Topic", key="topic_input", placeholder="What do you want researched?",
                  label_visibility="collapsed")
    submitted = c2.form_submit_button("Research it")

chip_cols = st.columns(len(SUGGESTIONS))
for col, s in zip(chip_cols, SUGGESTIONS):
    col.button(s, key=f"s_{s}", on_click=pick, args=(s,), use_container_width=True)

rail = st.empty()
note = st.empty()

topic = st.session_state.topic_input.strip()
go = (submitted or st.session_state.auto_run) and bool(topic)
st.session_state.auto_run = False
if submitted and not topic:
    st.warning("Type a topic first, then press Research it.")

# ------------------------------------------------------------------ run
if go:
    try:
        new_state = run_pipeline(topic, rail, note)
        st.session_state.state = new_state
        st.session_state.history.append(new_state)
        st.session_state.fresh = True
    except Exception as e:
        st.error(f"The run stopped at the step marked in red: {e}. "
                 "Check that your MISTRAL_API_KEY and TAVILY_API_KEY are set, then try again.")
        st.stop()
elif st.session_state.state:
    s = st.session_state.state
    rail.markdown(tracker_html(["done"] * 4, s["times"]), unsafe_allow_html=True)
else:
    rail.markdown(tracker_html(["wait"] * 4, [None] * 4), unsafe_allow_html=True)
    note.markdown('<div class="note">Pick a topic above or type your own to start.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ results
state = st.session_state.state
if state:
    sources = extract_sources(state["search_results"], state["scraped_content"], state["report"])
    words = len(state["report"].split())
    st.markdown(
        f'<div class="stats"><div class="stat"><b>{state["total"]:.0f}s</b>total time</div>'
        f'<div class="stat"><b>{len(sources)}</b>sources found</div>'
        f'<div class="stat"><b>{words}</b>words written</div></div>',
        unsafe_allow_html=True,
    )

    t_report, t_critic, t_sources, t_raw = st.tabs(["Report", "Critic", "Sources", "Raw agent output"])

    with t_report:
        with st.container(key="paper"):
            if st.session_state.fresh:
                box = st.empty()
                parts = state["report"].split(" ")
                step = max(4, len(parts) // 90)
                for k in range(step, len(parts) + step, step):
                    box.markdown(" ".join(parts[:k]))
                    time.sleep(0.02)
                st.session_state.fresh = False
            else:
                st.markdown(state["report"])
        st.download_button("Download report (.md)", state["report"],
                           file_name="research_report.md", mime="text/markdown")

    with t_critic:
        score, good, imp, verdict = parse_feedback(state["feedback"])
        if score is None or not (good or imp):
            st.markdown(state["feedback"])
        else:
            color = "#1FCF9D" if score >= 8 else ("#FFB21F" if score >= 6 else "#FF5D73")
            offset = 326.7 * (1 - score / 10)
            st.markdown(
                f'<div class="verdict"><div class="ring">'
                f'<svg width="130" height="130" viewBox="0 0 130 130">'
                f'<circle class="bg" cx="65" cy="65" r="52"/>'
                f'<circle class="fg" cx="65" cy="65" r="52" style="stroke:{color};stroke-dashoffset:{offset:.1f}"/></svg>'
                f'<div class="num"><span>{score:g}<small>/10</small></span></div></div>'
                f'<div class="vtext">{html.escape(verdict)}</div></div>'
                f'<div class="cols"><div class="fb"><h4>What worked</h4><ul>{li(good)}</ul></div>'
                f'<div class="fb imp"><h4>What to improve</h4><ul>{li(imp)}</ul></div></div>',
                unsafe_allow_html=True,
            )

    with t_sources:
        if not sources:
            st.info("No links were found in the agent output for this topic.")
        for u in sources:
            p = urlparse(u)
            dom = p.netloc.replace("www.", "")
            st.markdown(
                f'<a class="src" href="{html.escape(u)}" target="_blank" rel="noopener">'
                f'<span class="d">{html.escape(dom)}</span><span class="u">{html.escape(u)}</span></a>',
                unsafe_allow_html=True,
            )

    with t_raw:
        with st.expander("Search agent"):
            st.text(state["search_results"])
        with st.expander("Reader agent"):
            st.text(state["scraped_content"])