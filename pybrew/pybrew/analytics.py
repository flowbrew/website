
from .fun import *

import os
import pandas as pd
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import json

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor


def google_analytics_io():
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(
            secret_io('GOOGLE_ANALYTICS').replace("'", '"')
        )
    )
    return build('analyticsreporting', 'v4', credentials=credentials)


def google_analytics_view_id():
    return '203381219'


def to_dataframe(data):
    for report in data.get('reports', []):
        columnHeader = report.get('columnHeader', {})
        dimensionHeaders = columnHeader.get('dimensions', [])
        metricHeaders = [i.get('name', {}) for i in columnHeader.get(
            'metricHeader', {}).get('metricHeaderEntries', [])]
        finalRows = []
    for row in report.get('data', {}).get('rows', []):
        dimensions = row.get('dimensions', [])
        metrics = row.get('metrics', [])[0].get('values', {})
        rowObject = {}

        for header, dimension in zip(dimensionHeaders, dimensions):
            rowObject[header] = dimension

        for metricHeader, metric in zip(metricHeaders, metrics):
            rowObject[metricHeader] = metric

        finalRows.append(rowObject)

    dataFrameFormat = pd.DataFrame(finalRows)
    return dataFrameFormat


def execute_notebook_io(in_notebook, out_html):
    paper_folder, _ = os.path.split(out_html)
    os.makedirs(paper_folder, exist_ok=True)

    with open(in_notebook, 'r') as notebook_file:
        notebook = nbformat.reads(
            notebook_file.read(),
            as_version=4
        )

        ep = ExecutePreprocessor(
            timeout=600,
            kernel_name='python3',
            allow_errors=True
        )
        ep.preprocess(notebook, {'metadata': {'path': './'}})

        html_exporter = HTMLExporter()
        (body, _) = html_exporter.from_notebook_node(notebook)

        with open(out_html, 'w') as html:
            html.write(body)
            return notebook


def publish_paper_io(paper_name, sha, **kwargs):
    with tmp() as tp:
        html = os.path.join(tp, f'{paper_name}.html')

        notebook = execute_notebook_io(
            os.path.join('./papers', f'{paper_name}.ipynb'),
            html
        )

        key = f'papers/{sha}/{paper_name}.html'
        upload_to_s3_io(html, 'flowbrew', key)
        publish_url = f'https://flowbrew.s3-eu-west-1.amazonaws.com/{key}'

        for cell in notebook['cells']:
            for output in cell['outputs']:
                assert 'error' not in output['output_type'], \
                    f'There was an error during paper "{publish_url}" execution. {output.get("ename")}: {output.get("evalue")}'

        print(f'Paper were published to "{publish_url}"')


def on_pre_split_test_analysis_io(**kwargs):
    publish_paper_io(paper_name='test', **kwargs)


def on_split_test_io(**kwargs):
    publish_paper_io(paper_name='split_test_default_kpi', **kwargs)
