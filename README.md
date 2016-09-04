# YoutubeDL as a Web / REST server

Simple Web UI to queue downloads using the great [YoutubeDL](https://rg3.github.io/youtube-dl/)

![sample](static/sample.png)

It can also be used as a very simple REST api

## Run in Docker

```
docker run -d -p "5000:5000" -v ./downloads:/downloads/ franhp/youtubedl-web
```

## Using the API

```
curl -XPOST -d "url=$url" http://ip:5000/add/
```


