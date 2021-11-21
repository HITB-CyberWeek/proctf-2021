using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using checker.net;
using checker.rnd;
using Newtonsoft.Json;

namespace checker.mp
{
	internal class MpChecker : IChecker
	{
        private Uri baseUri;
        public Task<string> Info() => Task.FromResult("vulns: 1\npublic_flag_description: order id\n");

		public async Task Check(string host)
        {
            // var api = new UsersApi(GetBaseUri(host));
            // var result = api.UsersRegisterPostWithHttpInfo(new UserModel {Login = "test", Password = "test"});

            throw new NotImplementedException();
        }

		public async Task<PutResult> Put(string host, string flagId, string flag, int vuln)
		{
            baseUri = GetBaseUri(host);

            var user1 = new UserModel { Login = GenerateLogin(), Password = GeneratePassword() };
            await RegisterUser(user1);
            var cookie1 = (await LoginUser(user1))?.GetCookieHeader(baseUri);

            var product = new ProductModelPut
            {
                Name = RndText.RandomWord(RndUtil.GetInt(16, 32)).RandomUpperCase().RandomLeet(),
                Description = GenerateProductDescription()
            };
            var productId = await CreateProduct(product, cookie1);
            //NOTE give time for document to become searchable
            await Task.Delay(1500);

            var gotProduct = await GetProduct(productId, cookie1);

            if(gotProduct?.Name != product.Name || gotProduct?.Description != product.Description || gotProduct?.Id != productId)
                throw new CheckerException(ExitCode.MUMBLE, "Got modified product");

            await Task.Delay(new Random().Next(200, 1000));
            var user2 = new UserModel { Login = GenerateLogin(), Password = GeneratePassword() };
            await RegisterUser(user2);
            var cookie2 = (await LoginUser(user2))?.GetCookieHeader(baseUri);

            var products = await SearchProducts(RndUtil.Bool() ? product.Name : product.Description, cookie2);

            //TODO support paging
            var found = products.FirstOrDefault(p => p.Id == productId);
            if(found == null)
                throw new CheckerException(ExitCode.MUMBLE, "Can't find just created product");

            var publicFlagId = Guid.NewGuid().ToString("N");
            var order = new OrderModelPut
            {
                ProductId = found.Id,
                Description = GenerateOrderText(flagId, publicFlagId, flag)
            };
            var orderId = await CreateOrder(order, cookie1);

            return new PutResult
            {
                PublicFlagId = publicFlagId,
                ChecksystemFlagId = flagId,
                Login1 = user1.Login,
                Password1 = user1.Password,
                Cookie1 = cookie1,
                Login2 = user2.Login,
                Password2 = user2.Password,
                Cookie2 = cookie2,
                ProductId = productId,
                OrderId = orderId
            };
        }


        public async Task Get(string host, PutResult state, string flag, int vuln)
		{
            throw new NotImplementedException();
        }

        private async Task<string> CreateOrder(OrderModelPut order, string cookie)
        {
            await Console.Error.WriteLineAsync($"Creating order {JsonConvert.SerializeObject(order)}");
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookie);

            var result = await client.DoRequestAsync(HttpMethod.Put, ApiOrdersCreate, contentTypeHeaders, Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(order)), NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"put {ApiOrdersCreate} failed: {result.StatusCode.ToReadableCode()}");

