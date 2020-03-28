# YoutubeDL as a Web / REST server

Simple Web UI to queue downloads using the great [YoutubeDL](https://rg3.github.io/youtube-dl/)

![sample](static/sample.png)

It can also be used as a very simple REST api

## Configure

> cp .env.template .env

Modify the file to fit your needs.

Create formats to download just an audio only file or for selecting 
specific video resolutions/formats.

> python manage.py recreate-db
> python manage.py format add

Read more about valid format configurations for youtube-dl [here](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#format-selection) and valid output templates [here](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#output-template).

## Start

In one terminal start the webserver process

> python manange.py run

In a second terminal start the download task process

> python manage.py celery-worker

## Multiple Workers on the Network

Create a network drive to store downloaded files. On each worker mount the 
storage in the local `./downloads` directory so that all workers can save to it.


## Using the API

```
curl -XPOST -d "url=$url" http://ip:5000/api/add
```

```
curl -GET http://ip:5000/api/downloads
```

```
curl -XDELETE http://ip:5000/api/remove/<id>
```

```
curl -XPOST http://ip:5000/api/restart/<id>
```

## Roadmap

- [x] Extended API
- [x] Download Format Selection
- [ ] Download hours (I have slow internet connection)
- [x] Download directory selection
- [x] Playlist or single video download
- [ ] Filter downloads by status/path
- [ ] Proper Docker deployment
- [ ] Alert on frontend when `youtube-dl` fails (likely needs updating)
- [ ] Download file from browser
- [ ] Watch output directories for removed files then remove item from store

### Development Ideas

I am not sure if these ideas should be built into this project or if 
another project should be started that uses this project simply as 
an API for downloading. Perhaps an RSS feed already exists that 
can be read from or use Youtube API... but that seems overkill.

- [ ] Watch a public youtube playlist for changes then download
- [ ] Watch youtube channel for updates and then download
- [ ] Extend playlist download selection [see here](https://askubuntu.com/questions/1074697/how-can-i-download-part-of-a-playlist-from-youtube-with-youtube-dl)