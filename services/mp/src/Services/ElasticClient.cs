using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Elasticsearch.Net;
using mp.Entities;
using Newtonsoft.Json;

namespace mp.Services
{
    public class ElasticClient
    {
        private readonly ElasticLowLevelClient elasticLowLevelClient;
        private readonly string indexName;

        public ElasticClient(ElasticLowLevelClient elasticLowLevelClient, string indexName)
        {
            this.elasticLowLevelClient = elasticLowLevelClient;
            this.indexName = indexName;
        }

        public async Task<string> IndexAsync(string userId, string document, string routing = null)
        {
            var response = await elasticLowLevelClient.IndexAsync<StringResponse>(indexName, 
                SerializeString(document),
                new IndexRequestParameters
                {
                    Routing = routing,
                    RequestConfiguration = new RequestConfiguration { Headers = new() { { "Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(userId)}" } } }
                });
            return response.Body;
        }

        public async Task<string> SearchOrdersOfProduct(string userId, string parentId, int from, int size)
        {
            var request = JsonConvert.SerializeObject(new
                {
                    from = from,
                    size = size,
                    query = new
                    {
                        has_parent = new
                        {
                            parent_type = JoinField.ProductRelationName,
                            query = new
                            {
                                term = new
                                {
                                    _id = parentId
                                }
                            }
                        }
                    }
                }
            );

            var response = await elasticLowLevelClient.SearchAsync<StringResponse>(indexName,
                SerializeString(request),
                new SearchRequestParameters
                {
                    RequestConfiguration = new RequestConfiguration { Headers = new() { { "Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(userId)}" } } }
                });
            return response.Body;
        }

        public async Task<string> SearchAsync(string userId, string queryString, int from, int size)
        {
            var request = JsonConvert.SerializeObject(new
                {
                    from = from,
                    size = size,
                    query = new
                    {
                        @bool = new
                        {
                            must = new object[]
                            {
                                new
                                {
                                    range = new
                                    {
                                        dt = new
                                        {
                                            gte = "now-1d"
                                        }
                                    }
                                },
                                new
                                {
                                    query_string = new
                                    {
                                        fields = new []
                                        {
                                            "product_name", "text", "created_by"
                                        },
                                        query = queryString
                                    }
                                }
                            }
                        }
                    }
                }
            );

            var response = await elasticLowLevelClient.SearchAsync<StringResponse>(indexName,
                SerializeString(request),
                new SearchRequestParameters
                {
                    RequestConfiguration = new RequestConfiguration {Headers = new () {{"Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(userId)}"}}}
                });
            return response.Body;
        }

        public async Task<string> GetAsync(string userId, string documentId)
        {
            var response = await elasticLowLevelClient.GetAsync<StringResponse>(indexName, documentId,
                new GetRequestParameters
                {
                    RequestConfiguration = new RequestConfiguration {Headers = new() {{"Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(userId)}"}}}
                });
            return response.Body;
        }

        private const string KEY_PATH = @"..\opensearch\key.pem";

        private string CreateOpenSearchJwtTokenManually(string userId)
        {
            var headerEncoded = EncodeB64(new { alg = "RS256", typ = "JWT" }).TrimEnd('=');
            var bodyEncoded = EncodeB64(new { sub = userId, roles = "user_data" }).TrimEnd('=');
            
            using var rsa = RSA.Create();
            rsa.ImportFromPem(File.ReadAllText(KEY_PATH));
            var headerAndBodyBytes = SerializeString($"{headerEncoded}.{bodyEncoded}");
            var signatureBytes = rsa.SignData(headerAndBodyBytes, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
            var signatureEncoded = Microsoft.AspNetCore.WebUtilities.WebEncoders.Base64UrlEncode(signatureBytes);

            return $"{headerEncoded}.{bodyEncoded}.{signatureEncoded}";
        }

        private byte[] SerializeString(string s)
        {
            var result = Encoding.GetEncoding(1251).GetBytes(s);
            return result;
        }

        private string EncodeB64(object o)
        {
            return Microsoft.AspNetCore.WebUtilities.WebEncoders.Base64UrlEncode(SerializeString(JsonConvert.SerializeObject(o, Formatting.Indented)));
        }
    }
}