import re
from datetime import timedelta

import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from sqlalchemy.sql.functions import count, func
from sqlmodel import select, desc

from src.core.container import Container
from src.dashboards.utils import created_vs_predicted_times_converter, server_upd_over_time_converter, \
    input_vs_output_converter, avg_server_cost
from src.model.models import User, Prediction, InferenceServerORM, ClassificationModelORM
from src.util.date import get_now

# Assuming you have a session for SQLModel

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.themes.DARKLY]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

database = Container.db()

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.H2(f"Model: ", id='model-head'),
    dbc.Container([
        html.H2("Total servers alive: 0", id="total-servers-alive"),
        dbc.Row([
            dbc.Row([
                dbc.Col([
                    html.H5(
                        "Number of Inference Server status changes over time",
                        className='pad-elem'
                    ),
                    dcc.Graph(id='server-creations-over-time', className='pad-elem plot'),
                    dcc.Dropdown(
                        id='server-state-dd',
                        className='pad-elem select-dark',
                        options=[
                            {
                                'label': InferenceServerORM.ServerState.to_str(InferenceServerORM.ServerState.DEAD),
                                'value': InferenceServerORM.ServerState.DEAD.value
                            },
                            {
                                'label': InferenceServerORM.ServerState.to_str(InferenceServerORM.ServerState.STARTING),
                                'value': InferenceServerORM.ServerState.STARTING.value
                            }
                        ],
                        value=InferenceServerORM.ServerState.DEAD.value
                    ),
                ], className='col-6'),
                dbc.Col([
                    html.H5(
                        "Input and Output Data of Predictions for a Specific User",
                        className='pad-elem'
                    ),
                    dcc.Graph(id='input-vs-output', className='pad-elem'),
                    dcc.Dropdown(
                        id='user-dropdown',
                        className='pad-elem select-dark',
                    ),
                ], className='col-6'),
                dbc.Col([
                    html.H5(
                        "Created and Predicted Times of Predictions for a Specific User",
                        className='pad-elem'
                    ),

                    dcc.Graph(id='created-vs-predicted', className='pad-elem'),
                    dcc.Dropdown(
                        id='user-dropdown-2',
                        className='pad-elem'
                    ),
                ], className='col-6'),
                dbc.Col([
                    html.H5(
                        'Average Inference Server cost',
                        className='pad-elem'
                    ),

                    dcc.Graph(id='average-server-cost', className='pad-elem'),
                    dcc.Dropdown(
                        id='server-state-dd-2',
                        className='pad-elem select-dark',
                        options=[
                            {
                                'label': InferenceServerORM.ServerState.to_str(InferenceServerORM.ServerState.DEAD),
                                'value': InferenceServerORM.ServerState.DEAD.value
                            },
                            {
                                'label': InferenceServerORM.ServerState.to_str(InferenceServerORM.ServerState.STARTING),
                                'value': InferenceServerORM.ServerState.STARTING.value
                            },
                            {
                                'label': InferenceServerORM.ServerState.to_str(InferenceServerORM.ServerState.ALIVE),
                                'value': InferenceServerORM.ServerState.ALIVE.value
                            },
                        ],
                        value=InferenceServerORM.ServerState.ALIVE.value
                    ),
                ])
            ])
        ])
    ], fluid=True, className='dash-bootstrap')
])


@app.callback(
    Output('model-head', 'children'),
    Input('url', 'pathname')
)
def update_model_head(pathname):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    model_query = select(ClassificationModelORM).where(ClassificationModelORM.id == model_id_requested)
    with database.session() as ses:
        model = ses.execute(model_query).scalars().one_or_none()
    return f'Model: {model.name}'


@app.callback(
    Output('total-servers-alive', 'children'),
    Input('url', 'pathname')
)
def total_servers_alive(pathname):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    servers_query = select(count(InferenceServerORM.id)).where(
        InferenceServerORM.linked_model_id == model_id_requested,
        InferenceServerORM.server_state == InferenceServerORM.ServerState.ALIVE.value
    )
    with database.session() as ses:
        cnt = ses.execute(servers_query).scalars().one_or_none()
    return f"Total servers alive: {cnt}"


