using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using mp.Entities;
using Newtonsoft.Json;

namespace mp.Services
{
    public class OpenSearchService
    {
        private readonly IHttpContextAccessor httpContextAccessor;
        private readonly UserService userService;
        private readonly ElasticClient elasticClient;

        public OpenSearchService(IHttpContextAccessor httpContextAccessor, UserService userService, ElasticClient elasticClient)
        {
            this.httpContextAccessor = httpContextAccessor;
            this.userService = userService;
            this.elasticClient = elasticClient;
        }

        public async Task<string> IndexDocumentAsync(Document document, string routing = null)
        {
            return JsonConvert.DeserializeObject<IndexResponse>(await elasticClient.IndexAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), JsonConvert.SerializeObject(document), routing))?.Id;
        }

        public async Task<IEnumerable<Document>> SearchAsync(string queryString, int pageNum)
        {
            return JsonConvert.DeserializeObject<SearchResponse>(await elasticClient.SearchAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), queryString ?? "", pageNum * PageSize, PageSize))
                ?.Hits
                .Hits
                .Select(hit => hit?.Source?.CloneAndSetId(hit.Id));
        }

        //TODO copypaste
        public async Task<IEnumerable<Document>> SearchOrdersOfProductAsync(string productId, int pageNum)
        {
            return JsonConvert.DeserializeObject<SearchResponse>(await elasticClient.SearchOrdersOfProductAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), productId, pageNum * PageSize, PageSize))
                ?.Hits
                .Hits
                .Select(hit => hit?.Source?.CloneAndSetId(hit.Id));
        }

        //TODO check DLS works with get by id
        public async Task<Document> Get(string documentId)
        {
            var hit =  JsonConvert.DeserializeObject<Hit>(await elasticClient.GetAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), documentId));
            return hit?.Source?.CloneAndSetId(hit.Id);
        }

        private const int PageSize = 10;
    }

    class IndexResponse
    {
        [JsonProperty("_id")] public string Id;
    }

    class SearchResponse
    {
        [JsonProperty("hits")] public HitOuter Hits { get; set; }

        internal class HitOuter
        {
            [JsonProperty("hits")] public Hit[] Hits { get; set; }
        }
    }

    public class Hit
    {
        [JsonProperty("_id")] public string Id;
        [JsonProperty("_source")] public Document Source { get; set; }
    }
}