using System;
using System.Buffers;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Web;
using checker.net;
using checker.rnd;
using Newtonsoft.Json;

namespace checker.fs
{
    internal class FsChecker : IChecker
    {
        private Uri baseUri;
        public Task<string> Info() => Task.FromResult("vulns: 1\npublic_flag_description: filepath\n");

        public async Task Check(string host)
        {

        }

        public async Task<PutResult> Put(string host, string flagId, string flag, int vuln)
        {
            baseUri = GetBaseUri(host);
            var login1 = GenerateLogin();
            var password1 = GeneratePassword();
            var cookie1 = await RegisterOrLoginUser(login1, password1);
            var gotLogin = await WhoAmIUser(cookie1);
            if (gotLogin != login1)
                throw new CheckerException(ExitCode.MUMBLE, "Could not login user correctly");

            var (filePath, fileContent) = GenerateFilePathAndContent(flag);
            await UploadFile(filePath, fileContent, cookie1);
            filePath = "/" + login1 + filePath;

            return new PutResult
            {
                PublicFlagId = filePath,
                ChecksystemFlagId = flagId,
                Login1 = login1,
                Password1 = password1,
                FilePath = filePath
            };
        }

        public async Task Get(string host, PutResult state, string flag, int vuln)
        {
            //TODO sometimes not use cookie but login
	        var downloadedFileContent = await DownloadFile(state.FilePath, state.Cookie1);
	        if (!downloadedFileContent.Contains(flag))
		        throw new CheckerException(ExitCode.CORRUPT, "Can't find flag in downloaded content");
        }



        private async Task UploadFile(string filePath, string fileContent, string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.UploadFileAsync(ApiUpload, filePath, Encoding.UTF8.GetBytes(fileContent), NetworkOpTimeout, MaxHttpBodySize);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiUpload} failed: {result.StatusCode.ToReadableCode()}");
        }

        private async Task<string> DownloadFile(string filePath, string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiDownload + $"?file={HttpUtility.UrlEncode(filePath)}", contentTypeHeaders, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiDownload} failed: {result.StatusCode.ToReadableCode()}");

            return Encoding.UTF8.GetString(result.Body.ToArray());
        }

        private (string path, string content) GenerateFilePathAndContent(string flag)
        {
            string path = "";
            for (int i = 0; i < RndUtil.GetInt(1, 4); i++)
                path += $"/{RndText.RandomWord(8).RandomUpperCase().RandomLeet()}";
            path += "." + RndText.RandomWord(3).RandomLeet();

            var content = RndText.RandomText(RndUtil.GetInt(64, 512)).RandomUpperCase().RandomLeet().RandomUmlauts();
            if (flag != null)
            {
                content += " " + flag;
                if (RndUtil.Bool())
                    content += " " + RndText.RandomText(RndUtil.GetInt(64, 512)).RandomUpperCase().RandomLeet().RandomUmlauts();
            }

            return (path, content);
        }


        private async Task<string> RegisterOrLoginUser(string login, string password)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

            var result = await client.DoRequestAsync(HttpMethod.Post, ApiLogin, contentTypeHeaders, Encoding.UTF8.GetBytes($"username={HttpUtility.UrlEncode(login)}&password={HttpUtility.UrlEncode(password)}"), NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiLogin} failed: {result.StatusCode.ToReadableCode()}");

            return client.Cookies?.GetCookieHeader(baseUri);
        }

        private async Task<string> WhoAmIUser(string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiWhoAmI, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiWhoAmI} failed: {result.StatusCode.ToReadableCode()}");

            var match = Regex.Match(result.BodyAsString, "<h1>'(.+?)' logged in</h1>");
            if (!match.Success)
                throw new CheckerException(ExitCode.MUMBLE, $"get {ApiWhoAmI} returned wrong username");

            return match.Groups[1].Value;
        }


        private static string GenerateLogin()
        {
            var login = RndText.RandomWord(RndUtil.GetInt(4, 32)).RandomUpperCase().RandomLeet();
            return login;
        }

        private static string GeneratePassword()
        {
            return RndText.RandomText(RndUtil.GetInt(8, 16)).RandomLeet().RandomUpperCase();
        }





        private readonly Dictionary<string, string> contentTypeHeaders = new()
        {
            { "Content-Type", "application/x-www-form-urlencoded" }
        };

        private const string ApiPublicKey = "/publickey";
        private const string ApiLogin = "/login";
        private const string ApiUpload = "/upload";
        private const string ApiDownload = "/download";
        private const string ApiShare = "/share";
        private const string ApiAccess = "/access";
        private const string ApiWhoAmI = "/whoami";

        private const int MaxHttpBodySize = 32 * 1024;
        private const int NetworkOpTimeout = 8000;

        private const int Port = 7777;

        private static Uri GetBaseUri(string host) => new($"http://{host}:{Port}/");
    }
}
