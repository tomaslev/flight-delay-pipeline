"""
app.py — DST Airlines Dashboard v3
Professional aviation dark theme · Navbar + Sidebar + Footer · OOP
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from data import get_flights_df, get_summary_stats, get_live_flights, api_healthy, AIRLINES, AIRPORTS
from charts import ChartFactory

# ── Palette (matches charts.py) ───────────────────────────────────────────
BG       = "#0a0e1a"
CARD     = "#0f1523"
SURFACE  = "#161d2e"
BORDER   = "#1e2a3a"
CYAN     = "#00d4ff"
BLUE     = "#4a9eff"
PURPLE   = "#8b5cf6"
GREEN    = "#10b981"
AMBER    = "#f59e0b"
TEXT     = "#f1f5f9"
MUTED    = "#64748b"
SIDEBAR_W = "220px"

CARD_STYLE = {
    "backgroundColor": CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "12px",
    "padding": "20px",
}

DD_STYLE = {
    "backgroundColor": SURFACE,
    "color": TEXT,
    "border": f"1px solid {BORDER}",
    "borderRadius": "8px",
    "fontSize": "13px",
}


# ═══════════════════════════════════════════════════════════════════════════
class LayoutBuilder:

    @staticmethod
    def navbar() -> html.Div:
        return html.Div([
            html.Div([
                # Logo + title
                html.Div([
                    html.Div("✈", style={
                        "fontSize": "22px", "color": CYAN,
                        "marginRight": "12px", "flexShrink": "0",
                    }),
                    html.Div([
                        html.Span("DST Airlines", style={
                            "fontSize": "17px", "fontWeight": "700",
                            "color": TEXT, "letterSpacing": "0.3px",
                            "whiteSpace": "nowrap",
                        }),
                        html.Span(" · Flight Delay Analytics", style={
                            "fontSize": "12px", "color": MUTED,
                            "marginLeft": "8px", "whiteSpace": "nowrap",
                        }),
                    ]),
                ], style={"display": "flex", "alignItems": "center"}),

                # Right side badges
                html.Div([
                    html.Div(id="api-status-badge"),
                    html.Div("DATA ENGINEERING", style={
                        "fontSize": "10px", "fontWeight": "700",
                        "color": PURPLE, "letterSpacing": "1.5px",
                        "border": f"1px solid {PURPLE}",
                        "borderRadius": "20px", "padding": "3px 10px",
                        "marginLeft": "10px",
                    }),
                ], style={"display": "flex", "alignItems": "center"}),
            ], style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "padding": "0 24px",
                "height": "56px",
            }),
        ], style={
            "backgroundColor": CARD,
            "borderBottom": f"1px solid {BORDER}",
            "position": "sticky", "top": "0", "zIndex": "1000",
        })

    @staticmethod
    def sidebar() -> html.Div:
        nav_items = [
            ("▣", "Overview",    "overview"),
            ("✈", "Airlines",   "airlines"),
            ("⬡", "Routes",     "routes"),
            ("▲", "Trends",     "trends"),
            ("◈", "Prediction", "predict"),
        ]

        links = []
        for icon, label, pid in nav_items:
            links.append(
                html.Div(id=f"nav-{pid}", children=[
                    html.Span(icon, style={
                        "width": "20px", "display": "inline-block",
                        "textAlign": "center", "fontSize": "14px",
                        "marginRight": "10px", "color": CYAN,
                        "flexShrink": "0",
                    }),
                    html.Span(label, style={
                        "fontSize": "13px", "whiteSpace": "nowrap",
                        "fontWeight": "500",
                    }),
                ], style={
                    "display": "flex", "alignItems": "center",
                    "padding": "9px 14px", "borderRadius": "8px",
                    "cursor": "pointer", "color": MUTED,
                    "transition": "all 0.15s", "marginBottom": "2px",
                }, className="nav-item"),
            )

        # Airline dropdown options
        airline_opts = (
            [{"label": "All Airlines", "value": "ALL"}] +
            [{"label": a, "value": a} for a in sorted(AIRLINES)]
        )

        # Origin filter options
        origin_opts = (
            [{"label": "All Origins", "value": "ALL"}] +
            [{"label": f"{k} — {v}", "value": k} for k, v in sorted(AIRPORTS.items())]
        )

        return html.Div([
            # Section: Navigation
            html.Div("NAVIGATION", style={
                "fontSize": "9px", "fontWeight": "700", "color": MUTED,
                "letterSpacing": "2px", "padding": "20px 14px 8px",
            }),
            *links,

            html.Div(style={"height": "1px", "backgroundColor": BORDER, "margin": "14px 14px"}),

            # Section: Filters
            html.Div("FILTERS", style={
                "fontSize": "9px", "fontWeight": "700", "color": MUTED,
                "letterSpacing": "2px", "padding": "0 14px 10px",
            }),

            # Airline dropdown
            html.Div([
                html.Div("Airline", style={"color": MUTED, "fontSize": "11px",
                                           "marginBottom": "5px", "fontWeight": "500"}),
                dcc.Dropdown(
                    id="filter-airline", options=airline_opts,
                    value="ALL", clearable=False,
                    style=DD_STYLE, className="dst-dropdown",
                ),
            ], style={"padding": "0 10px", "marginBottom": "14px"}),

            # Origin dropdown
            html.Div([
                html.Div("Origin Airport", style={"color": MUTED, "fontSize": "11px",
                                                   "marginBottom": "5px", "fontWeight": "500"}),
                dcc.Dropdown(
                    id="filter-origin", options=origin_opts,
                    value="ALL", clearable=False,
                    style=DD_STYLE, className="dst-dropdown",
                ),
            ], style={"padding": "0 10px", "marginBottom": "14px"}),

            # Month range
            html.Div([
                html.Div("Month Range", style={"color": MUTED, "fontSize": "11px",
                                                "marginBottom": "8px", "fontWeight": "500"}),
                dcc.RangeSlider(
                    id="filter-month", min=1, max=12, step=1,
                    value=[1, 12],
                    marks={1:"Jan", 3:"Mar", 6:"Jun", 9:"Sep", 12:"Dec"},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], style={"padding": "0 10px", "marginBottom": "14px"}),

            # Delayed only toggle
            html.Div([
                html.Div("Show Only Delayed", style={"color": MUTED, "fontSize": "11px",
                                                      "marginBottom": "5px", "fontWeight": "500"}),
                dcc.RadioItems(
                    id="filter-delayed",
                    options=[
                        {"label": "  All Flights", "value": "all"},
                        {"label": "  Delayed Only", "value": "delayed"},
                    ],
                    value="all",
                    style={"color": MUTED, "fontSize": "12px"},
                    labelStyle={"display": "block", "marginBottom": "4px"},
                ),
            ], style={"padding": "0 10px", "marginBottom": "14px"}),

        ], style={
            "width": SIDEBAR_W, "minWidth": SIDEBAR_W,
            "backgroundColor": CARD,
            "borderRight": f"1px solid {BORDER}",
            "height": "calc(100vh - 56px)",
            "position": "sticky", "top": "56px",
            "overflowY": "auto", "overflowX": "hidden",
        })

    @staticmethod
    def kpi_card(label: str, value: str, sub: str, color: str, icon: str) -> html.Div:
        return html.Div([
            html.Div([
                html.Span(icon, style={"fontSize": "18px", "color": color}),
                html.Div(sub, style={"fontSize": "10px", "color": MUTED,
                                     "marginLeft": "auto", "fontWeight": "500",
                                     "letterSpacing": "0.5px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
            html.Div(value, style={
                "fontSize": "26px", "fontWeight": "700",
                "color": color, "lineHeight": "1", "letterSpacing": "-0.5px",
            }),
            html.Div(label, style={
                "fontSize": "12px", "color": MUTED, "marginTop": "5px",
            }),
        ], style={
            **CARD_STYLE,
            "flex": "1", "minWidth": "130px",
            "borderTop": f"2px solid {color}",
        })

    @staticmethod
    def footer() -> html.Div:
        return html.Div([
            html.Span("DST Airlines · Flight Delay Analytics",
                      style={"color": MUTED, "fontSize": "11px"}),
            html.Span(" · ", style={"color": BORDER}),
            html.Span("Data Engineering · DataScientest · Feb 2026",
                      style={"color": MUTED, "fontSize": "11px"}),
            html.Span(" · ", style={"color": BORDER}),
            html.Span("PostgreSQL · MongoDB · Neo4j · FastAPI",
                      style={"color": MUTED, "fontSize": "11px"}),
        ], style={
            "backgroundColor": CARD, "borderTop": f"1px solid {BORDER}",
            "textAlign": "center", "padding": "12px 24px",
        })

    def page_overview(self) -> html.Div:
        graph_cfg = {"displayModeBar": False}
        return html.Div([
            # KPI row
            html.Div(id="kpi-row", style={
                "display": "flex", "gap": "12px",
                "flexWrap": "wrap", "marginBottom": "16px",
            }),
            # Row 1: monthly trend + DOW
            html.Div([
                html.Div([dcc.Graph(id="chart-monthly", config=graph_cfg,
                                    style={"height": "300px"})],
                         style={**CARD_STYLE, "flex": "3"}),
                html.Div([dcc.Graph(id="chart-dow", config=graph_cfg,
                                    style={"height": "300px"})],
                         style={**CARD_STYLE, "flex": "2"}),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
            # Row 2: histogram + top routes
            html.Div([
                html.Div([dcc.Graph(id="chart-histogram", config=graph_cfg,
                                    style={"height": "280px"})],
                         style={**CARD_STYLE, "flex": "1"}),
                html.Div([dcc.Graph(id="chart-top-routes", config=graph_cfg,
                                    style={"height": "280px"})],
                         style={**CARD_STYLE, "flex": "1"}),
            ], style={"display": "flex", "gap": "12px"}),
        ])

    def page_airlines(self) -> html.Div:
        graph_cfg = {"displayModeBar": False}
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(id="chart-airline-bar", config=graph_cfg,
                                    style={"height": "340px"})],
                         style={**CARD_STYLE, "flex": "1"}),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
            html.Div([
                html.Div([dcc.Graph(id="chart-cause-stack", config=graph_cfg,
                                    style={"height": "320px"})],
                         style={**CARD_STYLE, "flex": "1"}),
            ], style={"display": "flex", "gap": "12px"}),
        ])

    def page_routes(self) -> html.Div:
        graph_cfg = {"displayModeBar": False}
        return html.Div([
            html.Div([
                dcc.Graph(id="chart-heatmap", config=graph_cfg, style={"height": "480px"})
            ], style={**CARD_STYLE, "marginBottom": "12px"}),
            html.Div([
                dcc.Graph(id="chart-bubble", config=graph_cfg, style={"height": "420px"})
            ], style=CARD_STYLE),
        ])

    def page_trends(self) -> html.Div:
        graph_cfg = {"displayModeBar": False}
        return html.Div([
            html.Div([dcc.Graph(id="chart-monthly-2", config=graph_cfg,
                                style={"height": "360px"})],
                     style={**CARD_STYLE, "marginBottom": "12px"}),
            html.Div([dcc.Graph(id="chart-top-routes-2", config=graph_cfg,
                                style={"height": "320px"})],
                     style=CARD_STYLE),
        ])

    def page_predict(self) -> html.Div:
        def field(label, placeholder, fid, typ="text"):
            return html.Div([
                html.Div(label, style={"color": MUTED, "fontSize": "11px",
                                       "marginBottom": "5px", "fontWeight": "500"}),
                dcc.Input(
                    id=fid, type=typ, placeholder=placeholder,
                    debounce=True, style={
                        "width": "100%", "backgroundColor": SURFACE,
                        "color": TEXT, "border": f"1px solid {BORDER}",
                        "borderRadius": "8px", "padding": "8px 12px",
                        "fontSize": "13px", "outline": "none",
                        "boxSizing": "border-box",
                    }),
            ], style={"marginBottom": "12px"})

        return html.Div([
            html.Div([
                html.Div("Delay Prediction", style={
                    "fontSize": "15px", "fontWeight": "700",
                    "color": TEXT, "marginBottom": "4px",
                }),
                html.Div("Enter flight & weather details to predict delay probability",
                         style={"fontSize": "12px", "color": MUTED, "marginBottom": "20px"}),

                html.Div([
                    html.Div([
                        field("Origin Airport (IATA)", "e.g. JFK", "pred-origin"),
                        field("Destination (IATA)",    "e.g. LAX", "pred-dest"),
                        field("Airline",               "e.g. Delta Air Lines", "pred-airline"),
                        field("Distance (miles)",      "e.g. 2475", "pred-distance", "number"),
                    ], style={"flex": "1"}),
                    html.Div([
                        field("Temp Origin (°C)",      "e.g. 12", "pred-temp-o", "number"),
                        field("Wind Speed (km/h)",     "e.g. 18", "pred-wind-o", "number"),
                        field("Precipitation (mm)",    "e.g. 0",  "pred-precip",  "number"),
                        field("Cloud Cover (oktas)",   "e.g. 4",  "pred-cloud",   "number"),
                    ], style={"flex": "1"}),
                ], style={"display": "flex", "gap": "24px"}),

                html.Button("Predict Delay →", id="btn-predict", n_clicks=0, style={
                    "backgroundColor": CYAN, "color": BG,
                    "border": "none", "borderRadius": "8px",
                    "padding": "10px 28px", "fontSize": "13px",
                    "fontWeight": "700", "cursor": "pointer",
                    "marginTop": "8px", "letterSpacing": "0.3px",
                }),
                html.Div(id="predict-result", style={"marginTop": "20px"}),
            ], style={**CARD_STYLE, "maxWidth": "780px"}),
        ])


# ═══════════════════════════════════════════════════════════════════════════
class AirlinesDashboard:

    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap",
            ],
            suppress_callback_exceptions=True,
            title="DST Airlines · Analytics",
        )
        self.charts  = ChartFactory()
        self.layout  = LayoutBuilder()
        self._build_layout()
        self._register_callbacks()

    def _build_layout(self):
        self.app.layout = html.Div([
            self.layout.navbar(),
            html.Div([
                self.layout.sidebar(),
                html.Div([
                    dcc.Store(id="current-page", data="overview"),
                    dcc.Interval(id="api-check", interval=30000, n_intervals=0),
                    html.Div(id="page-header", style={
                        "fontSize": "20px", "fontWeight": "700",
                        "color": TEXT, "marginBottom": "16px",
                        "letterSpacing": "-0.3px",
                    }),
                    html.Div(id="page-content"),
                ], style={
                    "flex": "1", "padding": "20px 24px",
                    "overflowY": "auto", "backgroundColor": BG,
                    "minHeight": "calc(100vh - 56px)",
                }),
            ], style={"display": "flex"}),
            self.layout.footer(),
        ], style={"fontFamily": "'DM Sans', sans-serif", "backgroundColor": BG})

    def _register_callbacks(self):
        app    = self.app
        charts = self.charts
        layout = self.layout

        # ── API status badge ─────────────────────────────────────────────
        @app.callback(Output("api-status-badge", "children"),
                      Input("api-check", "n_intervals"))
        def update_api_badge(_):
            ok = api_healthy()
            color = GREEN if ok else AMBER
            label = "● API LIVE" if ok else "● MOCK DATA"
            return html.Div(label, style={
                "fontSize": "10px", "fontWeight": "700", "color": color,
                "border": f"1px solid {color}", "borderRadius": "20px",
                "padding": "3px 10px", "letterSpacing": "1px",
            })

        # ── Sidebar nav ──────────────────────────────────────────────────
        app.clientside_callback(
            """
            function(c1,c2,c3,c4,c5, current) {
                const t = dash_clientside.callback_context.triggered;
                if (!t || t.length === 0) return current;
                const id = t[0].prop_id.split('.')[0];
                return id.replace('nav-', '');
            }
            """,
            Output("current-page", "data"),
            [Input(f"nav-{p}", "n_clicks") for p in
             ["overview","airlines","routes","trends","predict"]],
            State("current-page", "data"),
            prevent_initial_call=True,
        )

        # ── Page render ──────────────────────────────────────────────────
        @app.callback(
            Output("page-content", "children"),
            Output("page-header", "children"),
            Input("current-page", "data"),
            Input("filter-airline", "value"),
            Input("filter-origin", "value"),
            Input("filter-month", "value"),
            Input("filter-delayed", "value"),
        )
        def render_page(page, airline, origin, months, delayed_filter):
            titles = {
                "overview": "Overview",
                "airlines": "Airline Performance",
                "routes":   "Route Analysis",
                "trends":   "Monthly Trends",
                "predict":  "Delay Prediction",
            }
            pages = {
                "overview": layout.page_overview,
                "airlines": layout.page_airlines,
                "routes":   layout.page_routes,
                "trends":   layout.page_trends,
                "predict":  layout.page_predict,
            }
            content = pages.get(page, layout.page_overview)()
            return content, titles.get(page, "Dashboard")

        # ── KPI cards ────────────────────────────────────────────────────
        @app.callback(
            Output("kpi-row", "children"),
            Input("filter-airline", "value"),
            Input("filter-origin", "value"),
            Input("filter-month", "value"),
            Input("filter-delayed", "value"),
        )
        def update_kpis(airline, origin, months, delayed_filter):
            df = _filtered(airline, origin, months, delayed_filter)
            total   = len(df)
            delayed = int(df["Delayed"].sum()) if "Delayed" in df.columns else 0
            rate    = round(df["Delayed"].mean() * 100, 1) if total and "Delayed" in df.columns else 0
            avg_del = round(df[df["DepDelay"] > 0]["DepDelay"].mean(), 1) if total else 0
            routes  = df.groupby(["Origin","Dest"]).ngroups if "Origin" in df.columns else 0
            return [
                layout.kpi_card("Total Flights",   f"{total:,}",      "FLIGHTS", TEXT,   "▣"),
                layout.kpi_card("Delayed Flights",  f"{delayed:,}",    "DELAYED", AMBER,  "⏱"),
                layout.kpi_card("Delay Rate",       f"{rate}%",        "RATE",    AMBER,  "↑"),
                layout.kpi_card("Avg Delay",        f"{avg_del} min",  "AVG",     CYAN,   "◷"),
                layout.kpi_card("Airlines",
                                str(df["Operating_Airline"].nunique() if "Operating_Airline" in df.columns else 0),
                                "CARRIERS", GREEN, "✈"),
                layout.kpi_card("Routes", str(routes), "O-D PAIRS", PURPLE, "⬡"),
            ]

        # ── Shared filter helper ─────────────────────────────────────────
        def _filtered(airline, origin, months, delayed_filter):
            df = get_flights_df()
            if airline and airline != "ALL" and "Operating_Airline" in df.columns:
                df = df[df["Operating_Airline"] == airline]
            if origin and origin != "ALL" and "Origin" in df.columns:
                df = df[df["Origin"] == origin]
            if "Month" in df.columns:
                df = df[df["Month"].between(months[0], months[1])]
            if delayed_filter == "delayed" and "Delayed" in df.columns:
                df = df[df["Delayed"] == 1]
            return df

        # ── Overview charts ───────────────────────────────────────────────
        ins = [Input("filter-airline","value"), Input("filter-origin","value"),
               Input("filter-month","value"),   Input("filter-delayed","value")]

        @app.callback(Output("chart-monthly","figure"), *ins)
        def c_monthly(a,o,m,d): return charts.monthly_trend(_filtered(a,o,m,d))

        @app.callback(Output("chart-dow","figure"), *ins)
        def c_dow(a,o,m,d): return charts.dow_delay(_filtered(a,o,m,d))

        @app.callback(Output("chart-histogram","figure"), *ins)
        def c_hist(a,o,m,d): return charts.delay_histogram(_filtered(a,o,m,d))

        @app.callback(Output("chart-top-routes","figure"), *ins)
        def c_top(a,o,m,d): return charts.top_routes(_filtered(a,o,m,d))

        # ── Airlines charts ───────────────────────────────────────────────
        @app.callback(Output("chart-airline-bar","figure"), *ins)
        def c_airline(a,o,m,d): return charts.airline_delay_bar(_filtered(a,o,m,d))

        @app.callback(Output("chart-cause-stack","figure"), *ins)
        def c_cause(a,o,m,d): return charts.delay_cause_stack(_filtered(a,o,m,d))

        # ── Routes charts ─────────────────────────────────────────────────
        @app.callback(Output("chart-heatmap","figure"), *ins)
        def c_heat(a,o,m,d): return charts.route_heatmap_top(_filtered(a,o,m,d))

        @app.callback(Output("chart-bubble","figure"), *ins)
        def c_bubble(a,o,m,d): return charts.top_routes_bubble(_filtered(a,o,m,d))

        # ── Trends charts ─────────────────────────────────────────────────
        @app.callback(Output("chart-monthly-2","figure"), *ins)
        def c_monthly2(a,o,m,d): return charts.monthly_trend(_filtered(a,o,m,d))

        @app.callback(Output("chart-top-routes-2","figure"), *ins)
        def c_top2(a,o,m,d): return charts.top_routes(_filtered(a,o,m,d))

        # ── Prediction ────────────────────────────────────────────────────
        @app.callback(
            Output("predict-result","children"),
            Input("btn-predict","n_clicks"),
            State("pred-origin","value"), State("pred-dest","value"),
            State("pred-distance","value"), State("pred-airline","value"),
            prevent_initial_call=True,
        )
        def do_predict(n, origin, dest, distance, airline):
            import random
            if not all([origin, dest, distance]):
                return html.Div("⚠  Please fill in all required fields.",
                                style={"color": AMBER, "fontSize": "13px"})
            prob    = round(random.uniform(0.15, 0.85), 2)
            delayed = prob > 0.5
            color   = AMBER if delayed else GREEN
            label   = "LIKELY DELAYED" if delayed else "ON TIME"
            pct     = int(prob * 100)
            return html.Div([
                html.Div([
                    html.Span(label, style={
                        "fontSize": "20px", "fontWeight": "700",
                        "color": color, "letterSpacing": "0.5px",
                    }),
                    html.Span(f"  {pct}% probability",
                              style={"fontSize": "13px", "color": MUTED, "marginLeft": "8px"}),
                ], style={"marginBottom": "10px"}),
                # Probability bar
                html.Div([
                    html.Div(style={
                        "width": f"{pct}%", "height": "4px",
                        "backgroundColor": color, "borderRadius": "2px",
                        "transition": "width 0.5s",
                    }),
                ], style={
                    "width": "100%", "height": "4px",
                    "backgroundColor": BORDER, "borderRadius": "2px",
                    "marginBottom": "12px",
                }),
                html.Div(
                    f"Route: {(origin or '').upper()} → {(dest or '').upper()}"
                    + (f"  ·  {airline}" if airline else "")
                    + f"  ·  {distance} mi",
                    style={"fontSize": "12px", "color": MUTED}
                ),
                html.Div("⚡ Connect logistic_regression.pkl to FastAPI for live ML predictions.",
                         style={"fontSize": "11px", "color": MUTED,
                                "marginTop": "12px", "paddingTop": "12px",
                                "borderTop": f"1px solid {BORDER}"}),
            ], style={**CARD_STYLE, "borderTop": f"2px solid {color}"})

    def run(self, debug=False, port=8050):
        self.app.run(debug=debug, host="0.0.0.0", port=port)


if __name__ == "__main__":
    AirlinesDashboard().run(debug=False, port=8050)
