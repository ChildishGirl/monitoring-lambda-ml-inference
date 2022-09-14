import json
import boto3
import numpy as np
import pandas as pd
from xgboost import XGBClassifier


# Create session with CloudWatch
cloudwatch = boto3.client('cloudwatch')
# Load model
model = XGBClassifier()
model.load_model('sample_model.json')


def handler(event, context):
    # Get features for prediction
    data = pd.DataFrame(event)

    # Make prediction
    response = int(model.predict(data)[0])
    probability = np.max(model.predict_proba(data)).item()

    # Log parameters of the run
    log_message = {'Log level': 'INFO',
                   'Parameters for run': event,
                   'Predicted value': response,
                   'Predicted probability': probability}
    context.log(log_message)

    # Send custom metric to CloudWatch
    cloudwatch.put_metric_data(Namespace='SampleModel',
                               MetricData=[{'MetricName': 'PredictionProbability',
                                            'Dimensions': [
                                                {'Name': 'APP_VERSION',
                                                 'Value': '1.0'}],
                                            'Unit': 'None',
                                            'Value': probability}])
    return {'statusCode': 200,
            'body': json.dumps(
                {'predicted_label': response})}
