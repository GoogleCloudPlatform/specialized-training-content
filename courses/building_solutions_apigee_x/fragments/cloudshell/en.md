### Activate Cloud Shell

Cloud Shell is a virtual machine that is loaded with development tools. It offers a persistent 5GB home directory and runs on the Google Cloud. Cloud Shell provides command-line access to your Google Cloud resources. 

1. Click **Activate Cloud Shell** ![Activate Cloud Shell icon](https://storage.googleapis.com/cloud-training/images/devshell.png) at the top of the Google Cloud console.


When you are connected, you are already authenticated, and the project is set to your **PROJECT_ID**. The output contains a line that declares the **PROJECT_ID** for this session:

<ql-code-block output>
Your Cloud Platform project in this session is set to YOUR_PROJECT_ID
</ql-code-block>

`gcloud` is the command-line tool for Google Cloud. It comes pre-installed on Cloud Shell and supports tab-completion. 

2. (Optional) You can list the active account name with this command:

```
gcloud auth list
```
3. Click __Authorize__.

4. Your output should now look like this:

**Output:**
```output
ACTIVE: *
ACCOUNT: student-01-xxxxxxxxxxxx@qwiklabs.net

To set the active account, run:
    $ gcloud config set account `ACCOUNT`
```

4. (Optional) You can list the project ID with this command:

```
gcloud config list project
```

**Output:**

```output
[core]
project = <project_ID>
```
**Example output:**

```Output
[core]
project = qwiklabs-gcp-44776a13dea667a6
```
<ql-infobox>
<strong>Note: </strong>For full documentation of <code>gcloud</code>, in Google Cloud, refer to <a href="https://cloud.google.com/sdk/gcloud" target="_blank">the gcloud CLI overview guide</a>.
</ql-infobox>
