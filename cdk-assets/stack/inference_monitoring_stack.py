from aws_cdk import Stack, Duration
import aws_cdk.aws_iam as _iam
import aws_cdk.aws_sns as _sns
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_chatbot as _chatbot
import aws_cdk.aws_cloudwatch as _cloudwatch
import aws_cdk.aws_cloudwatch_actions as _cw_actions


class InferenceMonitoringStack(Stack):

    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create Inference with Docker image inside Lambda function
        inference_lambda = _lambda.DockerImageFunction(self, 'processing_lambda',
                                                       function_name='model_inference',
                                                       description='Inference for sample model.',
                                                       code=_lambda.DockerImageCode.from_image_asset('assets/',
                                                                                                     file='dockerfile'),
                                                       architecture=_lambda.Architecture.X86_64,
                                                       timeout=Duration.minutes(3),
                                                       retry_attempts=0,
                                                       memory_size=250)

        # Add permissions for Lambda function
        inference_lambda.role.attach_inline_policy(_iam.Policy(self, 'cloudwatch_access_fer_lambda',
                                                               statements=[
                                                                   _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                                                                        actions=['cloudwatch:*'],
                                                                                        resources=['*'])]))

        # Create CloudWatch dashboard
        dashboard = _cloudwatch.Dashboard(self, 'model_dashboard',
                                          dashboard_name='example-model-dashboard',
                                          period_override=_cloudwatch.PeriodOverride.AUTO,
                                          widgets=[[_cloudwatch.TextWidget(markdown='# Sample model performance',
                                                                           width=24,
                                                                           height=2)]])

        # Define custom metrics
        probability_metric = _cloudwatch.Metric(namespace='SampleModel',
                                                metric_name='PredictionProbability',
                                                dimensions_map={'APP_VERSION': '1.0'})
        max_memory_metric = _cloudwatch.Metric(namespace='LambdaInsights',
                                               metric_name='memory_utilization',
                                               dimensions_map={'function_name': inference_lambda.function_name})
        init_time_metric = _cloudwatch.Metric(namespace='LambdaInsights',
                                              metric_name='init_duration',
                                              dimensions_map={'function_name': inference_lambda.function_name})

        # Add widgets to CloudWatch dashboard
        dashboard.add_widgets(_cloudwatch.Row(_cloudwatch.GraphWidget(title='Lambda: Invocations & Errors', width=12,
                                                                      left=[inference_lambda.metric_invocations(
                                                                          statistic='Sum',
                                                                          period=Duration.minutes(1)),
                                                                          inference_lambda.metric_errors(
                                                                              statistic='Sum',
                                                                              period=Duration.minutes(1))]),
                                              _cloudwatch.GraphWidget(title='Model: Prediction probability', width=12,
                                                                      left=[probability_metric]),
                                              _cloudwatch.SingleValueWidget(title='Lambda: Maximum memory used',
                                                                            width=12,
                                                                            height=6,
                                                                            metrics=[max_memory_metric],
                                                                            sparkline=True),
                                              _cloudwatch.GraphWidget(title='Lambda: Time to initialize', width=12,
                                                                      left=[init_time_metric])
                                              ))

        # Create CloudWatch alarm for low prediction probability
        alarm = _cloudwatch.Alarm(self, 'probability_alarm',
                                  alarm_name='low-probability-alarm',
                                  metric=probability_metric,
                                  threshold=0.45,
                                  comparison_operator=_cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                                  evaluation_periods=1,
                                  datapoints_to_alarm=1)

        # Create SNS topic and use it an alarm action
        alarms_topic = _sns.Topic(self, 'AlarmsTopic',
                                  topic_name='ds-sample-model-alarms')
        alarm.add_alarm_action(_cw_actions.SnsAction(alarms_topic))

        # Add Slack notifications
        slack = _chatbot.SlackChannelConfiguration(self, 'MySlackChannel',
                                                   slack_channel_configuration_name='announcements',
                                                   slack_workspace_id='YOUR_WORKSPACE_ID',
                                                   slack_channel_id='YOUR_CHANNEL_ID',
                                                   notification_topics=[alarms_topic])
        slack.role.attach_inline_policy(_iam.Policy(self, 'slack_policy',
                                                    statements=[_iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                                                                     actions=['chatbot:*'],
                                                                                     resources=['*'])]))

