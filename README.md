
# Simplest web server
Yet another simple server which is able to:
1) Handle `GET` and `HEAD` requests
2) Response with 200, 400, 403 and 405 status codes
3) Read `index.html` file as default directory file
4) Handle URLs with `%XX` symbols

The server is based on *thread pool* architecture so you can specify number of thread by `-w` option.
To specify servers's root directory use an option `-r`

## How to run server
It developed and tested on Python *3.6*. So this version should be installed in your system.
```
$ git clone https://github.com/ligain/05_automatization
$ cd 05_automatization
$ python3 httpd.py -w 2 -r path/to/document/root
[2018.07.19 22:18:23] I Start worker to serve on host: 127.0.0.1, port: 8080
[2018.07.19 22:18:23] I Start worker to serve on host: 127.0.0.1, port: 8080
[2018.07.19 22:18:23] I Start worker to serve on host: 127.0.0.1, port: 8080
```
## Run tests
Unittests:
```
$ cd 05_automatization
$ python -m unittest httptest.py
```
Load testing (the server should be running):
```
$ ab -n 50000 -c 100 -r http://127.0.0.1:8080/
```

### Project Goals
The code is written for educational purposes. 
