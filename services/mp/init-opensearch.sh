#!/bin/sh

curl --retry 60 -f --retry-all-errors --retry-delay 1 -v -XPUT -H'Content-Type:application/json' -H'Authorization: Basic YWRtaW46RDBuVG4wRzAxY3I=' http://opensearch-node1:9200/mp -d'
{
  "settings": {
      "index": {
        "number_of_shards": "1",
        "number_of_replicas": "0"
      }
    },
    "mappings": {
      "dynamic": "strict",
      "properties": {
        "id": {
          "type": "keyword"
        },
        "join_field": {
          "type": "join",
          "eager_global_ordinals": true,
          "relations": {
            "product": "order"
          }
        },
        "dt": {
          "type": "date"
        },
        "product_name": {
          "type": "text"
        },
        "text": {
          "type": "text"
        },
        "readable_by": {
          "type": "keyword"
        },
        "created_by": {
          "type": "keyword"
        }
      }
    }
}'

curl --retry 60 -f --retry-all-errors --retry-delay 1 -v -XPUT -H'Content-Type:application/json' -H'Authorization: Basic YWRtaW46RDBuVG4wRzAxY3I=' http://opensearch-node1:9200/_plugins/_security/api/roles/user_data -d'
{
  "cluster_permissions": [
  ],
  "index_permissions": [{
    "index_patterns": [
      "mp*"
    ],
    "dls": "{\"bool\":{\"should\":[{\"term\": { \"readable_by\": \"${user.name}\"}},{\"term\": { \"join_field\": \"product\"}}]} }",
    "allowed_actions": [
      "read", "index"
    ]
  }]
}'

curl --retry 60 -f --retry-all-errors --retry-delay 1 -v -XPUT -H'Content-Type:application/json' -H'Authorization: Basic YWRtaW46RDBuVG4wRzAxY3I=' http://opensearch-node1:9200/_plugins/_security/api/rolesmapping/user_data -d'
{
  "backend_roles" : [ "user_data" ]
}'
