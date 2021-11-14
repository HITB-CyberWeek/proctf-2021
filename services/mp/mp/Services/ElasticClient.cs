using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Elasticsearch.Net;
using mp.Entities;
using mp.Models.Searchable;
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
                Serialize(document),
                new IndexRequestParameters
                {
                    Routing = routing,
                    RequestConfiguration = new RequestConfiguration { Headers = new() { { "Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(userId)}" } } }
                });
            return response.Body;
        }

        public async Task<string> SearchOrdersOfProduct(string userId, string parentId, int from = 0, int size = 10)
        {
            var request = $@"
                {{
                    ""from"": ""{from}"",
                    ""size"": ""{size}"",
                    ""query"": {{
                        ""has_parent"": {{
                            ""parent_type"": ""{JoinField.ProductRelationName}"",
                            ""query"": {{
                                ""term"": {{
                                    ""_id"": ""{Escape(parentId)}""
                                }}
                            }}
                        }}
                    }}
                }}";

            var response = await elasticLowLevelClient.SearchAsync<StringResponse>(indexName,
                Serialize(request),
                new SearchRequestParameters
                {
                    RequestConfiguration = new RequestConfiguration { Headers = new() { { "Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(userId)}" } } }
                });
            return response.Body;
        }

        public async Task<string> SearchAsync(string userId, string queryString, int from = 0, int size = 10)
        {
            var request = $@"
                {{
                    ""from"": ""{from}"",
                    ""size"": ""{size}"",
                    ""query"": {{
                        ""bool"": {{
                            ""must"":[
                                {{
                                    ""query_string"": {{
                                        ""query"": ""{Escape(queryString)}""
                                    }}
                                }}
                            ]
                        }}
                    }}
                }}";

            var response = await elasticLowLevelClient.SearchAsync<StringResponse>(indexName,
                Serialize(request),
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

        private string Escape(string s)
        {
            return s?.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        private const string KEY_PATH = @"..\opensearch\key.pem";

        private string CreateOpenSearchJwtTokenManually(string userId)
        {
            var headerEncoded = EncodeB64(new { alg = "RS256", typ = "JWT" }).TrimEnd('=');
            var bodyEncoded = EncodeB64(new { sub = userId, roles = "user_data" }).TrimEnd('=');
            
            using var rsa = RSA.Create();
            rsa.ImportFromPem(File.ReadAllText(KEY_PATH));
            var headerAndBodyBytes = Serialize($"{headerEncoded}.{bodyEncoded}");
            var signatureBytes = rsa.SignData(headerAndBodyBytes, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
            var signatureEncoded = Microsoft.AspNetCore.WebUtilities.WebEncoders.Base64UrlEncode(signatureBytes);

            return $"{headerEncoded}.{bodyEncoded}.{signatureEncoded}";
        }

        private string EncodeB64(object o)
        {
            return Microsoft.AspNetCore.WebUtilities.WebEncoders.Base64UrlEncode(Serialize(JsonConvert.SerializeObject(o, Formatting.Indented)));
        }

        private byte[] Serialize(string s)
        {
            return Encoding.GetEncoding(1251).GetBytes(s);
        }
    }
}