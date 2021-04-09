from aws_cdk import (
    core,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_events_targets as targets,
    aws_events as events,
    aws_lambda as _lambda
)

from aws_cdk.aws_events import EventField


class PRConstruct(core.Construct):
    def __init__(self, scope: core.Construct, construct_id: str,
                 _repo: codecommit.IRepository, account: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        _repo_dict = dict(self.node.try_get_context("repo"))
        _pr_build_dict = dict(self.node.try_get_context("pr_build"))

        self.account = account

        _pr_build = codebuild.Project(
            self,
            "PR",
            project_name="patientCommunicationPRBuild",
            badge=True,
            source=codebuild.Source.code_commit(repository=_repo),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                compute_type=codebuild.ComputeType.MEDIUM,
                privileged=False),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": [
                            "npm install -g aws-cdk",
                            "git config --global credential.helper '!aws codecommit credential-helper $@'",
                            "git config --global credential.UseHttpPath true",
                            "pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": ["cdk synth"]
                    }
                }
            }))

        _pr_lambda = _lambda.Function.from_function_arn(
            self, "pullRequestFn", function_arn=_pr_build_dict["pr_lambda_arn"])
        _pr_results_lambda = _lambda.Function.from_function_arn(
            self,
            "codebuildResultsPRFn",
            function_arn=_pr_build_dict["pr_build_results_lambda_arn"])

        _pr_event_pattern = events.EventPattern(
            account=[self.account],
            detail={
                "event":
                    ["pullRequestCreated", "pullRequestSourceBranchUpdated"]
            },
            source=["aws.codecommit"],
            resources=[_repo.repository_arn])

        _pr_event_rule = events.Rule(
            self,
            _repo_dict["repo_name"] + "PRRule",
            description="Rule to handle target for PR",
            enabled=True,
            rule_name=_repo_dict["repo_name"] + "PRRule",
            event_pattern=_pr_event_pattern,
        )

        _pr_build_events_input = events.RuleTargetInput.from_object({
            "sourceVersion": events.EventField.from_path("$.detail.sourceCommit"),
            "artifactsOverride": {"type": "NO_ARTIFACTS"},
            "environmentVariablesOverride": [
                {
                    "name": 'pullRequestId',
                    "value": EventField.from_path('$.detail.pullRequestId'),
                    "type": 'PLAINTEXT',
                },
                {
                    "name": 'repositoryName',
                    "value": EventField.from_path('$.detail.repositoryNames[0]'),
                    "type": 'PLAINTEXT',
                },
                {
                    "name": 'sourceCommit',
                    "value": EventField.from_path('$.detail.sourceCommit'),
                    "type": 'PLAINTEXT',
                },
                {
                    "name": 'destinationCommit',
                    "value": EventField.from_path('$.detail.destinationCommit'),
                    "type": 'PLAINTEXT',
                },
                {
                    "name": 'revisionId',
                    "value": EventField.from_path('$.detail.revisionId'),
                    "type": 'PLAINTEXT',
                },
            ],

        })

        _pr_event_rule.add_target(
            targets.LambdaFunction(_pr_lambda)
        )
        _pr_event_rule.add_target(
            targets.CodeBuildProject(
                _pr_build,
                event=_pr_build_events_input
            )
        )

        _pr_results_event_pattern = events.EventPattern(
            account=[self.account],
            source=["aws.codebuild"],
            detail={
                "build-status": ["FAILED", "SUCCEEDED"],
                "project-name": ["patientCommunicationPRBuild"]
            },
        )

        _pr_results_event_rule = events.Rule(
            self,
            _repo_dict["repo_name"] + "CodeBuildResultsRule",
            description="Rule to handle Results for PR",
            enabled=True,
            rule_name=_repo_dict["repo_name"] + "CodeBuildResultsRule",
            event_pattern=_pr_results_event_pattern,
        )
        _pr_results_event_rule.add_target(
            targets.LambdaFunction(_pr_results_lambda)
        )
