# Deploy to Google Cloud Run

## Build

- Set a `TAG_NAME` environment variable:
```shell
export TAG_NAME=`git log --pretty=format:'%h' \-n 1`
```
- Build the image using Google Cloud Build:
```shell
./devops/build.sh
```

This will archive the git repo at HEAD; pass a git ref `./devops/build.sh master` to target another branch.

The archive will be uploaded to Cloud Build and built using `cloudbuild.yaml`

## Deploy

```shell
./devops/deploy.sh
```

Using `TAG_NAME` from the build step above, the deploy script will create a new revision in Google Cloud Run.

The service will be available at **https://`git-${TAG_NAME}`---beyond-translation-site-gwgx3f4hha-uc.a.run.app**.

## Add revision tag

Using the revision name returned from "Deploy", (e.g. `beyond-translation-site-00033-fuj`):

```shell
./devops/add_revision_tag.sh beyond-translation-site-00033-fuj daphne
```

This will make a preview URL available, e.g.:

[https://daphne---beyond-translation-site-gwgx3f4hha-uc.a.run.app/](https://daphne---beyond-translation-site-gwgx3f4hha-uc.a.run.app/)
