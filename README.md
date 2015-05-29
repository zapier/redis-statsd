# redis-statsd

Based on https://github.com/keenlabs/redis-statsd, `redis-statsd` is a small
Python script which pipes Redis statistics (as reported by `INFO`) into StatsD.

## Usage

```bash
$ docker build -t redis-statsd .
$ docker run -e REDIS_HOST=10.0.0.1 -e STATSD_HOST=10.0.0.10 redis-statsd
```

## Available Environment Variables

* `REDIS_HOST`: Redis hostname/IP (default: `localhost`)
* `REDIS_PORT`: Redis port (default: `6379`)
* `STATSD_HOST`: StatsD hostname/IP (default: `localhost`)
* `STATSD_PORT`: StatsD port (default: `8125`)
* `PERIOD`: Polling period in second (default: `30`)
* `VERBOSE`: Print metrics to stdout (default: `false`)
