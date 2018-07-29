

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
To open wikipedia page go to URL http://localhost:8080/httptest/wikipedia_russia.html

## Run tests
Unittests ( Python *2.7*):
```
$ cd 05_automatization
$ python -m unittest httptest.py
```
Load testing (the server should be running):
```
$ ab -n 50000 -c 100 -s 60 -r http://localhost:8080/
This is ApacheBench, Version 2.3 <$Revision: 1706008 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   1.323 seconds
Complete requests:      50000
Failed requests:        50437
   (Connect: 0, Receive: 992, Length: 0, Exceptions: 49445)
Total transferred:      0 bytes
HTML transferred:       0 bytes
Requests per second:    37796.87 [#/sec] (mean)
Time per request:       2.646 [ms] (mean)
Time per request:       0.026 [ms] (mean, across all concurrent requests)
Transfer rate:          0.00 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    1   0.4      1       5
Processing:     0    1   1.9      1      47
Waiting:        0    0   0.0      0       0
Total:          0    3   2.0      3      47

Percentage of the requests served within a certain time (ms)
  50%      3
  66%      3
  75%      3
  80%      3
  90%      3
  95%      3
  98%      4
  99%      4
 100%     47 (longest request)

```

### Project Goals
The code is written for educational purposes.