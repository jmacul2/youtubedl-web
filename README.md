# YoutubeDL as a Web / REST server

Simple Web UI to queue downloads using the great [YoutubeDL](https://rg3.github.io/youtube-dl/)

![sample](static/sample.png)

It can also be used as a very simple REST api

## Configure

> cp youtubedl-web.yaml.example youtubedl-web

Modify the file to fit your needs.

Create multiple formats for downloading an audio only file or for selecting 
different video resolutions. You can also set a unique directory and output 
template for each format defined.


Read more about valid format configurations for youtube-dl [here](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#format-selection) and valid output templates [here](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#output-template).


## Run in Docker

> No longer working I believe...

I plan to create new docker files.

```
docker-compose up --build
```

## Using the API

```
curl -XPOST -d "url=$url" http://ip:5000/add/
```

```
curl -GET http://ip:5000/downloads
curl -GET http://ip:5000/downloads/format/<format>
curl -GET http://ip:5000/downloads/status/<status>
```

```
curl -XDELETE http://localho:5000/remove/<id>
```

```
curl -XPOST http://localho:5000/remove/<id>
```
