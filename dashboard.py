"""Clinical Trial Intelligence Dashboard -- 5-tab dark Plotly Dash app."""
import math
import json
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

import scheduler
import store
import nlp
from config import (
    BG, CARD_BG, BORDER, TEXT, MUTED, ACCENT, GREEN, RED, YELLOW, BLUE, ORANGE,
    STATUS_COLORS, PHASE_ORDER, PHASE_LABELS, PHASE_COLORS,
    DISEASE_AREAS, REFRESH_INTERVAL_S,
)

# Shared Plotly layout defaults
PL = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d0d20",
    font=dict(color=TEXT, family="Inter, Segoe UI, system-ui, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
)

PAGE_SIZE  = 25
GRID_COLOR = "rgba(255,255,255,0.05)"

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="Clinical Trial Intelligence",
)
server = app.server
scheduler.start()


def _card(*children, style=None):
    """Return a glassmorphism-styled card div."""
    base = {
        "background":   CARD_BG,
        "border":       f"1px solid {BORDER}",
        "borderRadius": "12px",
        "padding":      "20px",
        "marginBottom": "16px",
    }
    if style:
        base.update(style)
    return html.Div(list(children), style=base)


def _kpi(label, value, color=TEXT):
    """Return a single KPI card element."""
    return html.Div([
        html.Div(str(value), style={
            "fontSize": "2rem", "fontWeight": "700",
            "color": color, "lineHeight": "1.1",
        }),
        html.Div(label, style={"fontSize": "0.78rem", "color": MUTED, "marginTop": "4px"}),
    ], style={
        "background":   CARD_BG,
        "border":       f"1px solid {BORDER}",
        "borderRadius": "12px",
        "padding":      "18px 22px",
        "flex":         "1",
        "minWidth":     "160px",
    })