            var orderId = result.BodyAsString;
            await Console.Error.WriteLineAsync($"Got order id {orderId}");
            return orderId;
        }

        private string GenerateOrderText(string checksystemFlagId, string randomGuid, string flag)
        {
            var text = RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            text = text + " " + checksystemFlagId;

            if (RndUtil.GetInt(0, 3) == 0) text += ", " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 2) == 0) text += ", " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 2) == 0) text += ". " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 3) == 0) text += "; " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();

            text =  text + " " + flag;
            if (RndUtil.GetInt(0, 3) == 0) text += ", " + RndText.RandomText(32).RandomUpperCase();
            text += $" v{randomGuid}";
            text += $" (it's for {RndUtil.Choice("my mom", "my dad", "me", "my brother", "my sister")})";
            return text;
        }

        private static string GenerateProductDescription()
        {
            var text = RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            if (RndUtil.GetInt(0, 3) == 0) text += ", " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 2) == 0) text += ", " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 2) == 0) text += ". " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 3) == 0) text += "; " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            return text;
        }

        private static string GenerateLogin()
        {
            var login = RndText.RandomWord(RndUtil.GetInt(10, 32)).RandomUpperCase().RandomLeet();
            if (RndUtil.GetInt(0, 10) == 0) login += " " + RndText.RandomWord(RndUtil.GetInt(10, 32)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 10) == 0) login += ", " + RndText.RandomWord(RndUtil.GetInt(10, 32)).RandomUpperCase().RandomLeet();
            return login;
        }

        private static string GeneratePassword()
        {
            return RndText.RandomText(RndUtil.GetInt(8, 16)).RandomLeet().RandomUmlauts().RandomUpperCase();
        }

        private async Task RegisterUser(UserModel user)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

            var result = await client.DoRequestAsync(HttpMethod.Post, ApiRegister, contentTypeHeaders, Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(user)), NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiRegister} failed: {result.StatusCode.ToReadableCode()}");
        }

        private async Task<CookieContainer> LoginUser(UserModel user)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

            var result = await client.DoRequestAsync(HttpMethod.Post, ApiLogin, contentTypeHeaders, Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(user)), NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiLogin} failed: {result.StatusCode.ToReadableCode()}");

            return client.Cookies;
        }

        private async Task<IEnumerable<ProductModel>> SearchProducts(string text, string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiProductsSearch + $"?query={text}", contentTypeHeaders, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiProductsSearch} failed: {result.StatusCode.ToReadableCode()}");

            var resultString = result.BodyAsString;
            try
            {
                return JsonConvert.DeserializeObject<IEnumerable<ProductModel>>(resultString);
            }
            catch (Exception e)
            {
                await Console.Error.WriteLineAsync($"Failed to deserialize JSON of products '{resultString}' found by query '{text}': {e}");
                throw new CheckerException(ExitCode.MUMBLE, $"Failed to deserialize JSON from {ApiProductsSearch}");
            }
        }

        private async Task<ProductModel> GetProduct(string productId, string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiProductsGet + productId, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiProductsGet} failed: {result.StatusCode.ToReadableCode()}");

            var resultString = result.BodyAsString;
            try
            {
                return JsonConvert.DeserializeObject<ProductModel>(resultString);
            }
            catch(Exception e)
            {
                await Console.Error.WriteLineAsync($"Failed to deserialize JSON of product '{productId}' from '{resultString}': {e}");
                throw new CheckerException(ExitCode.MUMBLE, $"Failed to deserialize JSON from {ApiProductsGet}");
            }
        }

        private async Task<string> CreateProduct(ProductModelPut product, string cookie)
        {
            await Console.Error.WriteLineAsync($"Creating product {JsonConvert.SerializeObject(product)}");
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookie);

            var result = await client.DoRequestAsync(HttpMethod.Put, ApiProductsCreate, contentTypeHeaders, Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(product)), NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"put {ApiProductsCreate} failed: {result.StatusCode.ToReadableCode()}");

            var productId = result.BodyAsString;
            await Console.Error.WriteLineAsync($"Got product id {productId}");
            return productId;
        }


        private readonly Dictionary<string, string> contentTypeHeaders = new()
        {
            {"Content-Type", "text/json"}
        };

        private const string ApiRegister = "/Users/register";
        private const string ApiLogin = "/Users/login";

        private const string ApiProductsCreate = "/api/Products/create";
        private const string ApiProductsSearch = "/api/Products/search";
        private const string ApiProductsGet = "/api/Products/";

        private const string ApiOrdersCreate = "/api/Orders/create";
        private const string ApiOrdersSearchForMyProduct = "/api/Orders/searchForMyProduct";
        private const string ApiOrdersSearch = "/api/Orders/search";
        private const string ApiOrdersGet = "/api/Orders/";

        private const int MaxHttpBodySize = 512 * 1024;
        private const int NetworkOpTimeout = 8000;

        private const int Port = 54843;

        private static Uri GetBaseUri(string host) => new($"http://{host}:{Port}/");
    }
}
