# Scaife Stack

The **scaife-stack** project demonstrates an implementation of the Scaife Viewer frontend and backend.  The Scaife Viewer dev team hopes to continue to evolve this repository to serve as a template for sites that wish to utilize the Scaife Viewer.

## Site Components
- [frontend (Viewer)](frontend/README.md)
- [backend (ATLAS)](backend/README.md)

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
docker-compose exec atlas python manage.py prepare_atlas_db
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
