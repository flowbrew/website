
from .fun import *

import os
import pandas as pd
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime, timedelta

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor


def base_alpha():
    return 0.05


def base_beta():
    return 0.8


def business_cycle():
    return timedelta(days=7)


def parallel_test_groups():
    return 2


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
            for output in cell.get('outputs', []):
                assert 'error' not in output['output_type'], \
                    f'There was an error during paper "{publish_url}" execution. {output.get("ename")}: {output.get("evalue")}'

        print(f'Paper were published to "{publish_url}"')


def ga_simple_segment(filters):
    return {
        'simpleSegment': {
            'orFiltersForSegment': filters
        }
    }


def ga_dynamic_segment(name, filters):
    return {
        'dynamicSegment': {
            'name': name,
            'userSegment': {
                'segmentFilters': [ga_simple_segment(filters)]
            }
        }
    }


def dimension_filter(dimensionName, expressions, operator):
    return {
        'segmentFilterClauses': [
            {
                'dimensionFilter': {
                    'dimensionName': dimensionName,
                    'expressions': expressions,
                    'operator': operator
                },
            },
        ],
    }


def metric_filter(metricName, operator, comparisonValue):
    return {
        'segmentFilterClauses': [
            {
                'metricFilter': {
                    'metricName': metricName,
                    'operator': operator,
                    'comparisonValue': comparisonValue
                },
            },
        ],
    }


def target_audience_filters():
    return [
        dimension_filter(
            dimensionName='ga:country',
            expressions=['Russia'],
            operator='EXACT'
        ),
        dimension_filter(
            dimensionName='ga:sessionCount',
            expressions=['5'],
            operator='NUMERIC_LESS_THAN'
        ),
        metric_filter(
            metricName='ga:sessionDuration',
            operator='GREATER_THAN',
            comparisonValue='15'
        ),
    ]


def ga_target_audience_segment():
    return ga_dynamic_segment(
        "Target Audience",
        target_audience_filters()
    )


def ga_sha_segment(sha):
    return ga_dynamic_segment(
        "Target Audience",
        target_audience_filters() + [
            dimension_filter(
                dimensionName='ga:dimension2',
                expressions=[sha],
                operator='EXACT'
            ),
        ]
    )


@curry
def unique_pageviews_of_segments_io(analytics, start, end, segments):
    res = analytics.reports().batchGet(
        body={
            'reportRequests': [
                {
                    'viewId': google_analytics_view_id(),
                    'dateRanges': [{
                        'startDate': str(start.date()),
                        'endDate': str(end.date())}
                    ],
                    'metrics': [{
                        'expression': 'ga:uniquePageviews'
                    }],
                    'dimensions': [
                        {'name': 'ga:segment'},
                        {'name': 'ga:pagePath'}
                    ],
                    'segments': segments,
                }]
        }
    ).execute()
    df = to_dataframe(res)
    if 'ga:uniquePageviews' not in df.columns:
        return pd.DataFrame({'ga:uniquePageviews': []})

    upv = df.astype({'ga:uniquePageviews': 'int32'})
    upv['ga:pagePath'] = upv['ga:pagePath'].apply(
        lambda x: x.split('?')[0]
    )

    return upv.groupby(['ga:pagePath', 'ga:segment']).sum()


def unique_pageviews_of_target_audience_io(analytics, start, end):
    return unique_pageviews_of_segments_io(
        analytics, start, end,
        [ga_target_audience_segment()]
    )


def unique_pageviews_of_sha_io(analytics, start, end, sha):
    return unique_pageviews_of_segments_io(
        analytics, start, end,
        [ga_sha_segment(sha)]
    )


def ga_segment_stats_io(
    analytics,
    start,
    end,
    segments
):
    upv = unique_pageviews_of_segments_io(
        analytics,
        start,
        end,
        segments,
    )

    n = deep_get(
        ['ga:uniquePageviews', '/', 'Target Audience'],
        upv, 0
    )

    n_conversion = deep_get(
        ['ga:uniquePageviews', '/checkout.html', 'Target Audience'],
        upv, 0
    )

    return {
        'n': n,
        'n_conversion': n_conversion,
        'conversion': 0.0 if n == 0 else n_conversion / n
    }


def on_pre_split_test_analysis_io(branch, **kwargs):
    if branch == master_branch():
        return
    else:
        publish_paper_io(paper_name='pre_split_test_analysis', **kwargs)


def on_split_test_io(branch, **kwargs):
    if branch == master_branch():
        return
    else:
        publish_paper_io(paper_name='split_test', **kwargs)
