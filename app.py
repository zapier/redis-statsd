import logging
import os
import socket
import sys
import time

from redis.client import StrictRedis

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
STATSD_HOST = os.environ.get('STATSD_HOST', 'localhost')
STATSD_PORT = int(os.environ.get('STATSD_PORT', 8125))
STATSD_PREFIX = os.environ.get('STATSD_PREFIX', 'redis')
PERIOD = int(os.environ.get('PERIOD', 30))

VERBOSE = '-v' in sys.argv or os.environ.get('VERBOSE', '').lower() in ['true', 'yes']

logger = logging.getLogger()

if VERBOSE:
    handler = logging.StreamHandler()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s %(name)s %(levelname)s] %(message)s')
    handler.setFormatter(formatter)

logger.addHandler(handler)


GAUGES = {
    'blocked_clients': 'blocked_clients',
    'connected_clients': 'connected_clients',
    'instantaneous_ops_per_sec': 'instantaneous_ops_per_sec',
    'latest_fork_usec': 'latest_fork_usec',
    'mem_fragmentation_ratio': 'mem_fragmentation_ratio',
    'migrate_cached_sockets': 'migrate_cached_sockets',
    'pubsub_channels': 'pubsub_channels',
    'pubsub_patterns': 'pubsub_patterns',
    'uptime_in_seconds': 'uptime_in_seconds',
    'used_memory': 'used_memory',
    'used_memory_lua': 'used_memory_lua',
    'used_memory_peak': 'used_memory_peak',
    'used_memory_rss': 'used_memory_rss'
}

COUNTERS = {
    'evicted_keys': 'evicted_keys',
    'expired_keys': 'expired_keys',
    'keyspace_hits': 'keyspace_hits',
    'keyspace_misses': 'keyspace_misses',
    'rejected_connections': 'rejected_connections',
    'sync_full': 'sync_full',
    'sync_partial_err': 'sync_partial_err',
    'sync_partial_ok': 'sync_partial_ok',
    'total_commands_processed': 'total_commands_processed',
    'total_connections_received': 'total_connections_received'
}

KEYSPACE_COUNTERS = {
    'expires': 'expires'
}

KEYSPACE_GAUGES = {
    'avg_ttl': 'avg_ttl',
    'keys': 'keys'
}

last_seens = {}

def send_metric(out_sock, mkey, mtype, value):
    finalvalue = value

    if mtype == 'c':
        # For counters we will calculate our own deltas.
        if mkey in last_seens:
            # global finalvalue
            # calculate our deltas and don't go below 0
            finalvalue = max(0, value - last_seens[mkey])
        else:
            # We'll default to 0, since we don't want our first counter
            # to be some huge number.
            finalvalue = 0
        last_seens[mkey] = value

    met = '{}:{}|{}'.format(mkey, finalvalue, mtype)
    out_sock.sendto(met, (STATSD_HOST, STATSD_PORT))
    logger.debug('{}:{} = {}'.format(mtype, mkey, finalvalue))


def main():
    while True:
        try:
            run_once()
        except Exception as e:
            logger.exception(e)
            time.sleep(5)

def run_once():
    redis = StrictRedis(REDIS_HOST, REDIS_PORT)

    stats = redis.info()
    stats['keyspaces'] = {}

    for key in stats.keys():
        if key.startswith('db'):
            stats['keyspaces'][key] = stats[key]
            del stats[key]

    out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for g in GAUGES:
        if g in stats:
            send_metric(out_sock, '{}.{}'.format(STATSD_PREFIX, g), 'g', float(stats[g]))

    for c in COUNTERS:
        if c in stats:
            send_metric(out_sock, '{}.{}'.format(STATSD_PREFIX, c), 'c', float(stats[c]))

    for ks in stats['keyspaces']:
        for kc in KEYSPACE_COUNTERS:
            if kc in stats['keyspaces'][ks]:
                send_metric(out_sock, '{}.keyspace.{}'.format(
                    STATSD_PREFIX, kc), 'c',
                float(stats['keyspaces'][ks][kc]))

        for kg in KEYSPACE_GAUGES:
            if kg in stats['keyspaces'][ks]:
                send_metric(out_sock, '{}.keyspace.{}'.format(
                    STATSD_PREFIX, kg), 'g',
                    float(stats['keyspaces'][ks][kg]))

    out_sock.close()
    time.sleep(PERIOD)

if __name__ == '__main__':
    main()
