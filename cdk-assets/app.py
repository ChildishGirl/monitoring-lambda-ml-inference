import aws_cdk as cdk
from stack.inference_monitoring_stack import *


app = cdk.App()
InferenceMonitoringStack(app, "CloudwatchMlMonitoringStack")
app.synth()
