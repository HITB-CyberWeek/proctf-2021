using System;
using System.Threading.Tasks;
using IO.Swagger.Api;
using IO.Swagger.Model;

namespace checker.mp
{
	internal class MpChecker : IChecker
	{
		public Task<string> Info() => Task.FromResult("vulns: 1\npublic_flag_description: order id\n");

		public async Task Check(string host)
        {
            var api = new UsersApi(GetBaseUri(host));
            var result = api.UsersRegisterPostWithHttpInfo(new UserModel {Login = "test", Password = "test"});

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

		private const int Port = 1117;

		private static string GetBaseUri(string host) => $"http://{host}:{Port}/";
    }
}
