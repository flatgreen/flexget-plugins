# plugins for Flexget

## Getting started

- Download this [repository](https://github.com/flatgreen/flexget-plugins/archive/master.zip).
- unzip all files in the "good" [location](https://flexget.com/Plugins#third-party-plugins).
- check if all is for the best:
`flexget check`

## crawljob
This plugin (base make_html) create a .crawljob file for each accepted entry. This file (.crawljob) is for used with JDownloader2 and the folderwtach system.

The file name is 'title' and there is 'url' in the text file.

Configuration required:
```
path: folderwtach directory for the .crawljob files 

(ex : "C:\\Users\\flatgreen\\AppData\\Local\\JDownloader 2.0\\folderwatch")
````

Example:
```
crawljob:
    path: "{? jd2.watch ?}"
````


## dir_size
Set the dir_size about directory when the entries come from the filesystem input.

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
Download videos using YoutubeDL.

[Inspiration](https://github.com/z00nx/flexget-plugins/blob/master/youtubedl.py), [discussion](https://github.com/Flexget/Flexget/pull/65)

This plugin requires the [youtube-dl](https://github.com/rg3/youtube-dl) Python module. To install the Python module run: `pip install youtube-dl`

**Configuration:**

````
username:       Login with this account ID (option)
password:       Account password (option)
videopassword:  Video password (vimeo, smotri, youku)
format:         Video format code (default: best)
template:       Output filename template (default: '%(title)s-%(id)s.%(ext)s')
path:           Destination path (can be use with 'Set' plugin)
json:           (true/false) like youtube-dl option 'writeinfojson' without '.info' in filename
other_options:  all parameters youtube-dl can accept
                (see : https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py)


'template' and 'path' support Jinja2 templating on the input entry
````

Examples 1:
````
youtubedl:
    format: best
    template: {{ title }}.%(ext)s
    path: ~/downloads/
````

Example 2:
````
youtubedl:
    path: 'E:\--DL--\'
    other_options:
        writeinfojson: true
````

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