from datetime import datetime, timedelta

from src.model.models import Prediction, InferenceServerORM
import plotly.graph_objs as go


def created_vs_predicted_times_converter(predictions: list[Prediction]):
    figure = {
        'x': [],
        'y': [],
        'layout': go.Layout(
            title='Inference time',
            xaxis=dict(
                title='Time',
            ),
            yaxis=dict(
                title='Clean inference time',
            ),
            template='plotly_dark'
        )
    }

    for i, prediction in enumerate(predictions):
        figure['x'].append(prediction.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        figure['y'].append((prediction.predicted_at - prediction.created_at).total_seconds())

    return go.Figure(data=go.Scatter(x=figure['x'], y=figure['y']), layout=figure['layout'])


def server_upd_over_time_converter(
        servers: list[InferenceServerORM],
        start_of_comparison: datetime,
        end_of_comparison: datetime,
        item_on_compare: str
):
    figure = {
        'x': [],
        'y': [],
        'layout': go.Layout(
            title='Servers in state',
            xaxis=dict(
                title='Time',
            ),
            yaxis=dict(
                title='Count',
            ),
            template='plotly_dark'
        )
    }
    last_hours = [start_of_comparison]
    for i in range(int((start_of_comparison - end_of_comparison).total_seconds() // 3600)):
        diff = start_of_comparison - timedelta(hours=i)
        diff = diff.astimezone(start_of_comparison.tzinfo)
        last_hours.append(diff)
    figure['x'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in last_hours[:-1]]
    figure['y'] = [0 for _ in range(len(last_hours) - 1)]
    for idx, x in enumerate(last_hours[:-1]):
        for server in servers[::-1]:
            on_compare = getattr(server, item_on_compare)
            on_compare = on_compare.astimezone(start_of_comparison.tzinfo)
            if on_compare >= x:
                figure['y'][idx] += 1
    return go.Figure(data=go.Scatter(x=figure['x'], y=figure['y']), layout=figure['layout'])


def input_vs_output_converter(predictions: list[Prediction]):
    figure = {
        'x': [],
        'y': [],
        'layout': go.Layout(
            title='Predictions state',
            xaxis=dict(
                title='Result',
            ),
            yaxis=dict(
                title='Count',
            ),
            template='plotly_dark'
        )
    }
    unique_results = dict()

    for prediction in predictions:
        res = prediction.output_data.get('prediction')
        if res:
            res = res[0]
        if res not in unique_results:
            unique_results[res] = 1
        else:
            unique_results[res] += 1
    for r, cnt in unique_results.items():
        figure['x'].append(str(r))
        figure['y'].append(cnt)
    return go.Figure(data=go.Bar(x=figure['x'], y=figure['y']), layout=figure['layout'])


def avg_server_cost(server_mappings: list[dict]):
    figure = {
        'x': [i['created_at'].strftime("%Y-%m-%d") for i in server_mappings],
        'y': [i['avg'] for i in server_mappings],
        'layout': go.Layout(
            title='Servers',
            xaxis=dict(
                title='Created at',
                tickformat="%Y-%m-%d"
            ),
            yaxis=dict(
                title='Avg cost ($)',
            ),
            template='plotly_dark'
        )
    }
    return go.Figure(data=go.Bar(x=figure['x'], y=figure['y']), layout=figure['layout'])
