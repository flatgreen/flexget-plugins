# plugins for Flexget

## Getting started

- Download this [repository](https://github.com/flatgreen/flexget-plugins/archive/master.zip).
- unzip all files in the "good" [location](https://flexget.com/Plugins#third-party-plugins).
- check if all is for the best:
`flexget check`

## crawljob
This plugin (base make_html) create a .crawljob file for each accepted entry. This file (.crawljob) is for used with JDownloader2 and the folderwtach system.

The file name is 'title' and there is 'url' in the text file.

Configuration required: path

Examples:
```
crawljob:
  path: "{? jd2.watch ?}"
    
crawljob:    
  path: "C:\\Users\\flatgreen\\AppData\\Local\\JDownloader 2.0\\folderwatch"
```


## dir_size
Set the dir_size about directory when the entries come from the filesystem input. Value in bytes.

Example:

```
check_dir_size:
    filesystem:
    	path:
            - D:\Media\Incoming\series
        recursive: yes
        retrieve: dirs
    dir_size: yes
    if:
        - dir_size == 0: accept
	...
````

## sms_free_fr
Sends SMS notification through smsapi.free-mobile.fr . This is a french service.

Some [informations in french](https://www.freenews.fr/freenews-edition-nationale-299/free-mobile-170/nouvelle-option-notifications-par-sms-chez-free-mobile-14817).

Example:

````
sms_free_fr:
    user: your login (accepted format example: '12345678')
    password: <PASSWORD>
````
Full example:

````
notify:
    entries:
        via:
            - sms_free_fr:
                user: '{? free_sms.user ?}'
                password: '{? free_sms.password ?}'
````

## youtubedl

Download videos using youtube-dl or yt-dlp

This plugin requires the [youtube-dl](https://github.com/rg3/youtube-dl) or [yt-dlp](https://github.com/yt-dlp/yt-dlp) Python module.
To install the Python module run:
```bash
pip install youtube-dl
```
```bash
pip install yt-dlp
```

Examples with simple configuration:
```yaml
youtubedl: <path>   Destination folder path
```

**Advanced usages with properties configuration::**

```yaml
ytdl_name:      youtube dowloader (yt-dlp (default) or youtube-dl)
format:         Video format code (default : ytdl downloader default)
template:       Output filename template (default: '%(title)s-%(id)s.%(ext)s')
path:           Destination path (can be use with 'Set' plugin) - Required 
other_options:  all parameters from youtube-dl or yt-dlp params
```
'template' and 'path' support Jinja2 templating on the input entry

'other_options' see [youtube-dl](https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L141) or [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L197)

Example:
```yaml
youtubedl:
    ytdl_name: yt-dlp
    template: {{ title }}.%(ext)s
    path: ~/downloads/
```

Example:
```yaml
youtubedl:
    path: 'E:\--DL--\'
    format: '160/18'
    other_options:
        writeinfojson: true
```

Example with yt-dlp, extract audio::
```yaml
youtubedl:
   path: ~/dowload/
   format: bestaudio*
     other_options:
       postprocessors:
         - key: FFmpegExtractAudio
           preferredcodec: best
```

## log_info
Write a message (with jinja2 replacement) to the system logging with level=INFO for accepted entries.

Example:
````
log_info: a message for the log file !
````
Example:
````
log_info: 'download: {{ url }}'
````
