# Integrating a Client Application

## Overview

In this lab, you deploy **Show-Me-Now** for testing. **Show-Me-Now** is an Angular Single Page Application and includes content validation. You configure the application for Firebase Authentication, deploy it to Cloud Run, and test to confirm that integration with Apigee is successful.

## Objectives

In this lab, you learn how to:
- Checkout the source code for Show Me Now 
- Establish a local Cloud Source Repository
- Set up continuous deployment to Cloud Run
- Enable Firebase Authentication 
- Configure Show-Me-Now and Apigee to use Authentication

## Setup and Requirements

![[/fragments/startqwiklab]]


![[/fragments/cloudshell]]


<!-- ![[/fragments/apigeex-ui]] -->

## Task 0. Provison LAB resources 

1. Navigate to the the Google Cloud console at **https://console.cloud.google.com**.

2. Click Activate Cloud Shell (Activate Cloud Shell icon) in the top menu to open Cloud Shell

3.  To ensure that you are in the Cloud Shell home directory, execute the following command.

    ```bash
    cd ~ 
    ```

4. In Cloud Shell, confirm the default compute zone is set to the zone used by the gateway VM.

    <ql-code-block templated>
    gcloud config set compute/zone {{{project_0.default_zone|vm_zone}}}
    </ql-code-block>

5. Clone the class repository and move into the repository root folder.

    ```bash
    git clone https://github.com/fabltd/Apigee-utils
    cd Apigee-utils
    ```

    <ql-infobox>
     The following step runs a script that provisons all the resources you will need
    </ql-infobox>

6. Create and configure the gateway / legacy VMs and base API proxy using the following bash script. If you are prompted to generate SSH keys, confirm YES and press ENTER twice for passphrase.

   ```bash
    ./setup/install/lab4/install.sh
    ```

7. If you are prompted to generate SSH keys, confirm YES and press ENTER twice for passphrase.

8. Wait for the script to complete and you should see Done - Return to Apigee.

## Task 1. Download the source code in Cloud Shell

In this task, you clone the source code for the **Show Me Now** Angular application. 

1. In the Google Cloud console, in the top menu, click **Activate Cloud Shell** (![Activate Cloud Shell icon](images/activate_shell.png)) to open Cloud Shell.

2. To configure git for Cloud Shell, modify the email address and username in the following commands to appropriate values and execute them in the Cloud Shell terminal. 

    ```bash
    git config --global user.email "you@example.com"
    git config --global user.name "Your Name"
    ```

3. To clone the repository for the **Show Me Now** web application, execute the following command.

    ```
    cd ~
    git clone https://github.com/fabltd/apigee-show-me-now
    ```

4. Navigate to the directory that contains your working files.

    ```bash
    cd ~/apigee-show-me-now/
    ```

5. To create a Google Cloud Source Repository named **showmenow** and push the initial code to the repository, execute the following commands.

    ```bash
    gcloud source repos create showmenow
    git remote add showmenow \
     https://source.developers.google.com/p/$DEVSHELL_PROJECT_ID/r/showmenow
    git push --all showmenow
    ```

6. Close **Cloud Shell**.

7. In the Google Cloud console, locate **Source Repositories**, right-click and select **Open Link in New Tab**.

    <ql-infobox>
    Note: Cloud Source Repositories have their own UI.
    </ql-infobox>

8. In the Cloud Source Repository, click **HEAD** and select Branch **main**. Verify that the source code for **Show Me Now** is shown.

9. Return to the Cloud console, reopen Cloud Shell, and click **Open Editor**.

    <ql-infobox>
    Note: In Incognito mode in Chrome, you may need to click the Open in a new window link in order to access the Cloud Shell Editor.  
    </ql-infobox>

10. Inside the Editor Explorer pane, navigate to the **apigee-show-me-now** folder.

    <ql-infobox>
    Note: the application is a standard Single Page Application using the popular Angular framework.
    </ql-infobox>

11. Now navigate to the **apigee-show-me-now/src** folder. You will be editing files in this directory in upcoming tasks.

