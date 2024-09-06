## To Run
1. Clone the repo
2. Change to the application folder (it should be the `dsl/clicks-service` folder) and run the following to create a Virtual Environment:

```
pip install virtualenv
virtualenv ~/clicks-service-env
source ~/clicks-service-env/bin/activate
```

3. Use Pip to install the prequisites

```
pip install -r requirements.txt
```

4. To test the pogram run:

```
python main.py
```

5. If running in Google Cloud Shell, test your app using __Web Preview__ on port 8080. If running on your own computer browse to localhost:8080. 

6. Deploy the App to Cloud Run. 

7. Setup as a Push Subscriber.
