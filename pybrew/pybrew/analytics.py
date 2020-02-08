
from .fun import *
from .io import secret_io

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
