### Create Dataflow Workbench Instance

1. Using the Navigation menu in the Google Cloud console, select __Dataflow__ > __Workbench__ from the __Analytics__ section.

__Tip:__ You can also search for `Dataflow Workbench` using the Search box in the Console toolbar.

2. If the __Enable Notebooks API__ link appears, click the link to activate the API.
   

3. From the Workbench page, click the __Create New__ button. <div>Name the Notebook __my-notebook__, choose the __<ql-variable key="project_0.default_region" placeHolder="<filled in at lab start>"></ql-variable>__ region. You may choose any zone for this region.

4. Click __Machine type__ from the list on the left, select __E2 standard__ and __e2-standard-2__ for the Machine type.  

5. Leave the remaining fields at their default and click __Create__.

6. When the instance is ready, click the __Open Jupyter__ link. This opens Jupyter in another browser tab.<div> On the __Launcher__ tab that is open, scroll down (if necessary) and click __Terminal__.</div><br> <div>Run the following command to clone the Git repository that contains the files needed for this lab:</div>

```
git clone https://github.com/GoogleCloudPlatform/training-data-analyst
```
