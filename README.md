# YoutubeDL as a Web / REST server

Simple Web UI to queue downloads using the great [YoutubeDL](https://rg3.github.io/youtube-dl/)

![sample](static/sample.png)

It can also be used as a very simple REST api

## Configure Formats

In `app.py` there is a dictionary that can be populated with format strings you want to define.

Read more about valid format strings from the [youtube-dl docs](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#format-selection).

## Run in Docker

> I haven't set up Docker myself yet. You would have to build first then you can run locally.

```
docker run -d -p "5000:5000" -v ./downloads:/downloads/ ??????/youtubedl-web
```

## Using the API

```
curl -XPOST -d "url=$url" http://ip:5000/add/
```


