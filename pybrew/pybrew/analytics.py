
from .fun import *

import os
import pandas as pd
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import json


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


def publish_paper_io(
    paper_name,
    event_name,
    organization,
    deployment_repo,
    branch,
    **kwargs
):
    with github_io(
        username=secret_io('GITHUB_WEBSITE_USERNAME'),
        token=secret_io('GITHUB_WEBSITE_TOKEN'),
        repo_name=deployment_repo,
        branch='master',
        message=event_name + ' report',
        organization=organization
    ) as repo_path:
        paper_folder = os.path.join(
            repo_path,
            branch_to_prefix(branch),
            'papers',
        )
        os.makedirs(paper_folder, exist_ok=True)
        run_io(
            f'jupyter nbconvert \
                --execute \
                --output-dir {paper_folder} \
                ./papers/{paper_name}.ipynb'
        )


def on_pre_split_test_analysis(**kwargs):
    publish_paper_io(paper_name='test', **kwargs)


def on_split_test_io(**kwargs):
    pass
