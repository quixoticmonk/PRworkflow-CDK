#!/usr/bin/env python3

import json

from aws_cdk import core as cdk
from aws_cdk import aws_codecommit as codecommit

from lib.pr_construct import PRConstruct
from lib.lambda_construct import LambdaConstruct

_env_dev = cdk.Environment(account="", region="")
_repo_arn = ""


class DeployStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        _repo = codecommit.Repository.from_repository_arn(repository_arn=_repo_arn)
        _pr_comment_fn = LambdaConstruct(app, "lambdaConstruct", "lambda1")
        _codebuild_results_fn = LambdaConstruct(app, "lambdaConstruct", "lambda2")
        PRConstruct(app, "PRConstruct", _repo, self.account)


app = cdk.App()
with open('./tags.json', 'r') as file:
    tags = json.loads(file.read())

for key, value in tags.items():
    cdk.Tags.of(app).add(key, value)

DeployStack(app, "deployDev", env=_env_dev)

app.synth()
