# Scaife Stack

The **scaife-stack** project demonstrates an implementation of the Scaife Viewer frontend and backend.  The Scaife Viewer dev team hopes to continue to evolve this repository to serve as a template for sites that wish to utilize the Scaife Viewer.

## Site Components
- [frontend (Viewer)](frontend/README.md)
- [backend (ATLAS)](backend/README.md)

## Codespaces

This project can be developed via [GitHub Codespaces](https://github.com/features/codespaces).

### Create the codespace
- Browse to https://github.com/scaife-viewer/beyond-translation-site and fork the repo to your own GitHub organization.  This will make it easier to open pull requests against `scaife-viewer/beyond-translation-site`.

- From the "Code" button choose the "Codespaces" tab and then "Create codespace on main": ![image-20230609113900044](https://p.ipic.vip/n17meq.png)

- This will build a new Codespace environment: ![image-20230609113955162](https://p.ipic.vip/coeobl.png)
- From the "Codespaces" menu at the bottom left corner of the screen (can also use F1 to open command search bar), select "Stop current codespace": 
  - ![image-20230614095207321](https://f000.backblazeb2.com/file/typora-images-23-06-14/uPic/image-20230614095207321.png) 
  - ![image-20230609161218432](https://p.ipic.vip/jfroyd.jpg)
  - ![image-20230609114120729](https://p.ipic.vip/wt9idm.png)

- Browse to https://github.com/codespaces, navigate to the codespace and rename it: ![image-20230609114212538](https://p.ipic.vip/o9tav0.png)

![image-20230609114215203](https://p.ipic.vip/tvpwo2.png)

### Set up project in the codespace

Follow the steps below to configure the codespace for development.

_NOTE_: This process will likely be streamlined by customizing Beyond Translation's [dev container configuration](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers)

#### Resize the codespace
- Change the machine type to use 4 cores / 8 gigabytes of RAM:

![image-20230609114240488](https://p.ipic.vip/tt6pxn.png)

![image-20230609114302426](https://p.ipic.vip/ufjiq1.png)

The increased resources are required for the initial ingestion of content within the codespace.

- Re-open the codespace: ![image-20230609114327861](https://p.ipic.vip/o359ri.png)

- In a new terminal, run the command below to verify the resize was successful:

  ```
  free -m
  ```

     ![image-20230609114425494](https://p.ipic.vip/7oonwe.png)

#### Install the frontend
Next, we'll be configuring the frontend dependencies.  Use the Codespaces terminal to complete the steps below.

- Install Node.js v12:

```
cd frontend
nvm install 12
```

- Select Node.js v12

```
nvm use 12
```
<!-- TODO: Revisit shell integration, https://github.com/nvm-sh/nvm#deeper -->

- Install dependencies

```
yarn install
```

- Build static dependencies

```
yarn build
```

This will create a frontend bundle that will be served by the backend.

#### Install the backend
The backend will run in a Python [virtual environment](https://docs.python.org/3/library/venv.html).

```
..
cd ../backend
```

- Create the virtual environment and activate it:
```shell
python3 -m venv .venv
source .venv/bin/activate
```
- Update the `pip` and `wheel` packages before installing the project packages; the install the project packages:
```shell
pip install pip wheel --upgrade
pip install -r requirements-dev.txt
```
- Copy the frontend bundle:
```shell
mkdir -p static
./manage.py collectstatic --noinput
```
- Initialize the SQLite database:
```shell
./manage.py migrate
```
- Start the backend dev server:
```shell
./manage.py runserver
```

#### Test out the application

When `./manage.py runserver` is invoked, the Codespaces environment should prompt to expose the port.
- Browse to the "ports" tab and make the port public: ![image-20230609115553092](https://p.ipic.vip/63sbtb.png)

- From the "ports" tab, click the link in local address to open in browser: ![image-20230609115624596](https://p.ipic.vip/55t1ag.png)
- Browse to `/graphql/`: ![image-20230609115647298](https://p.ipic.vip/a53ecz.png)

Go back to the terminal and stop the dev server process (`ctrl-c`).

#### Ingest initial data

The final step will be to run a script that loads all of the current data into a SQLite database:


```shell
./manage.py prepare_atlas_db --force
```

<!-- TODO: Clean up the output -->

#### Resize the codespace again
- After the script completes, select the "Codespaces" menu at the bottom right of the screen (or use F1 for command search bar)and then select "Stop current codespace":

![image-20230609161218432](https://p.ipic.vip/jfroyd.jpg)

![image-20230609114120729](https://p.ipic.vip/wt9idm.png)

- Go to https://github.com/codespaces and change the machine type back to 2 core:
![image-20230609160251564](https://p.ipic.vip/9cdqum.png)

![image-20230609160301728](https://p.ipic.vip/laohc7.png)

Re-open the space in the browser

![image-20230609160328502](https://p.ipic.vip/aruzkp.png)


### Developing in the Codespace
After the codespace has been configured for development, use the steps below to run the frontend and backend development servers.

#### Backend dev server


- Open a terminal and navigate to `backend/`:
```shell
cd backend
```
- Activate the virtual environment:
```shell
source .venv/bin/activate
```
- Start the backend dev server
```shell
./manage.py runserver
```
- Make port `8000` public: ![image-20230609160503795](https://p.ipic.vip/qwx6pg.jpg)

- Open the port in the browser

- ![image-20230609160517851](https://p.ipic.vip/1ijbxo.jpg)

![image-20230609160526215](https://p.ipic.vip/h8wi1z.jpg)

- Copy the provided URL to the clipboard, e.g.
```
https://jacobwegner-improved-space-fortnight-4j77v65qvh9jj-8000.preview.app.github.dev/
```

#### Frontend dev server
- Open a new terminal and navigate to `frontend/`
```shell
cd frontend
```
- Select Node 12:
```shell
nvm use 12
```
- Set the `VUE_APP_ATLAS_GRAPHQL_ENDPOINT` variable, using the provided URL on the clipboard. Append `/graphql`, e.g.:
```shell
export VUE_APP_ATLAS_GRAPHQL_ENDPOINT="https://jacobwegner-improved-space-fortnight-4j77v65qvh9jj-8000.preview.app.github.dev/graphql/"
```

This will tell the frontend to use the backend dev server to load content

- Run the frontend dev server:
```shell
yarn serve
```



![image-20230609161017737](https://p.ipic.vip/h4ps6n.jpg)

- Make port 8080 public: ![image-20230609160733464](https://p.ipic.vip/vzafu9.jpg)

- Open the frontend URL in the browser:

![image-20230609160755723](https://p.ipic.vip/v3b8f0.jpg)

- Verify that content is shown:
![image-20230609161210417](https://p.ipic.vip/ifaed0.jpg)

#### Stopping the codespace
By default, the codespace will stop after 30 minutes of inactivity.

To stop the codespace manually:

- Select the "Codespaces" menu at the bottom right of the screen and then select "Stop current codespace":

![image-20230609161218432](https://p.ipic.vip/jfroyd.jpg)
![image-20230609114120729](https://p.ipic.vip/wt9idm.png)


## Local Development using [Docker Compose](https://docs.docker.com/compose/)

The following Dockerfiles are configured to build environments / install dependencies for the frontend and backend:
- `frontend-dev.dockerfile`
- `backend-dev.dockerfile`

`docker-compose.yml` and `docker-compose.override.yml` are set up to mount the appropriate component to the appropriate
service:
- The `atlas` service runs the backend, and is addressable via http://localhost:8000/graphql/
- The `viewer` service runs the frontend, and is addressable via http://localhost:8080/

To bring up the stack:

```shell
docker-compose up
```

To rebuild images used by the stack:

```shell
docker-compose up --build
```

(you may also use `docker-compose up -d` to run the stack in the background)

To bring down the stack and remove data volumes:

```shell
docker-compose down --rmi all -v
```

To run a one-off container for the `atlas` service:
```shell
docker-compose run atlas sh
```

To connect to the running container for the `atlas` service:
```shell
docker-compose exec atlas sh

```

## Loading data into ATLAS
By design, the ATLAS data ingestion process is designed as an atomic process:

- New texts or annotations are staged into the `SV_ATLAS_DATA_DIR` directory
- ATLAS ingestion scripts are used to ingest the data into the ATLAS SQlite database

If a new annotation was to be added into ATLAS, the entire SQLite database would be destroyed
and all data re-ingested.  Please note that the Scaife Viewer dev team _does_ plan on supporting
incremental updates in the future.

<!-- TODO: Prefer prepare_atlas_db command? -->
For the `translation-alignments-stack`, load data via
```shell
docker-compose exec atlas ./manage.py prepare_atlas_db
```

## Deployment
For convenience, `heroku.yml` and `heroku.dockerfile` can be used to deploy the stack as a Heroku application.

- Heroku's GitHub integration is used to trigger a deployment when commits are made against the `main` branch.
- [Review apps](https://devcenter.heroku.com/articles/build-docker-images-heroku-yml#review-apps-and-app-json) can be used to spin up a copy of the application when pull requests are opened on GitHub.
- `heroku.dockerfile` is used to build the frontend and backend into a single image.  Frontend static assets are served via Django and Whitenoise at the application root (`/`).  See [Building docker images with heroku.yml](https://devcenter.heroku.com/articles/build-docker-images-heroku-yml) for more information.

Customize `app.json` and `heroku.yml` as-needed for projects derived from this repo.

### Review Apps
[Review Apps](https://devcenter.heroku.com/articles/github-integration-review-apps) have been set up for Beyond Translation.

To have a review app created for a pull request:
- Open a new pull request
- Ping @jacobwegner on the pull request and request that a review app be created
- Once the review app has been created, a "View deployment" button will appear on the PR:
![image](https://github.com/scaife-viewer/beyond-translation-site/assets/629062/472d6769-332a-4728-b6f1-991b64dccb71)
- Subsequent commits pushed to the PR branch will trigger new deployments

## Nav

- Set `VUE_APP_ABOUT_URL` and `VUE_APP_ABOUT_TEXT` to add a link to an about page

