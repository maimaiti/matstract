import dash_html_components as html
import dash_core_components as dcc


def serve_layout(db):
    """Generates the layout dynamically on every refresh"""

    return html.Div([serve_analogy(), serve_similarity()])


def serve_similarity():
    return html.Div([
                html.Div([
                    html.Span("Similarity", style={"fontWeight": "bold"}),
                    html.Br(),
                    dcc.Input(id='similar_words_input',
                              placeholder='e.g. LiMn2O4, anode, ...',
                              type='text'),
                    html.Button("Is similar to", id="similar_words_button", className="butson-primary"),
                    ]),
                html.Div('', id='similar_words_container')])


def serve_analogy():
    return html.Div([
                html.Span("Analogy", style={"fontWeight": "bold"}),
                html.Br(),
                dcc.Input(id='analogy_neg_1',
                          placeholder='e.g. LiCoO2, Co',
                          type='text'),
                html.Span(" is to "),
                dcc.Input(id='analogy_pos_1',
                          placeholder='e.g. cathode, CoO',
                          type='text'),
                html.Span(" as "),
                dcc.Input(id='analogy_pos_2',
                          placeholder='e.g. graphite, Al',
                          type='text'),
                html.Span(" is to "),
                html.Span("", id="analogy_container", style={"fontWeight": "bold"}),
                html.Button("?", id="analogy_run", className="buton-primary")])