def _empty_fig(msg="No data yet"):
    """Return a blank figure placeholder with a centred message."""
    fig = go.Figure()
    fig.update_layout(
        **PL,
        annotations=[dict(
            text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(color=MUTED, size=14),
        )],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _phase_label(p):
    """Return the human-readable label for a phase code."""
    return PHASE_LABELS.get(p, p)


def _status_badge(status):
    """Return a coloured inline badge for a trial status string."""
    color = STATUS_COLORS.get(status, STATUS_COLORS["UNKNOWN"])
    label = status.replace("_", " ").title() if status else "Unknown"
    return html.Span(label, style={
        "background":   color + "22",
        "color":        color,
        "border":       f"1px solid {color}55",
        "borderRadius": "20px",
        "padding":      "2px 10px",
        "fontSize":     "0.72rem",
        "fontWeight":   "600",
        "whiteSpace":   "nowrap",
    })

# Header
header = html.Div([
    html.Div([
        html.Div([
            html.H1("Clinical Trial Intelligence Dashboard", style={
                "fontSize": "1.6rem", "fontWeight": "800",
                "background": "linear-gradient(135deg, #e2e2f0, #7c3aed)",
                "WebkitBackgroundClip": "text",
                "WebkitTextFillColor": "transparent",
                "margin": "0",
            }),
            html.P(
                "Real-time insights from ClinicalTrials.gov API v2",
                style={"color": MUTED, "margin": "4px 0 0", "fontSize": "0.85rem"},
            ),
        ]),
        html.Div([
            html.Span(id="last-updated", style={
                "color": MUTED, "fontSize": "0.78rem", "marginRight": "14px",
            }),
            html.Button("Refresh Now", id="btn-refresh", n_clicks=0, style={
                "background":   "linear-gradient(135deg, #7c3aed, #6d28d9)",
                "border":       "none",
                "borderRadius": "8px",
                "color":        "#fff",
                "fontWeight":   "600",
                "padding":      "8px 18px",
                "cursor":       "pointer",
                "fontSize":     "0.82rem",
            }),
        ], style={"display": "flex", "alignItems": "center"}),
    ], style={
        "display":        "flex",
        "justifyContent": "space-between",
        "alignItems":     "center",
        "maxWidth":       "1400px",
        "margin":         "0 auto",
        "padding":        "0 24px",
    }),
], style={
    "background":   "linear-gradient(135deg, rgba(18,18,42,0.98), rgba(30,20,60,0.98))",
    "borderBottom": "1px solid rgba(255,255,255,0.08)",
    "padding":      "18px 0",
})

TABS = [
    ("tab-overview", "Pipeline Overview"),
    ("tab-disease",  "Disease Intelligence"),
    ("tab-sponsors", "Sponsor Leaderboard"),
    ("tab-geo",      "Geographic Distribution"),
    ("tab-tracker",  "Trial Tracker"),
]

tab_bar = dcc.Tabs(
    id="main-tabs",
    value="tab-overview",
    className="custom-tabs",
    children=[
        dcc.Tab(label=label, value=val,
                style={
                    "background":    "rgba(18,18,42,0.6)",
                    "border":        "1px solid rgba(255,255,255,0.08)",
                    "borderBottom":  "none",
                    "color":         MUTED,
                    "padding":       "10px 20px",
                    "fontSize":      "0.85rem",
                    "fontWeight":    "500",
                    "letterSpacing": "0.02em",
                    "borderRadius":  "8px 8px 0 0",
                    "marginRight":   "4px",
                },
                selected_style={
                    "background":   "rgba(124,58,237,0.25)",
                    "borderColor":  "rgba(124,58,237,0.5)",
                    "borderBottom": "2px solid #7c3aed",
                    "color":        TEXT,
                    "padding":      "10px 20px",
                    "fontSize":     "0.85rem",
                    "fontWeight":   "600",
                    "borderRadius": "8px 8px 0 0",
                    "marginRight":  "4px",
                })
        for val, label in TABS
    ],
)

app.layout = html.Div([
    header,
    html.Div([
        tab_bar,
        html.Div(id="tab-content", style={
            "border":       "1px solid rgba(255,255,255,0.08)",
            "borderRadius": "0 8px 8px 8px",
            "padding":      "24px",
            "background":   "transparent",
            "marginTop":    "-1px",
        }),
    ], style={"maxWidth": "1400px", "margin": "0 auto", "padding": "0 24px 40px"}),

    dcc.Interval(id="interval", interval=REFRESH_INTERVAL_S * 1000, n_intervals=0),
    dcc.Store(id="tracker-page", data=0),
], style={"background": BG, "minHeight": "100vh",
          "fontFamily": "Inter, Segoe UI, system-ui, sans-serif"})


# Tab routing callback
@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def render_tab(tab):
    """Render the selected tab layout shell."""
    if tab == "tab-overview":
        return _layout_overview()
    if tab == "tab-disease":
        return _layout_disease()
    if tab == "tab-sponsors":
        return _layout_sponsors()
    if tab == "tab-geo":
        return _layout_geo()
    if tab == "tab-tracker":
        return _layout_tracker()
    return html.Div("Unknown tab")


# --- TAB 1: Pipeline Overview ---

def _layout_overview():
    """Return the Pipeline Overview tab layout shell."""
    return html.Div([
        html.Div(id="kpi-row", style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),
        html.Div([
            html.Div(dcc.Graph(id="fig-phase-funnel", config={"displayModeBar": False}),
                     style={"flex": "1"}),
            html.Div(dcc.Graph(id="fig-status-donut", config={"displayModeBar": False}),
                     style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "16px"}),
        _card(dcc.Graph(id="fig-top-sponsors", config={"displayModeBar": False})),
    ])


@app.callback(
    Output("kpi-row",          "children"),
    Output("fig-phase-funnel", "figure"),
    Output("fig-status-donut", "figure"),
    Output("fig-top-sponsors", "figure"),
    Output("last-updated",     "children"),
    Input("interval",    "n_intervals"),
    Input("btn-refresh", "n_clicks"),
)
def update_overview(n_intervals, n_clicks):
    """Populate all Pipeline Overview visuals from the current DB snapshot."""
    ctx = callback_context
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "btn-refresh.n_clicks" and n_clicks:
        scheduler.force_refresh()

    df    = store.get_trials()
    stats = store.get_stats()

    total       = stats.get("total", 0)
    recruiting  = stats.get("by_status", {}).get("RECRUITING", 0)
    n_countries = len(stats.get("by_country", {}))

    avg_dur = 0
    if not df.empty and "start_date" in df.columns and "completion_date" in df.columns:
        try:
            sub = df.dropna(subset=["start_date", "completion_date"]).copy()
            sub["start_dt"] = pd.to_datetime(sub["start_date"], errors="coerce")
            sub["end_dt"]   = pd.to_datetime(sub["completion_date"], errors="coerce")
            sub = sub.dropna(subset=["start_dt", "end_dt"])
            if not sub.empty:
                sub["dur_m"] = (sub["end_dt"] - sub["start_dt"]).dt.days / 30.44
                sub = sub[sub["dur_m"].between(1, 600)]
                avg_dur = round(sub["dur_m"].mean(), 1) if not sub.empty else 0
        except Exception:
            pass

    kpis = html.Div([
        _kpi("Total Trials",        f"{total:,}",      ACCENT),
        _kpi("Actively Recruiting", f"{recruiting:,}", GREEN),
        _kpi("Avg Duration (mo)",   f"{avg_dur}",      BLUE),
        _kpi("Countries Covered",   f"{n_countries:,}", YELLOW),
    ], style={"display": "flex", "gap": "16px", "width": "100%"})

    if df.empty:
        empty = _empty_fig()
        return kpis, empty, empty, empty, scheduler.last_run_str()

    # Phase funnel (horizontal bar)
    by_phase = stats.get("by_phase", {})
    phases   = [p for p in PHASE_ORDER if p in by_phase]
    counts   = [by_phase[p] for p in phases]
    labels   = [_phase_label(p) for p in phases]
    colors   = [PHASE_COLORS.get(p, MUTED) for p in phases]

    fig_funnel = go.Figure(go.Bar(
        x=counts, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{c:,}" for c in counts],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    fig_funnel.update_layout(
        **PL,
        title=dict(text="Trial Phase Distribution", font=dict(size=14, color=TEXT), x=0),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED, title="Number of Trials"),
        yaxis=dict(showgrid=False, color=MUTED, autorange="reversed"),
        height=340, showlegend=False,
    )

    # Status donut
    by_status = stats.get("by_status", {})
    s_labels  = list(by_status.keys())
    s_values  = list(by_status.values())
    s_colors  = [STATUS_COLORS.get(s, STATUS_COLORS["UNKNOWN"]) for s in s_labels]

    fig_donut = go.Figure(go.Pie(
        labels=s_labels, values=s_values, hole=0.55,
        marker=dict(colors=s_colors, line=dict(color=BG, width=2)),
        textinfo="percent",
        hovertemplate="%{label}: %{value:,}<extra></extra>",
    ))
    fig_donut.update_layout(
        **PL,
        title=dict(text="Status Breakdown", font=dict(size=14, color=TEXT), x=0),
        legend=dict(font=dict(color=TEXT, size=10), bgcolor="rgba(0,0,0,0)"),
        height=340,
    )

    # Top 10 sponsors
    if "sponsor" in df.columns:
        top_sp = (
            df.dropna(subset=["sponsor"])
              .groupby("sponsor").size()
              .nlargest(10).reset_index(name="count")
        )
        fig_sponsors = go.Figure(go.Bar(
            x=top_sp["count"], y=top_sp["sponsor"], orientation="h",
            marker=dict(
                color=list(range(len(top_sp))),
                colorscale=[[0, BLUE], [0.5, ACCENT], [1, "#a855f7"]],
                showscale=False,
            ),
            text=[f"{c:,}" for c in top_sp["count"]],
            textposition="outside",
            textfont=dict(color=TEXT, size=10),
            hovertemplate="%{y}: %{x:,}<extra></extra>",
        ))
        fig_sponsors.update_layout(
            **PL,
            title=dict(text="Top 10 Sponsors by Trial Count", font=dict(size=14, color=TEXT), x=0),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
            yaxis=dict(showgrid=False, color=MUTED, autorange="reversed"),
            height=380, showlegend=False,
        )
    else:
        fig_sponsors = _empty_fig("No sponsor data")

    return kpis, fig_funnel, fig_donut, fig_sponsors, scheduler.last_run_str()


# --- TAB 2: Disease Intelligence ---

def _layout_disease():
    """Return the Disease Intelligence tab layout shell."""
    return html.Div([
        _card(dcc.Graph(id="fig-treemap", config={"displayModeBar": False})),
        html.Div([
            html.Div(dcc.Graph(id="fig-trending",     config={"displayModeBar": False}),
                     style={"flex": "1"}),
            html.Div(dcc.Graph(id="fig-disease-phase", config={"displayModeBar": False}),
                     style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px"}),
    ])


@app.callback(
    Output("fig-treemap",       "figure"),
    Output("fig-trending",      "figure"),
    Output("fig-disease-phase", "figure"),
    Input("interval",    "n_intervals"),
    Input("btn-refresh", "n_clicks"),
)
def update_disease(n_intervals, n_clicks):
    """Populate all Disease Intelligence visuals."""
    df = store.get_trials()
    if df.empty:
        empty = _empty_fig()
        return empty, empty, empty

    # Treemap: disease area -> conditions
    try:
        rows = []
        for _, r in df.iterrows():
            area  = r.get("disease_area") or "Unknown"
            conds = r.get("conditions") or []
            for c in (conds if isinstance(conds, list) else []):
                rows.append({"area": area, "condition": str(c).strip()[:60]})

        cdf = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["area", "condition"])
        if not cdf.empty:
            cdf_counts = (
                cdf.groupby(["area", "condition"]).size()
                   .reset_index(name="count")
                   .sort_values("count", ascending=False)
                   .groupby("area").head(8)
                   .reset_index(drop=True)
            )
            area_totals = cdf_counts.groupby("area")["count"].sum().reset_index()
            area_totals.columns = ["area", "count"]

            ids     = (["World"]
                       + list(area_totals["area"])
                       + list(cdf_counts.apply(lambda r: r["area"] + "|" + r["condition"], axis=1)))
            labels  = ["World"] + list(area_totals["area"]) + list(cdf_counts["condition"])
            parents = [""] + ["World"] * len(area_totals) + list(cdf_counts["area"])
            values  = [0] + list(area_totals["count"]) + list(cdf_counts["count"])

            fig_tree = go.Figure(go.Treemap(
                ids=ids, labels=labels, parents=parents, values=values,
                branchvalues="total",
                marker=dict(
                    colorscale=[[0, "#1e1e3f"], [0.5, ACCENT], [1, "#a855f7"]],
                    line=dict(color=BG, width=1),
                ),
                textfont=dict(color=TEXT, size=11),
                hovertemplate="<b>%{label}</b><br>Count: %{value:,}<extra></extra>",
            ))
            fig_tree.update_layout(
                **PL,
                title=dict(text="Disease Areas and Conditions", font=dict(size=14, color=TEXT), x=0),
                height=420,
            )
        else:
            fig_tree = _empty_fig("No condition data")
    except Exception as exc:
        print(f"[dashboard] treemap error: {exc}")
        fig_tree = _empty_fig("Treemap error")

    # Trending conditions
    trending = nlp.get_trending_conditions(df, top_n=15)
    if not trending.empty:
        fig_trend = go.Figure(go.Bar(
            x=trending["count"], y=trending["condition"], orientation="h",
            marker=dict(
                color=list(range(len(trending))),
                colorscale=[[0, BLUE], [1, GREEN]],
                showscale=False,
            ),
            text=trending["count"].astype(str),
            textposition="outside",
            textfont=dict(color=TEXT, size=10),
            hovertemplate="%{y}: %{x:,}<extra></extra>",
        ))
        fig_trend.update_layout(
            **PL,
            title=dict(text="Top 15 Trending Conditions", font=dict(size=14, color=TEXT), x=0),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
            yaxis=dict(showgrid=False, color=MUTED, autorange="reversed"),
            height=420, showlegend=False,
        )
    else:
        fig_trend = _empty_fig("No condition data")

    # Disease area vs phase stacked bar
    try:
        dp     = df.groupby(["disease_area", "phase"]).size().reset_index(name="count")
        fig_dp = go.Figure()
        for phase in PHASE_ORDER:
            sub = dp[dp["phase"] == phase]
            if sub.empty:
                continue
            fig_dp.add_trace(go.Bar(
                name=_phase_label(phase),
                x=sub["disease_area"],
                y=sub["count"],
                marker_color=PHASE_COLORS.get(phase, MUTED),
                hovertemplate=_phase_label(phase) + ": %{y:,}<extra></extra>",
            ))
        fig_dp.update_layout(
            **PL,
            title=dict(text="Disease Area vs Phase", font=dict(size=14, color=TEXT), x=0),
            barmode="stack",
            xaxis=dict(showgrid=False, color=MUTED, tickangle=-20),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
            legend=dict(font=dict(color=TEXT, size=10), bgcolor="rgba(0,0,0,0)"),
            height=420,
        )
    except Exception as exc:
        print(f"[dashboard] disease-phase error: {exc}")
        fig_dp = _empty_fig()

    return fig_tree, fig_trend, fig_dp


# --- TAB 3: Sponsor Leaderboard ---

def _layout_sponsors():
    """Return the Sponsor Leaderboard tab layout shell."""
    return html.Div([
        html.Div(id="sponsor-kpis",
                 style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),
        html.Div([
            html.Div(dcc.Graph(id="fig-top20-sponsors", config={"displayModeBar": False}),
                     style={"flex": "1"}),
            html.Div(dcc.Graph(id="fig-sponsor-phase",  config={"displayModeBar": False}),
                     style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px"}),
    ])


@app.callback(
    Output("sponsor-kpis",       "children"),
    Output("fig-top20-sponsors", "figure"),
    Output("fig-sponsor-phase",  "figure"),
    Input("interval",    "n_intervals"),
    Input("btn-refresh", "n_clicks"),
)
def update_sponsors(n_intervals, n_clicks):
    """Populate Sponsor Leaderboard visuals and KPIs."""
    df = store.get_trials()

    if df.empty:
        kpis = html.Div([
            _kpi("Total Sponsors",       "0",   ACCENT),
            _kpi("Avg Trials / Sponsor", "0",   BLUE),
            _kpi("Most Active Sponsor",  "N/A", GREEN),
        ], style={"display": "flex", "gap": "16px", "width": "100%"})
        empty = _empty_fig()
        return kpis, empty, empty

    sp_counts = (
        df.dropna(subset=["sponsor"])
          .groupby("sponsor").size()
          .reset_index(name="count")
          .sort_values("count", ascending=False)
    )

    total_sponsors = len(sp_counts)
    avg_trials     = round(sp_counts["count"].mean(), 1) if not sp_counts.empty else 0
    most_active    = sp_counts.iloc[0]["sponsor"][:40] if not sp_counts.empty else "N/A"

    kpis = html.Div([
        _kpi("Total Sponsors",       f"{total_sponsors:,}", ACCENT),
        _kpi("Avg Trials / Sponsor", f"{avg_trials}",       BLUE),
        _kpi("Most Active Sponsor",  most_active,           GREEN),
    ], style={"display": "flex", "gap": "16px", "width": "100%"})

    # Top 20 sponsors colored by dominant phase
    top20 = sp_counts.head(20).copy()

    dom_phase_map = {}
    for sp in top20["sponsor"]:
        sub = df[df["sponsor"] == sp]
        dom_phase_map[sp] = sub["phase"].value_counts().idxmax() if not sub.empty else "NA"

    top20["dom_phase"] = top20["sponsor"].map(dom_phase_map)
    top20["color"]     = top20["dom_phase"].map(lambda p: PHASE_COLORS.get(p, MUTED))
    top20["sp_label"]  = top20["sponsor"].str[:50]

    fig_top20 = go.Figure(go.Bar(
        x=top20["count"],
        y=top20["sp_label"],
        orientation="h",
        marker_color=list(top20["color"]),
        text=[f"{c:,}" for c in top20["count"]],
        textposition="outside",
        textfont=dict(color=TEXT, size=10),
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    fig_top20.update_layout(
        **PL,
        title=dict(text="Top 20 Sponsors (colored by dominant phase)",
                   font=dict(size=14, color=TEXT), x=0),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
        yaxis=dict(showgrid=False, color=MUTED, autorange="reversed"),
        height=560, showlegend=False,
    )

    # Sponsor phase breakdown stacked bar (top 10)
    top10_names  = list(sp_counts.head(10)["sponsor"])
    sp_df        = df[df["sponsor"].isin(top10_names)]
    sp_phase_grp = sp_df.groupby(["sponsor", "phase"]).size().reset_index(name="count")

    fig_sp_phase = go.Figure()
    for phase in PHASE_ORDER:
        sub = sp_phase_grp[sp_phase_grp["phase"] == phase]
        if sub.empty:
            continue
        merged = (
            pd.DataFrame({"sponsor": top10_names})
              .merge(sub, on="sponsor", how="left")
              .fillna(0)
        )
        fig_sp_phase.add_trace(go.Bar(
            name=_phase_label(phase),
            x=merged["sponsor"].astype(str).str[:35],
            y=merged["count"],
            marker_color=PHASE_COLORS.get(phase, MUTED),
            hovertemplate=_phase_label(phase) + ": %{y:,}<extra></extra>",
        ))
    fig_sp_phase.update_layout(
        **PL,
        title=dict(text="Top 10 Sponsors - Phase Breakdown",
                   font=dict(size=14, color=TEXT), x=0),
        barmode="stack",
        xaxis=dict(showgrid=False, color=MUTED, tickangle=-25),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
        legend=dict(font=dict(color=TEXT, size=10), bgcolor="rgba(0,0,0,0)"),
        height=420,
    )

    return kpis, fig_top20, fig_sp_phase


# --- TAB 4: Geographic Distribution ---

def _layout_geo():
    """Return the Geographic Distribution tab layout shell."""
    return html.Div([
        _card(dcc.Graph(id="fig-choropleth",     config={"displayModeBar": False})),
        html.Div([
            html.Div(dcc.Graph(id="fig-top-countries",  config={"displayModeBar": False}),
                     style={"flex": "1"}),
            html.Div(dcc.Graph(id="fig-country-status", config={"displayModeBar": False}),
                     style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px"}),
    ])


@app.callback(
    Output("fig-choropleth",    "figure"),
    Output("fig-top-countries", "figure"),
    Output("fig-country-status","figure"),
    Input("interval",    "n_intervals"),
    Input("btn-refresh", "n_clicks"),
)
def update_geo(n_intervals, n_clicks):
    """Populate Geographic Distribution visuals."""
    df    = store.get_trials()
    stats = store.get_stats()

    if df.empty:
        empty = _empty_fig()
        return empty, empty, empty

    by_country = stats.get("by_country", {})
    countries  = list(by_country.keys())
    counts     = list(by_country.values())

    # Choropleth world map
    fig_choro = go.Figure(go.Choropleth(
        locations=countries,
        locationmode="country names",
        z=counts,
        colorscale=[[0, "#1e1e3f"], [0.4, ACCENT], [1, "#a855f7"]],
        zmin=0,
        zmax=max(counts) if counts else 1,
        colorbar=dict(
            title=dict(text="Trials", font=dict(color=TEXT)),
            tickfont=dict(color=TEXT),
            bgcolor="rgba(0,0,0,0)",
        ),
        marker=dict(line=dict(color=BG, width=0.5)),
        hovertemplate="<b>%{location}</b><br>Trials: %{z:,}<extra></extra>",
    ))
    fig_choro.update_layout(
        **PL,
        title=dict(text="Global Trial Distribution", font=dict(size=14, color=TEXT), x=0),
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.1)",
            showland=True,
            landcolor="#0d0d20",
            showocean=True,
            oceancolor="#060612",
            showlakes=False,
            projection_type="natural earth",
        ),
        height=440,
    )

    # Top 15 countries bar
    top15_items = sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:15]
    t_countries = [x[0] for x in top15_items]
    t_counts    = [x[1] for x in top15_items]

    fig_top = go.Figure(go.Bar(
        x=t_counts, y=t_countries, orientation="h",
        marker=dict(
            color=list(range(len(t_counts))),
            colorscale=[[0, BLUE], [1, ACCENT]],
            showscale=False,
        ),
        text=[f"{c:,}" for c in t_counts],
        textposition="outside",
        textfont=dict(color=TEXT, size=10),
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    fig_top.update_layout(
        **PL,
        title=dict(text="Top 15 Countries by Trial Count", font=dict(size=14, color=TEXT), x=0),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
        yaxis=dict(showgrid=False, color=MUTED, autorange="reversed"),
        height=420, showlegend=False,
    )

    # Country vs status stacked bar (top 10 countries)
    try:
        top10_c  = [x[0] for x in top15_items[:10]]
        exp_rows = []
        for _, row in df.iterrows():
            status = row.get("status")
            clist  = row.get("countries")
            if not isinstance(clist, list):
                continue
            for c in clist:
                if c in top10_c:
                    exp_rows.append({"country": c, "status": status})

        if exp_rows:
            c_df   = pd.DataFrame(exp_rows)
            c_grp  = c_df.groupby(["country", "status"]).size().reset_index(name="count")
            fig_cs = go.Figure()
            for st in STATUS_COLORS:
                sub = c_grp[c_grp["status"] == st]
                if sub.empty:
                    continue
                merged = (
                    pd.DataFrame({"country": top10_c})
                      .merge(sub, on="country", how="left")
                      .fillna(0)
                )
                fig_cs.add_trace(go.Bar(
                    name=st.replace("_", " ").title(),
                    x=merged["country"],
                    y=merged["count"],
                    marker_color=STATUS_COLORS[st],
                    hovertemplate=st + ": %{y:,}<extra></extra>",
                ))
            fig_cs.update_layout(
                **PL,
                title=dict(text="Country vs Status (Top 10)", font=dict(size=14, color=TEXT), x=0),
                barmode="stack",
                xaxis=dict(showgrid=False, color=MUTED, tickangle=-20),
                yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=MUTED),
                legend=dict(font=dict(color=TEXT, size=9), bgcolor="rgba(0,0,0,0)"),
                height=420,
            )
        else:
            fig_cs = _empty_fig("No country-status data")
    except Exception as exc:
        print(f"[dashboard] country-status error: {exc}")
        fig_cs = _empty_fig()

    return fig_choro, fig_top, fig_cs


# --- TAB 5: Trial Tracker ---

def _layout_tracker():
    """Return the Trial Tracker tab layout shell with search and filter controls."""
    all_statuses = ["All"] + list(STATUS_COLORS.keys())
    all_areas    = ["All"] + list(DISEASE_AREAS.keys())
    all_phases   = ["All"] + list(PHASE_LABELS.keys())

    dd_style = {
        "background":   CARD_BG,
        "border":       "1px solid " + BORDER,
        "borderRadius": "8px",
        "color":        TEXT,
        "flex":         "1",
        "minWidth":     "150px",
    }

    return html.Div([
        html.Div([
            dcc.Input(
                id="tracker-search", type="text",
                placeholder="Search title, sponsor, NCT ID...",
                debounce=True,
                style={
                    "flex":         "2",
                    "background":   CARD_BG,
                    "border":       "1px solid " + BORDER,
                    "borderRadius": "8px",
                    "color":        TEXT,
                    "padding":      "8px 14px",
                    "fontSize":     "0.85rem",
                    "outline":      "none",
                },
            ),
            dcc.Dropdown(
                id="tracker-status",
                options=[{"label": s.replace("_", " ").title(), "value": s} for s in all_statuses],
                value="All", clearable=False, style=dd_style,
            ),
            dcc.Dropdown(
                id="tracker-area",
                options=[{"label": a, "value": a} for a in all_areas],
                value="All", clearable=False, style=dd_style,
            ),
            dcc.Dropdown(
                id="tracker-phase",
                options=[{"label": PHASE_LABELS.get(p, p), "value": p} for p in all_phases],
                value="All", clearable=False, style={**dd_style, "minWidth": "120px"},
            ),
        ], style={"display": "flex", "gap": "10px", "marginBottom": "16px", "alignItems": "center"}),

        html.Div([
            html.Span(id="tracker-info", style={"color": MUTED, "fontSize": "0.8rem"}),
            html.Div([
                html.Button("< Prev", id="btn-prev", n_clicks=0, style={
                    "background":   CARD_BG,
                    "border":       "1px solid " + BORDER,
                    "color":        TEXT,
                    "borderRadius": "6px",
                    "padding":      "5px 12px",
                    "cursor":       "pointer",
                    "fontSize":     "0.8rem",
                }),
                html.Button("Next >", id="btn-next", n_clicks=0, style={
                    "background":   CARD_BG,
                    "border":       "1px solid " + BORDER,
                    "color":        TEXT,
                    "borderRadius": "6px",
                    "padding":      "5px 12px",
                    "cursor":       "pointer",
                    "fontSize":     "0.8rem",
                }),
            ], style={"display": "flex", "gap": "8px"}),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "12px"}),

        html.Div(id="tracker-table"),
    ])


@app.callback(
    Output("tracker-page", "data"),
    Input("btn-prev",       "n_clicks"),
    Input("btn-next",       "n_clicks"),
    Input("tracker-search", "value"),
    Input("tracker-status", "value"),
    Input("tracker-area",   "value"),
    Input("tracker-phase",  "value"),
    State("tracker-page",   "data"),
    prevent_initial_call=True,
)
def update_tracker_page(prev_clicks, next_clicks, search, status, area, phase, current_page):
    """Advance or retreat the tracker page, resetting to 0 on filter changes."""
    ctx = callback_context
    if not ctx.triggered:
        return 0
    trigger = ctx.triggered[0]["prop_id"]
    if trigger == "btn-next.n_clicks":
        return (current_page or 0) + 1
    if trigger == "btn-prev.n_clicks":
        return max(0, (current_page or 0) - 1)
    return 0


@app.callback(
    Output("tracker-table", "children"),
    Output("tracker-info",  "children"),
    Input("tracker-search", "value"),
    Input("tracker-status", "value"),
    Input("tracker-area",   "value"),
    Input("tracker-phase",  "value"),
    Input("tracker-page",   "data"),
    Input("interval",       "n_intervals"),
)
def update_tracker(search, status, area, phase, page, n_intervals):
    """Render the filtered, paginated trial table."""
    df = store.get_trials()

    if df.empty:
        msg = html.Div("No data yet. Data is being fetched...",
                       style={"color": MUTED, "textAlign": "center", "padding": "40px"})
        return msg, ""

    mask = pd.Series([True] * len(df), index=df.index)

    if search:
        q = search.lower()
        mask &= (
            df.get("title",   pd.Series(dtype=str)).fillna("").str.lower().str.contains(q, regex=False)
            | df.get("sponsor", pd.Series(dtype=str)).fillna("").str.lower().str.contains(q, regex=False)
            | df.get("nct_id",  pd.Series(dtype=str)).fillna("").str.lower().str.contains(q, regex=False)
        )

    if status and status != "All":
        mask &= df.get("status", pd.Series(dtype=str)) == status
    if area and area != "All":
        mask &= df.get("disease_area", pd.Series(dtype=str)) == area
    if phase and phase != "All":
        mask &= df.get("phase", pd.Series(dtype=str)) == phase

    filtered = df[mask].reset_index(drop=True)
    total    = len(filtered)
    page     = page or 0
    n_pages  = max(1, math.ceil(total / PAGE_SIZE))
    page     = min(page, n_pages - 1)

    start = page * PAGE_SIZE
    end   = start + PAGE_SIZE
    chunk = filtered.iloc[start:end]

    info_txt = (
        f"Showing {start + 1}-{min(end, total)} of {total:,} trials  |  "
        f"Page {page + 1} of {n_pages}"
    )

    th_style = {
        "padding":      "10px 14px",
        "textAlign":    "left",
        "fontSize":     "0.75rem",
        "fontWeight":   "600",
        "color":        MUTED,
        "borderBottom": "1px solid " + BORDER,
        "whiteSpace":   "nowrap",
        "background":   "rgba(124,58,237,0.1)",
    }
    td_style = {
        "padding":       "9px 14px",
        "fontSize":      "0.78rem",
        "color":         TEXT,
        "borderBottom":  "1px solid rgba(255,255,255,0.04)",
        "verticalAlign": "top",
    }

    header_row = html.Tr([
        html.Th("NCT ID",       style=th_style),
        html.Th("Title",        style={**th_style, "minWidth": "220px"}),
        html.Th("Phase",        style=th_style),
        html.Th("Status",       style=th_style),
        html.Th("Disease Area", style=th_style),
        html.Th("Sponsor",      style={**th_style, "maxWidth": "180px"}),
        html.Th("Countries",    style=th_style),
        html.Th("Start Date",   style=th_style),
    ])

    body_rows = []
    for _, row in chunk.iterrows():
        nct_id  = row.get("nct_id")  or ""
        title   = row.get("title")   or ""
        rphase  = _phase_label(row.get("phase") or "NA")
        rstatus = row.get("status")  or ""
        rarea   = row.get("disease_area") or ""
        sponsor = (row.get("sponsor") or "")[:60]
        clist   = row.get("countries") or []
        cstr    = (", ".join(clist[:3]) + (" ..." if len(clist) > 3 else "")
                   if isinstance(clist, list) else str(clist))
        start_d = row.get("start_date") or ""

        nct_link = (html.A(nct_id,
                           href=f"https://clinicaltrials.gov/study/{nct_id}",
                           target="_blank",
                           style={"color": ACCENT, "textDecoration": "none", "fontWeight": "600"})
                    if nct_id else "")

        body_rows.append(html.Tr([
            html.Td(nct_link,                                         style=td_style),
            html.Td(title[:120] + ("..." if len(title) > 120 else ""),
                    style={**td_style, "maxWidth": "280px"}),
            html.Td(rphase,                                           style=td_style),
            html.Td(_status_badge(rstatus),                           style=td_style),
            html.Td(rarea,                                            style=td_style),
            html.Td(sponsor,                                          style={**td_style, "maxWidth": "180px"}),
            html.Td(cstr,                                             style=td_style),
            html.Td(start_d,                                          style=td_style),
        ]))

    table = html.Table(
        [html.Thead(header_row), html.Tbody(body_rows)],
        style={
            "width":          "100%",
            "borderCollapse": "collapse",
            "background":     CARD_BG,
            "borderRadius":   "10px",
            "overflow":       "hidden",
            "border":         "1px solid " + BORDER,
        },
    )
    return html.Div(table, style={"overflowX": "auto", "borderRadius": "10px"}), info_txt


# Entry point
if __name__ == "__main__":
    print("Clinical Trial Intelligence Dashboard  ->  http://localhost:8051")
    app.run(debug=False, port=int(os.environ.get("PORT", 8051)), host="0.0.0.0")

