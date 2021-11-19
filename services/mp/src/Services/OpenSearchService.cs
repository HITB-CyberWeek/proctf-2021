using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using Elasticsearch.Net;
using Microsoft.AspNetCore.Http;
using mp.Entities;
using Newtonsoft.Json;

namespace mp.Services
{
    public class OpenSearchService
    {
        private readonly IHttpContextAccessor httpContextAccessor;
        private readonly UserService userService;
        private readonly OpenSearchClient openSearchClient;

        public OpenSearchService(IHttpContextAccessor httpContextAccessor, UserService userService, OpenSearchClient openSearchClient)
        {
            this.httpContextAccessor = httpContextAccessor;
            this.userService = userService;
            this.openSearchClient = openSearchClient;
        }

        public async Task<string> IndexDocumentAsync(Document document, string routing = null)
        {
            return JsonConvert.DeserializeObject<IndexResponse>(await openSearchClient.IndexAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), JsonConvert.SerializeObject(document), routing))?.Id;
        }

        public async Task<IEnumerable<Document>> SearchAsync(string queryString, int pageNum)
        {
            return JsonConvert.DeserializeObject<SearchResponse>(await openSearchClient.SearchAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), queryString ?? "", pageNum * PageSize, PageSize))
                ?.Hits
                .Hits
                .Select(hit => hit?.Source?.CloneAndSetId(hit.Id));
        }

        //TODO copypaste
        public async Task<IEnumerable<Document>> SearchOrdersOfProductAsync(string productId, int pageNum)
        {
            return JsonConvert.DeserializeObject<SearchResponse>(await openSearchClient.SearchOrdersOfProductAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), productId, pageNum * PageSize, PageSize))
                ?.Hits
                .Hits
                .Select(hit => hit?.Source?.CloneAndSetId(hit.Id));
        }

        //TODO check DLS works with get by id
        public async Task<Document> TryGet(string documentId)
        {
	        Hit hit;
	        try
	        {
		        hit = JsonConvert.DeserializeObject<Hit>(await openSearchClient.GetAsync(httpContextAccessor.HttpContext?.User.FindCurrentUserId(), documentId));
            }
	        catch(ElasticsearchClientException e)
	        {
		        if(e.Response?.HttpStatusCode == (int?)HttpStatusCode.NotFound)
			        return null;
		        throw;
	        }
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