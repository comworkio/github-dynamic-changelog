# Github Dynamic Changelog

A restful api which gives you the github changelog of a protected branch in real time.
Usefull to see what is deployed on your environments in a web dashboard. The changelog can also be uploaded in an object storage bucket (i.e: Amazon S3 or Google Object Storage).

This api is available as a ready to use docker image.

## Table of content

[[_TOC_]]

## Git repositories

* Main repo: https://gitlab.comwork.io/oss/github-dynamic-changelog
* Github mirror: https://github.com/idrissneumann/github-dynamic-changelog.git
* Gitlab mirror: https://gitlab.com/ineumann/github-dynamic-changelog.git
* Bitbucket mirror: https://bitbucket.org/idrissneumann/github-dynamic-changelog.git
* Froggit mirror: https://lab.frogg.it/ineumann/github-dynamic-changelog.git

## Image on the dockerhub

The image is available and versioned here: https://hub.docker.com/r/comworkio/github-dynamic-changelog

## Test the api

Here's an available endpoint to test the api with public repositories: https://github-dynamic-changelog.comwork.io/

Example of results:

![github-dynamic-changelog](./images/github-dynamic-changelog.png)

You can see the "Endpoints" section below to get all the available endpoints.
## Running with docker-compose

First create your `.env` file from the `.env.example`:

```shell
cp .env.example .env
```

Then replace the values (like the `GITHUB_ACCESS_TOKEN` with one of your own). Then:

```shell
$ docker-compose up
```

If you want to test on a raspberrypi or any other ARM device, use this command instead:

```shell
$ docker-compose -f docker-compose-arm.yml up
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

#### Syntax of commit

In order to be able to provide the list of the issues by this API, your commits must follow this rule: put the issue reference in your commit's comment or body like that:

* `#12345`: if your issue `12345` is on the same repository as the updated code
* `#{orga}/{repo}/issues/12345`: if your issue isn't on the same repository as the updated code (juste copy/past the path of the issue provided by the github's issue url and write it behind a `#`)

If you're using something like [conventional commits](https://www.conventionalcommits.org), you can add the reference of the issue in the body of the commit:

```
chore(domain): add something like XXXXX in order to YYYYY

Issue #myorga/myrepo/issues/12345
```

This way, the message of your commits will directly be published on the issue's comments and this API will provide a more complete changelog containing the related issues (and not only the pull requests).

#### Changelog from protected branch

```shell
curl localhost:8080/v1/changelog -X POST -d '{"ref":"main", "org": "EbookFoundation", "repo":"free-programming-books", "since":"2022-01-01T02:34:56-06:00", "format":"text/markdown"}' -v
```

```shell
curl https://github-dynamic-changelog.comwork.io/v1/changelog  -X POST -d '{"ref":"main", "org": "EbookFoundation", "repo":"free-programming-books", "since":"2022-01-01T02:34:56-06:00", "format":"text/markdown"}' -v
```

Note:
* `format` supports also `text/csv` and `application/json` (which is the default value)
* `filter_author` is not required but if it's defined, it will filter all the pull requests opened by a login matching this value
* `filter_message` is not required but if it's defined, it will filter the commit which have their messages matching this value
* `only_prs` is not required but if it's defined, no issues will be searched and the changelog will only contained the pull requests
* `write_bucket` is not required but if it's defined with `true`, the changelog will be upload in an object storage bucket (you'll have to define the following environment variables: `BUCKET_ENDPOINT`, `BUCKET_NAME`, `BUCKET_REGION`, `BUCKET_ACCESS_KEY`, `BUCKET_SECRET_KEY`)

#### Changelog from commit

```shell
curl localhost:8080/v1/changelog/sha -X POST -d '{"sha":"0b318f6381cacfb9c79b332d7b256749f13da668", "org": "EbookFoundation", "repo":"free-programming-books", "format":"text/markdown"}' -v
```

```shell
curl https://github-dynamic-changelog.comwork.io/v1/changelog/sha -X POST -d '{"sha":"0b318f6381cacfb9c79b332d7b256749f13da668", "org": "EbookFoundation", "repo":"free-programming-books", "format":"text/markdown"}' -v
```

Note:
* `format` supports also `text/csv` and `application/json` (which is the default value)
* `filter_author` is not required but if it's defined, it will filter all the pull requests opened by a login matching this value
* `filter_message` is not required but if it's defined, it will filter the commit which have their messages matching this value
* `only_prs` is not required but if it's defined, no issues will be searched and the changelog will only contained the pull requests
* `write_bucket` is not required but if it's defined with `true`, the changelog will be upload in an object storage bucket (you'll have to define the following environment variables: `BUCKET_ENDPOINT`, `BUCKET_NAME`, `BUCKET_REGION`, `BUCKET_ACCESS_KEY`, `BUCKET_SECRET_KEY`)

### Update the issues associated to a given pull request

Update the issues associated to a given pull request with the target branch (that correspond to an environment).

```shell
curl -X POST "http://localhost:8080/v1/label" -d '{"pr_id":"2648", "org": "idrissneumann", "repo":"shmwrapper"}'
```

Note:
* `label` is not required, if it's not defined, the pull request target branch will be taken as the label to add to the issues
* if you want to change the label color, you might have to create the wanted label to github with the wanted color first
