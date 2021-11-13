using System;
using System.Buffers.Text;
using System.Collections.Specialized;
using System.IdentityModel.Tokens.Jwt;
using System.IO;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Elasticsearch.Net;
using Microsoft.IdentityModel.Tokens;
using mp.Entities;
using Newtonsoft.Json;

namespace mp
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

        public async Task<string> SearchAsync(User user, string queryString, int from = 0, int size = 10)
        {
            var request = $@"
                {{
                    ""from"": ""{from}"",
                    ""size"": ""{size}"",
                    ""query"": {{
                        ""query_string"": {{
                            ""default_field"" : ""text"",
                            ""query"": ""{Escape(queryString)}""
                        }}
                    }}
                }}";

            var response = await elasticLowLevelClient.SearchAsync<StringResponse>(indexName,
                Serialize(request),
                new SearchRequestParameters
                {
                    QueryString = {{"pretty", "true"}},
                    RequestConfiguration = new RequestConfiguration {Headers = new () {{"Authorization", $"Bearer {CreateOpenSearchJwtTokenManually(user)}"}}}
                });
            return response.Body;
        }

        private string Escape(string s)
        {
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        private const string TEMP_KEY_PATH = @"..\opensearch\key.pem";
        private string CreateOpenSearchJwtToken(User user)
        {
            using var rsa = RSA.Create();
            rsa.ImportFromPem(File.ReadAllText(TEMP_KEY_PATH));
            var tokenDescriptor = new SecurityTokenDescriptor
            {
                Subject = new ClaimsIdentity(new[]
                {
                    new Claim(JwtRegisteredClaimNames.Sub, user.Login),
                    new Claim("roles", "user_data")
                }),
                SigningCredentials = new SigningCredentials(new RsaSecurityKey(rsa), SecurityAlgorithms.RsaSha256)
            };

            var handler = new JwtSecurityTokenHandler();
            var result = handler.CreateEncodedJwt(tokenDescriptor);
            return result;
        }

        private string CreateOpenSearchJwtTokenManually(User user)
        {
            var headerEncoded = EncodeB64(new { alg = "RS256", typ = "JWT" }).TrimEnd('=');
            var bodyEncoded = EncodeB64(new { sub = user.Login, roles = "user_data" }).TrimEnd('=');
            
            using var rsa = RSA.Create();
            rsa.ImportFromPem(File.ReadAllText(TEMP_KEY_PATH));
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