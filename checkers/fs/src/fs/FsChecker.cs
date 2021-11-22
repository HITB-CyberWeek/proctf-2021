using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace checker.fs
{
    internal class FsChecker : IChecker
    {
        private Uri baseUri;
        public Task<string> Info() => Task.FromResult("vulns: 1\npublic_flag_description: filepath\n");

        public async Task Check(string host)
        {
            throw new NotImplementedException();
        }

        public async Task<PutResult> Put(string host, string flagId, string flag, int vuln)
        {
            throw new NotImplementedException();
        }


        public async Task Get(string host, PutResult state, string flag, int vuln)
        {
            throw new NotImplementedException();
        }

        private readonly Dictionary<string, string> contentTypeHeaders = new()
        {
            { "Content-Type", "text/json" }
        };

        private const int MaxHttpBodySize = 512 * 1024;
        private const int NetworkOpTimeout = 8000;

        private const int Port = 7777;

        private static Uri GetBaseUri(string host) => new($"http://{host}:{Port}/");
    }
}
