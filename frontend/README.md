# Scaife Stack Frontend

front-end for the Scaife "Scaife Stack" prototype

This repository is part of the [Scaife Viewer](https://scaife-viewer.org) project, an open-source ecosystem for building rich online reading environments.

## Prerequisites
- [Node.js 12](https://nodejs.org/en/)
- [yarn](https://yarnpkg.com/en/docs/install)
- [vue-cli](https://cli.vuejs.org/guide/installation.html)

## Install project
```
yarn install
```

### Compiles and hot-reloads for development
```
yarn run serve
```

### Compiles and minifies for production
```
yarn run build
```

### Run your tests
```
yarn run test
```

### Lints and fixes files
```
yarn run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

**NOTE: Project initialization**

The following command was used to set up the initial project; it does not need to be ran again, but is provided here for reference on future projects:
```shell
vue create scaife-stack -d
```

### Routing to a local ATLAS server.
If you want to run an ATLAS server on your local machine then you can route all
requests to that address by overriding the graphql endpoint, like so:
```
export VUE_APP_ATLAS_GRAPHQL_ENDPOINT=http://localhost:8000/graphql/
```
