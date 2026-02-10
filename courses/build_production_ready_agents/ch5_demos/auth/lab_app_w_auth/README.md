# Lab App w/Auth

## Overview

This is a simple example of adding OAuth access control to the application from Chapter 2 lab.

1. Server has added middleware that checks for valid credentials
2. Client has code that supports Google login

## Server

1. `authentication_middleware` checks for valid tokens

## Client

1. Uses Google's GSI client
2. Login panel implemented in <!-- Authentication Section -->

# Demo

If you want to do more than quickly tour the code...

### Create credential

1. Create an Oauth Web credential
2. Configure authorized origin to `http://localhost:8080`
   
### Update code
3. Create a `.env` file from `.env.example` and set:
   - `GOOGLE_CLOUD_PROJECT` - your Google Cloud project ID
   - `GOOGLE_OAUTH_CLIENT_ID` - your OAuth client id
4. In the **client_auth.html** file, replace the `YOUR_CLIENT_ID_HERE` placeholder with your OAuth client id

### Start server
5. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
6. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
7. Run server: `python sessions_server_auth.py`

### Start client
8. Open 2nd terminal
9. Run `python -m http.server 8080`
10. In client, note the login area (forced because page load tries to call session endpoint)
11. Demonstrate login flow
12. Show user logged in and session created