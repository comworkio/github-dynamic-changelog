# Github Dynamic Changelog

A restful api which gives you the github changelog of a protected branch in real time.
Usefull to see what is deployed on your environments in a web dashboard.

This api is available as a ready to use docker image.

## Table of content

[[_TOC_]]

## Git repositories

* Main repo: https://gitlab.comwork.io/oss/github-dynamic-changelog
* Github mirror: https://github.com/idrissneumann/github-dynamic-changelog.git
* Gitlab mirror: https://gitlab.com/ineumann/github-dynamic-changelog.git

## Running with docker-compose

First create your `.env` file from the `.env.example`:

```shell
cp .env.example .env
```

Then replace the values (like the `GITHUB_ACCESS_TOKEN` with one of your own). Then:

```shell
$ docker-compose up
```

## Endpoints

### Healthcheck

```shell
$ curl localhost:8080/v1/health
{"status": "ok", "alive": true}
```

### Manifests

```shell
$ curl localhost:8080/v1/manifest 
{"version": "1.0", "sha": "1c7cb1f", "arch": "x86"}
```

### Generate the changelog

```shell
curl localhost:8080/v1/changelog -X POST -d '{"ref":"master", "org": "shippeo", "repo":"shippeo-deployments", "since":"2021-09-01T02:34:56-06:00","details":"true", "format":"text/markdown"}' -v
```

Note:
* `details` is not mandatory but if it's not defined, you'll have only the url of issues (you'll have also the title and the author otherwise)
* `format` supports also `text/csv` and `application/json` (which is the default value)
