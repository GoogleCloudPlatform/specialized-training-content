from google.cloud import aiplatform

PROJECT_ID='your-project-id' # UPDATE ME
LOCATION='us-central1' # UPDATE ME
ENDPOINT='5532261234567260544' # UPDATE ME

model_endpoint = aiplatform.Endpoint(f'projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT}')

SAMPLE_REQUEST = [{'step' : [100],
                  'action' : ['PAYMENT'],
                  'amount' : [500.45],
                  'idOrig' : ["148935081346"],
                  'oldBalanceOrig' : [1200.45],
                  'newBalanceOrig' : [700.00],
                  'idDest' : ["M-2398004569"],
                  'oldBalanceDest' : [1890.00],
                  'newBalanceDest' : [2390.00]
                 }]

def parse_prediction(response):
    predict_prob = response.predictions[0][0]*100
    return f'There is a {predict_prob} percent chance of fraud for this transaction'

if __name__ == '__main__':
    response = model_endpoint.predict(SAMPLE_REQUEST)
    print(parse_prediction(response))