## Task 2. Create a Firebase project

In this task, you use Firebase, Google’s mobile application development platform. Firebase has many tools that assist in the development and deployment of applications. **Show Me Now** uses Firebase Authentication to authenticate users. 

1. Open a new browser tab and navigate to [https://console.firebase.google.com/](https://console.firebase.google.com/).

    <ql-infobox>
    You may need to sign in again using your lab username and password.
    </ql-infobox>

2. On the **Welcome to Firebase!** page, click **Add project**.

3. Enter your project ID. This can be located to the left of these instructions, and should be available for selection once you click in the dialog.

    ![Enter project](images/firebaseproject.png)

4. Agree to the terms and conditions and confirm you will use Firebase for professional purposes, then click **Continue**

5. In the **Confirm Firebase billing plan** dialog for Pay as you go, click **Confirm plan** and **Continue**.

6. Toggle **Enable Google Analytics for this project** to the off position and click **Add Firebase**.

7. When it appears, click **Continue**.


## Task 3. Configure Firebase Authentication

1. In the left navigation of the Firebase page, click **All products** and then in the main pane, click **Authentication**.

    ![Firebase Authentication](images/authentication.png)

2. On the next page, click **Get Started**.

3. On the next page in the **Additional Providers** section, click **Google** and then toggle **Enable** to the on position.

4. Select your Qwiklabs student email as the **Project support email** and then click **Save**.

5. Click **Settings** and **Authroized domains** 

6. Click **Add domain** and insert **run.app** and click **Add**

7. Click **Project Overview** in the upper-left corner of the Firebase console.

8. Locate the **Getting started** section and click the web icon ```</>```.

    ![Web Icon](images/addapp.png)

9. In the **Register your app** wizard step, give your app the nickname **Show Me Now**, then click **Register app**.

10. In **Add Firebase SDK** (Step 2), locate the variable named **firebaseConfig**.

11. Select and copy the content of the **firebaseConfig** object.

![firebase config](images/config.png)

12. Click **Continue to console**.

13. Return to Cloud Shell Editor in your original browser tab and refresh the browser to ensure you are connected.

14. Use Explorer to locate the file **apigee-show-me-now/src/environments/environment.ts** and click the file to open it in the editor. You should see the following content.

    ```javascript
    export const environment = {
        production: true,
        recaptcha: '',
        url: 'https://',
        firebaseConfig : {
            apiKey: "",
            authDomain: "",
            projectId: "",
            storageBucket: "",
            messagingSenderId: "",
            appId: ""
        },
        key: ''
    };
    ```

15. Replace the entire contents of the **firebaseConfig** object with the section copied from the Firebase console.

    **EXAMPLE**

    ```javascript
    export const environment = {
        production: true,
        recaptcha: '',
        url: '',
        firebaseConfig : {
            apiKey: "AIzaSyBSz00WVTQX6apvVPyzFe-3uY7id700Wq0",
            authDomain: "qwiklabs-gcp-03-2a13b9bc2c16.firebaseapp.com",
            projectId: "qwiklabs-gcp-03-2a13b9bc2c16",
            storageBucket: "qwiklabs-gcp-03-2a13b9bc2c16.appspot.com",
            messagingSenderId: "997243225397",
            appId: "1:997243225397:web:3cacb49a4c6027c4f1787c"
        },
        key: ''
    };
    ```

## Task 4. Add API details to the Angular configuration

The Angular application requires your API key and Apigee endpoint in order to access the service. This information is available inside Apigee.

1. In a separate browser tab from Google Cloud console, open the Apigee console at [console.cloud.google.com/apigee](https://console.cloud.google.com/apigee).

Alternatively, to open the Apigee console from the Google Cloud console Navigation menu (![Navigation menu icon](https://storage.googleapis.com/cloud-training/images/menu.png)), select **Tools > Apigee**.
    
2. Verify that your Apigee Organization is selected at the top of the console.

3. On the left navigation menu, select **Distribution > Apps**.

4. On the list page, select **show-me-now**

5. On the details page, locate the **Credentials** section and click **Show** beside **Key**. Select and copy the API key. Save the API key locally as you will need it soon.

6. In the left navigation menu, select **Management > Environments** and then click **Environment Groups** and copy the hostname from __test-env-group__. Save the hostname so that it is available for the following steps.

    ![hostname](images/hostname.png)

7. Return to the **show-me-now/src/environments/environment.prod.ts** file in the editor and update the value of the **url** with the hostname from Apigee plus **show-me-now/v0/**.

    **EXAMPLE**

    ```javascript
     url: 'https://34.107.155.147.nip.io/show-me-now/v0/',
    ```

    <ql-infobox>
    Note:  Make sure the value is wrapped with single quotes <strong>'</strong>.
    </ql-infobox>

8. Update the key property with the API key you retrieved from the Credentials section.

    <ql-infobox>
    Note:  Make sure the value is wrapped with single quotes <strong>'</strong>, and that the string ends with a forward slash <strong>/</strong>.
    </ql-infobox>


    **EXAMPLE - Complete File**

    ```javascript
    export const environment = {
        production: true,
        recaptcha: '',
        url: 'https://34.107.155.147.nip.io/show-me-now/v0/',
        firebaseConfig : {
            apiKey: "AIzaSyBSz00WVTQX6apvVPyzFe-3uY7id700Wq0",
            authDomain: "qwiklabs-gcp-03-2a13b9bc2c16.firebaseapp.com",
            projectId: "qwiklabs-gcp-03-2a13b9bc2c16",
            storageBucket: "qwiklabs-gcp-03-2a13b9bc2c16.appspot.com",
            messagingSenderId: "997243225397",
            appId: "1:997243225397:web:3cacb49a4c6027c4f1787c"
        },
        key: 'L6DyrxBdik0KtQ8ikTodHRxekrG1tNC8GHk1Y70XIvXBF3tO'
    };
    ```

    <ql-infobox>
    Your configuration is complete. Now it must be committed and pushed to the Cloud Source Repository.
    </ql-infobox>

9. Open the **Cloud Shell Terminal** and run the following commands to navigate to the root folder of the Angular application, commit the changes, and push them to your Google Cloud Source Repository.

    ```bash
    cd ~/apigee-show-me-now
    git commit -a -m "updated config" 
    git push showmenow main
    ```

10. Close **Cloud Shell**.

## Task 5. Deploy Show Me Now to Cloud Run

1. In the Google Cloud console, navigate to **Cloud Run**.

2. Click **Create Service** to create a new service.

3. Select the **Continuously deploy new revisions from a source repository** radio button and then the **Set up with Cloud Build** button.

4. In the flyout panel, select **Cloud Source Repositories** in the **Repository Provider** dropdown.

5. In the **Repository** textbox, select **showmenow** as the repository, then click **NEXT.**

6. In the **Build Configuration** section, select the **Dockerfile** radio button. Leave all other settings at their default values and click **Save**. 

7. Leave the **Service name** as **showmenow**.

8. Set **Region** to <ql-variable key="project_0.default_region" placeHolder="<filled in at lab start>"></ql-variable>.

9. Scroll down to **Autoscaling** and set the **Maximum number of instances** to **1** and leave the default **All** setting to allow direct access from the internet. 

10. Under **Authentication**, select **Allow unauthenticated invocations**.

11. Click **Container, Connections, Security**, and set **General > Container port** to **80**

12. Leave all other settings at their default values and click **Create**. 

13. Wait for the service URL to appear, and then click the copy icon to copy the URL to your clipboard.

    ![copy url](images/copy.png)

    <ql-infobox>
    Note: The URL will be in the format https://showmenow-[hash]-uc.a.run.app
    </ql-infobox>

14. Return to the Firebase console - [https://console.firebase.google.com/](https://console.firebase.google.com/).

15. In the left pane of the Firebase page, click **Authentication**. 

16. Click the **Settings** tab inside **Authentication** and then click **Authorized domains**.

17. Click **Add domain** and enter the URL copied from Cloud Run. 

18. Delete **https://** from the beginning of the domain and then click **Add**.

19. Return to Cloud Run and continue waiting for your revision to be deployed.

20. Once the revision is deployed, click the URL to start testing.

    <ql-infobox>
    You should now see <strong>Show Me Now</strong> in a new browser window.
    </ql-infobox>

    ![Show Me Now](images/show.png)


## Task 6. Test Show Me Now

1. Click **Login with Google** and select your Qwiklabs account when promted to do so. If you successfully linked Firebase Authentication to **Show Me Now**, you should see something similar to the following.

    ![Show Me Now logged in](images/loggedin.png)

2. In the **Track My Package** box, enter the following tracking number.

    ```
    2nUz1hUbaQdfoS4Sktm9
    ```

3. Note that there is no response. Use the Chrome developer tools to examine the error message.

    **EXAMPLE** substituting **[X]** for the Cloud Run hostname

    ```
    Origin [X] has been blocked by CORS policy: Request header field authorization is not allowed by Access-Control-Allow-Headers in preflight response.
    ```

    <ql-infobox>
    Developer tools can be accessed by right-clicking on the page and selecting <strong>inspect</strong>. The error message is available in the <strong>console</strong> tab.
    </ql-infobox>


## Task 7. Fix the CORS error

1. Return to the browser tab that has Apigee open. 

2. In the left navigation menu, select **Develop > API Proxies**.

3. From the proxy list, select **SMN-Labs**. To switch to the development view, click **Develop**.

4. In the development navigation panel, click the proxy name **SMN-Labs**.

    ![navigation panel](images/metadata1.png)

5. To edit the metadata, click the pencil icon beside **Details**.

    ![navigation panel](images/metadata2.png)

6. Enter the following values in the dialog.

    | Property | Value |
    | --- | --- |
    | Display name | **SMN-Lab4** |
    | Description | **Show Me Now - LAB 4** |


7. In the Policies list, locate **CORS-EnableCORS** and replace the line with the tag ```<Access-Control-Allow-Headers>``` with the following.

    ```xml
    <AllowHeaders>apikey,authorization, email, content-type, origin, x-requested-with, accept, x-recaptcha-key, x-recaptcha-token</AllowHeaders>
    ```

    <ql-infobox>
    Show Me Now forwards the authorization token received from Firebase Authentication to Apigee in the authorization header. Our proxy did not permit this header, resulting in the error.
    </ql-infobox>

8. Click **Save** and **Save as New Revision**.

9. Click **Deploy**.

10. In the Deploy dialog, add the Service Account identifier. 

    <ql-infobox>
    In the Cloud Shell, run the following command to get your service account.
    </ql-infobox>

    ```bash
    gcloud iam service-accounts list --filter="'DISPLAY NAME': Service account for Apigee to access Google services"
    ```

11. Copy the **EMAIL** value an past into the **service account** field of the Deploy dialog.

12. Click **Overview** and verify that the proxy has been deployed successfully.

13. Return to Show Me Now and check the tracking number ```2nUz1hUbaQdfoS4Sktm9``` is still present. Click ***Get Progress*** and you should see the following. You may need to refresh the page.

  ![tracking result](images/track.png)


## Task 8. Test the application

In this task, you explore some of the operations of Show Me Now. When you log in, you are able to fetch all suppliers/shipments/customers. In a real world application, system access would be restricted based on user credentials. Once you have verified full access, you implement access control in Apigee to limit the scope of the logged in user.

1. Return to the browser tab with **Show Me Now** and refreesh the page.

2. Click **Login with Google**. If you are prompted to log in, do so using your Qwiklabs identity.

3. To see details of an individual supplier, click **Suppliers**, enter the ID ```6VylK3m2Pl1vGG800EmF``` in the textbox, and click **Get Supplier**.

    <ql-infobox>
    You should see details of an individual supplier, together with a list of their customers by email address and action buttons. 
    </ql-infobox>

4. To see details of an individual customer, select one of the customer email addresses; e.g., **tkevlin11@pcworld.com**. Click the **Customers** link and paste the email address into the textbox. Click **Get Customer** and you should see an individual customer along with action buttons.

    ![Show Me Now](images/customer.png)

    <ql-infobox>
    Your **@qwiklabs.net** identity is an administrator and can see and change everything. Non-administrator users should only be able to edit their own details. This functionality is naively implemented on the client, leaving your API vulnerable to abuse. 
    </ql-infobox>

    <ql-infobox>
    Next, you explore this vulnerability, and use Apigee policies to protect your API. You begin by temporarily adding your own Google identity as a customer. The email address will only be stored for the duration of this lab. If you don't have a Google identity or don't want to use it, you can skip the testing steps below and move straight to the next task where you implement the policy.
    </ql-infobox>

5. Inside the **Show Me Now** UI, select **Customers** and **Add**. Enter any details you like, but make sure that the email address is a real Google login for which you have the password. 

    <ql-infobox>
    You can now log into <strong>Show Me Now</strong> as a customer. For this, you need a separate browser instance where you are not logged in using the student Qwiklabs identity. 
    </ql-infobox>

6. To get the URL for your second login, click **Track My Package** and then copy the contents of the address bar. 

7. If you are using an Incognito window for this lab, open a separate standard (not Incognito) Chrome window and paste the URL into the address bar. Otherwise, open an Incognito window and paste the URL there.

   <ql-infobox>
    All Incognito windows use the same identity, so if you log in to a second Incognito window as yourself, you will log out the Qwiklabs user even if it is in a different Incognito window.
   </ql-infobox>

8. Click **Login** and log in using the Google identity that you added as a customer. Once logged in, you should only see the **Customers** section in the menu.

9. To edit your own details, click **Customers**.

    <ql-infobox>
    Your email address should be prefilled in the textbox. 
    </ql-infobox>

10. Click **Get Customer** and then **edit** and modify one of the fields. 

11. Click **Update Customer** and then once again retrieve your details to see that the change has been actioned.

    <ql-infobox>
    This works as expected. Unfortunately, the UI developer did not anticipate a customer experimenting with other customers' email addresses. 
    </ql-infobox>

12. Click **Customers**, replace your email address in the textbox with ```tkevlin11@pcworld.com```, and click **Get Customers**. Experiment with changing the user's details.

    <ql-infobox>
    There is nothing to stop you from retrieving, and altering, another user's details. Next, you use Apigee Policies to remove this security vulnerability.
    </ql-infobox>


## Task 9. Lock down the user

All requests sent to the API by users who have logged in using federated authentication are authenticated by JSON Web Tokens (JWT). The Apigee **Verify JWT** policy can be used to verify the token and extract the caller's details, including their email address. This can be used to prevent the unwanted behavior.

1. Return to the browser window where you are logged in as a Qwiklabs student, and click the tab where Apigee is already open, or navigate to the Apigee console at [apigee.google.com](https://apigee.google.com/).

2. In the left navigation menu, select **Proxy development > API Proxies** and then click **SMN-Labs**. 

3. In the top menu, click **Develop**.

4. In the Navigator, select **Customers** in the **Proxy endpoints default**. 

5. In the development panel, click the **+ icon**  for the **Proxy Endpoint default > Request > Customers** conditional flow.

    ![add policy to conditional flow](images/addcustomer.png)
 
6. In the dialog, select **Create new policy**, and select the **Verify JWT** policy from the **Security** group. 

7. Set the following properties and click **Add**. 

    | Property | Value |
    | --- | --- |
    | Name | **VJWT-Firebase** |
    | Display name | **VJWT-Firebase** |

8. In the development panel, locate the policy inside the **Customers** conditional flow and click the **VJWT-Firebase** link.

9. Delete all the existing XML for the **VJWT-Firebase** policy and replace it with the following.

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <VerifyJWT name="VJWT-Firebase">
        <Algorithm>RS256</Algorithm>
        <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
        <PublicKey>
            <JWKS uri="https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"/>
        </PublicKey>
    </VerifyJWT>
    ```

    <ql-infobox>
    This verifies the JWT found in the default location (request.header.authorization).
    </ql-infobox>

10. In the development panel, click the policy step actions icon (![actions icon](images/actions.png)) for the **Proxy Endpoint default > Request > Customers** conditional flow. Click **Move up** to position the **VJWT-Firebase** policy as the first policy in the flow.

    ![move policy to top](images/top.png)
 
    <ql-infobox>
    You can also drag policies to change the order.
    </ql-infobox>

    <ql-infobox>
    Three further policies are required to ensure an individual can only modify their own details: an Assign Message policy, a Raise Fault policy, and a policy that extracts the email address from the JSON body of the request rather than a parameter.
    </ql-infobox>

11. Add an **Assign Message** policy to the Customer Preflow as follows.

    | Property | Value |
    | --- | --- |
    | Name | **AM-Admin-User** |
    | Display name | **AM-Admin-User** |

12. Delete all the existing XML for the **AM-Admin-User** policy and replace it with the following.

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <AssignMessage continueOnError="false" enabled="true" name="AM-Admin-User">
        <DisplayName>AM-Admin-User</DisplayName>
        <AssignVariable>
            <Name>admin</Name>
            <Value>true</Value>
        </AssignVariable>
        <AssignTo createNew="false" transport="http" type="request"/>
    </AssignMessage>
    ```

    <ql-infobox>
    This policy sets the admin variable to true when the condition matches. Note: the condition has not yet been implemented.
    </ql-infobox>

13. In the development panel, move the position the **AM-Admin-User** policy before the existing **EV-Get-Email** policy.

14. Add a **Raise Fault** policy to the Customer Preflow as follows.

    | Property | Value |
    | --- | --- |
    | Name | **RF-JWT-Email-Error** |
    | Display name | **RF-JWT-Email-Error** |

15. Delete all the existing XML for the **RF-JWT-Email-Error** policy and replace it with the following.

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <RaiseFault continueOnError="false" enabled="true" name="RF-JWT-Email-Error">
        <DisplayName>RF-JWT-Email-Error</DisplayName>
        <Properties/>
        <FaultResponse>
            <Set>
                <Headers/>
                <Payload contentType="text/plain"/>
                <StatusCode>401</StatusCode>
                <ReasonPhrase>JWT email does not match request</ReasonPhrase>
            </Set>
        </FaultResponse>
        <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
    </RaiseFault>
    ```

    <ql-infobox>
    This policy will raise a fault if the user attempts to access an account that is not their own.
    </ql-infobox>

16. In the development navigator panel, click **Proxy endpoints > default** to reopen the Proxy endpoint in the development panel.

17. In the XML, locate the ```<Flow name="Customers">``` element and the **AM-Admin-User** ```Step```.

18. Add a new Condition element between the closing ```</Name>``` and ```</Step>``` tags as follows.

    ```xml
    <Condition>jwt.VJWT-Firebase.decoded.claim.email == "REPLACE-ME"</Condition>
    ```

    <ql-infobox>
    The complete step should now be as follows.
    </ql-infobox>

    ```xml
    <Step>
        <Name>AM-Admin-User</Name>
        <Condition>jwt.VJWT-Firebase.decoded.claim.email == "REPLACE-ME"</Condition>
    </Step>
    ```

19. To allow only the Qwiklabs student identity to modify an email address other than their own, modify the Condition by replacing **REPLACE-ME** with the email address of the student identity.

    <ql-infobox>
    The email address is available to the left of these instructions. 
    </ql-infobox>

    **EXAMPLE CONDITION**

    ```xml
    <Step>
        <Name>AM-Admin-User</Name>
        <Condition>jwt.VJWT-Firebase.decoded.claim.email == "student-02-11076261a3d5@qwiklabs.net"</Condition>
    </Step>
    ```

    <ql-infobox>
    This sets the variable <strong>admin</strong> to true if the email address found in the JWT is equal to your student email address. This should be checked in the Raise Fault step.
    </ql-infobox>

20. Also in the ```<Flow name="Customers">``` element in the XML, locate the **RF-JWT-Email-Error** ```Step``` and add the following condition to raise the error if the user requests a customer email other than their own, and the **admin** variable is not set to **true**.

    ```xml
    <Condition>jwt.VJWT-Firebase.claim.email != queryinfo.email and admin != true</Condition>
    ```

    <ql-infobox>
    The complete step should be as follows.
    </ql-infobox>

    ```xml
    <Step>
        <Name>RF-JWT-Email-Error</Name>
        <Condition>jwt.VJWT-Firebase.decoded.claim.email != queryinfo.email and admin != true</Condition>
    </Step>
    ```

21. To ensure the **EV-Get-Email** policy only runs if the user is not an administrator, locate the **EV-Get-Email** ```Step``` in the **Customer** flow and replace the existing condition with the following.

    ```xml
     <Condition>(request.verb = "GET" and admin != true)</Condition>
    ```

    <ql-infobox>
    This ensures the Administrator can still see every customer's data. 
    </ql-infobox>

22. To retrieve a customer email address in the edit path, add an additional **Extract Variables** policy with the following properties. 

    | Property | Value |
    | --- | --- |
    | Name | **EV-Get-Email-Body** |
    | Display name | **EV-Get-Email-Body** |

23. In the development panel, locate the policy inside the **Customers** conditional flow and move it immediately after **EV-Get-Email**. 

24. Click the **EV-Get-Email** link to select it, delete all the existing XML for the **EV-Get-Email** policy and replace it with the following.

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <ExtractVariables continueOnError="false" enabled="true" name="EV-Get-Email-Body">
    <DisplayName>EV-Get-Email-Body</DisplayName>
    <Properties/>
    <Source>request</Source>
    <JSONPayload>
        <Variable name="email" type="string">
        <JSONPath>$.results[0].Email</JSONPath>
        </Variable>
    </JSONPayload>
    <VariablePrefix>queryinfo</VariablePrefix>
    <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
    </ExtractVariables>
    ```

    <ql-infobox>
    This policy captures the <strong>email</strong> from the JSON body and stores it as a variable for use in the validation process.
    </ql-infobox>

25. To ensure the **EV-Get-Email-Body** policy only runs if the user is not an administrator, locate the **EV-Get-Email** ```Step``` in the **Customer** flow and add the following condition.

    ```xml
     <Condition>(request.verb = "PUT" and admin != true)</Condition>
    ```

 26. To ensure the email variable is evaluated on a **PUT** as well as a **GET** request, but only if the user is not an admin, locate the **EV-DLP** ```Step``` in the **Customer** flow and replace the existing condition with the following.

     ```xml
     <Condition>(admin != true and request.verb = "GET" OR request.verb = "PUT")</Condition>
     ```


27. Click **Save** and **Save as New Revision**

28. Click **Deploy** and add in the dialog, the Service Account identifier that you saved in an earlier lab.

    <ql-infobox>
    If you have mislaid your service account identifier, the steps to discover it are available above.
    </ql-infobox>

29. Click __Deploy__ and then __Confirm__ and wait until the revision has finished deploying.


## Task 10. Test user verification

1. To test your policies as an administrator, locate the URL for **Show Me Now** and open it in a new tab in the same browser window as your Apigee development environment.

2. Click **Login** and when the **Customers** menu item appears, click it and enter the following email on the **Find Customer** page.

    ```
    tkevlin11@pcworld.com
    ```

    <ql-infobox>
    You should be able to see and edit the user because you are an administrator. 
    </ql-infobox>

3. In a separate non-Incognito browser window, open **Show Me Now** using the Google identity you added as a customer in an earlier step.

4. Attempt to retrieve and edit your own details, and those of ```tkevlin11@pcworld.com```. 

    <ql-infobox>
    You should be able to see and edit your own details, but attempts to see or edit other users should result in an error. 
    </ql-infobox>



### **Congratulations!** You enabled Firebase Authentication and used Apigee to verify the token provisioned by Firebase. In production, you would have a more in-depth configuration. This solution only verifies the email address, allowing hackers to provide a token with an administrator email address and bypass this simple security check. 

![[/fragments/copyright]]