@app.callback(
    Output('user-dropdown', 'options'),
    Output('user-dropdown-2', 'options'),
    Input('url', 'pathname'),
)
def update_dropdown(pathname):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    users_query = select(User).join(Prediction).join(InferenceServerORM).where(
        InferenceServerORM.linked_model_id == model_id_requested
    )
    with database.session() as ses:
        users = ses.execute(users_query).scalars().unique()
        options = [
            {'label': user.email, 'value': user.id}
            for user in users
        ]
    return [options, options]


@app.callback(
    Output('created-vs-predicted', 'figure'),
    Input('url', 'pathname'),
    Input('user-dropdown-2', 'value'),
)
def update_created_and_predicted_times(pathname, user):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    predictions_query = select(Prediction).join(InferenceServerORM).where(
        InferenceServerORM.linked_model_id == model_id_requested
    ).limit(100).order_by(desc(Prediction.id))
    if user:
        predictions_query = predictions_query.where(Prediction.user_id == user)
    with database.session() as ses:
        predictions = ses.execute(predictions_query).scalars().all()
    figure = created_vs_predicted_times_converter(predictions)
    return figure


@app.callback(
    Output('server-creations-over-time', 'figure'),
    Input('url', 'pathname'),
    Input('server-state-dd', 'value')
)
def update_server_upd_over_time(pathname, state):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    start_of_comparison = get_now()
    end_of_comparison = start_of_comparison - timedelta(hours=24)
    servers_query = select(InferenceServerORM).where(
                InferenceServerORM.linked_model_id == model_id_requested,
    )
    item_on_compare = 'updated_at'
    match state:
        case InferenceServerORM.ServerState.ALIVE.value:
            servers_query = servers_query.where(
                InferenceServerORM.updated_at <= start_of_comparison,
                InferenceServerORM.updated_at >= end_of_comparison,
                InferenceServerORM.server_state == state
            ).order_by(desc(InferenceServerORM.updated_at))
        case InferenceServerORM.ServerState.DEAD.value:
            servers_query = servers_query.where(
                InferenceServerORM.updated_at <= start_of_comparison,
                InferenceServerORM.updated_at >= end_of_comparison,
                InferenceServerORM.server_state == state
            ).order_by(desc(InferenceServerORM.updated_at))
        case InferenceServerORM.ServerState.STARTING.value:
            servers_query = servers_query.where(
                InferenceServerORM.created_at <= start_of_comparison,
                InferenceServerORM.created_at >= end_of_comparison,
            ).order_by(desc(InferenceServerORM.created_at))
            item_on_compare = 'created_at'
    with database.session() as ses:
        servers = ses.execute(servers_query).scalars().all()
    figure = server_upd_over_time_converter(servers, start_of_comparison, end_of_comparison, item_on_compare)
    return figure


@app.callback(
    Output('input-vs-output', 'figure'),
    Input('url', 'pathname'),
    Input('user-dropdown', 'value'),
)
def update_input_vs_output(pathname, user):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    predictions_query = select(Prediction).join(InferenceServerORM).where(
        InferenceServerORM.linked_model_id == model_id_requested
    ).limit(100).order_by(desc(Prediction.id))
    if user:
        predictions_query = predictions_query.where(Prediction.user_id == user)
    with database.session() as ses:
        predictions = ses.execute(predictions_query).scalars().all()
    figure = input_vs_output_converter(predictions)
    return figure


@app.callback(
    Output('average-server-cost', 'figure'),
    Input('url', 'pathname'),
    Input('server-state-dd-2', 'value')
)
def update_average_cost(pathname, state):
    model_id_requested = int(re.search(r'/model/([0-9]+)', pathname).group(1))
    servers_query = select(
        func.date(InferenceServerORM.created_at).label('created_at'),
        func.avg(InferenceServerORM.cost)
    ).where(
        InferenceServerORM.linked_model_id == model_id_requested,
        InferenceServerORM.server_state == state
    ).group_by(func.date(InferenceServerORM.created_at))
    with database.session() as ses:
        servers = ses.execute(servers_query).mappings().all()
    figure = avg_server_cost(servers)
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)
