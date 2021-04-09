import boto3

codecommit_client = boto3.client('codecommit')


def handler(event, context):
    print(event)
    for item in event['detail']['additional-information']['environment'][
            'environment-variables']:
        if item['name'] == 'pullRequestId': pull_request_id = item['value']
        if item['name'] == 'repositoryName': repository_name = item['value']
        if item['name'] == 'sourceCommit': before_commit_id = item['value']
        if item['name'] == 'destinationCommit': after_commit_id = item['value']

    for phase in event['detail']['additional-information']['phases']:
        if phase.get('phase-status') == 'FAILED':
            content = '''## ❌ Pull request build FAILED
                        Commit ID: afterCommitId
See the [Logs]({0})'''.format(
                event['detail']['additional-information']['logs']['deep-link'])
            break
        else:
            content = '''## ✔️ Pull request build SUCCEEDED
See the [Logs]({0})'''.format(
                event['detail']['additional-information']['logs']['deep-link'])

    codecommit_client.post_comment_for_pull_request(
        pullRequestId=pull_request_id,
        repositoryName=repository_name,
        beforeCommitId=before_commit_id,
        afterCommitId=after_commit_id,
        content=content)
