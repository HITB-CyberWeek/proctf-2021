using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Web;
using checker.net;
using checker.rnd;
using Newtonsoft.Json;

namespace checker.mp
{
	internal class MpChecker : IChecker
	{
        private Uri baseUri;
        public Task<string> Info() => Task.FromResult("vulns: 1\npublic_flag_description: Flag ID is in the order description, flag is also there\n");

		public async Task Check(string host)
        {
            baseUri = GetBaseUri(host);

            var user1 = new UserModel { Login = GenerateLogin(), Password = GeneratePassword() };
            await RegisterUser(user1);
            var cookie1 = (await LoginUser(user1))?.GetCookieHeader(baseUri);
            var gotUsername =await  WhoAmIUser(cookie1);
            if(gotUsername != user1.Login)
                throw new CheckerException(ExitCode.MUMBLE, "Could not login user correctly");
            //TODO do it several times in parallel

            var user2 = new UserModel { Login = GenerateLogin(), Password = GeneratePassword() };
            await RegisterUser(user2);
            var cookie2 = (await LoginUser(user2))?.GetCookieHeader(baseUri);

            var product = new ProductModelPut
            {
                Name = RndText.RandomWord(RndUtil.GetInt(16, 32)).RandomUpperCase().RandomLeet(),
                Description = GenerateProductDescription()
            };
            var productId = await CreateProduct(product, cookie1);
            //NOTE give time for document to become searchable
            await Task.Delay(1500);

            var gotProduct = await GetProduct(productId, cookie2);
            if (gotProduct?.Name != product.Name || gotProduct?.Description != product.Description || gotProduct?.Id != productId)
                throw new CheckerException(ExitCode.MUMBLE, "Got modified or invalid product");

            var products = await SearchProducts(RndUtil.Bool() ? product.Name : product.Description, RndUtil.Choice(cookie1, cookie2));
            var foundProduct = products?.FirstOrDefault(p => p.Id == productId);
            if (foundProduct == null)
                throw new CheckerException(ExitCode.MUMBLE, "Can't find just created product");

            var order = new OrderModelPut
            {
                ProductId = foundProduct.Id,
                Description = GenerateOrderText()
            };
            var orderId = await CreateOrder(order, cookie2);

            await Task.Delay(1500);

            var gotOrder = await GetOrder(orderId, RndUtil.Choice(cookie1, cookie2));
            if (gotOrder?.Description != order.Description || gotOrder?.ProductId != order.ProductId || gotOrder?.Id != orderId)
                throw new CheckerException(ExitCode.MUMBLE, "Got modified or invalid order");

            var foundOrders = await SearchOrders(order.Description, RndUtil.Choice(cookie1, cookie2));
            var foundOrder  = foundOrders?.FirstOrDefault(o => o.Id == orderId);
            if (foundOrder?.Description != order.Description || foundOrder?.ProductId != order.ProductId || foundOrder?.Id != orderId)
                throw new CheckerException(ExitCode.MUMBLE, "Can't find just created order");

            //TODO randomly use cookies or login/pass
            var orders = await SearchOrdersOfProduct(productId, RndUtil.Choice(cookie1, cookie2));
            var foundOrderOfProduct = orders?.FirstOrDefault(o => o.Id == orderId && o.ProductId == order.ProductId && o.Description == order.Description);
            if (foundOrderOfProduct == null)
                throw new CheckerException(ExitCode.MUMBLE, "Can't find just created order by productId");
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

            var user2 = new UserModel { Login = GenerateLogin(), Password = GeneratePassword() };
            await RegisterUser(user2);
            var cookie2 = (await LoginUser(user2))?.GetCookieHeader(baseUri);

            var products = await SearchProducts(RndUtil.Bool() ? product.Name : product.Description, RndUtil.Choice(cookie1, cookie2));
            var foundProduct = products?.FirstOrDefault(p => p.Id == productId);
            if(foundProduct == null)
                throw new CheckerException(ExitCode.MUMBLE, "Can't find just created product");

            var publicFlagId = Guid.NewGuid().ToString("N");
            var order = new OrderModelPut
            {
                ProductId = foundProduct.Id,
                Description = GenerateOrderText(flag, flagId, publicFlagId)
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
            baseUri = GetBaseUri(host);

            //NOTE give time for document to become searchable
            await Task.Delay(1500);

            //TODO randomly use cookies or login/pass
            var orders = await SearchOrdersOfProduct(state.ProductId, state.Cookie1);
            var order = orders?.FirstOrDefault(o => o.Description.Contains(flag));

            //TODO support paging

            //TODO is it ok to disclouse public flag id here?
            if(order == null)
                //TODO maybe it is ok to disclouse public flag id here?
                // throw new CheckerException(ExitCode.CORRUPT, $"Can't find flag with id '{state.PublicFlagId}'");
                throw new CheckerException(ExitCode.CORRUPT, $"Can't find flag");

        }

        private string GenerateSuffixForPOW(string prefix)
        {
	        prefix += "&r=00000";
	        var buffer = Encoding.ASCII.GetBytes(prefix);
	        for(byte c1 = 0x61; c1 < 0x7B; c1++)
	        {
		        buffer[buffer.Length - 5] = c1;
                for (byte c2 = 0x61; c2 < 0x7B; c2++)
		        {
			        buffer[buffer.Length - 4] = c2;
                    for (byte c3 = 0x61; c3 < 0x7B; c3++)
			        {
				        buffer[buffer.Length - 3] = c3;
                        for (byte c4 = 0x61; c4 < 0x7B; c4++)
				        {
					        buffer[buffer.Length - 2] = c4;
                            for (byte c5 = 0x61; c5 < 0x7B; c5++)
					        {
						        buffer[buffer.Length - 1] = c5;
						        var sha512 = new SHA512Managed().ComputeHash(buffer);
						        if(sha512[0] == 0 && sha512[1] == 0)
							        return "&r=" + Encoding.ASCII.GetString(new[] {c1, c2, c3, c4, c5});
					        }
				        }
			        }
                }
            }
	        return null;
        }

        private async Task<IEnumerable<OrderModel>> SearchOrders(string text, string cookies)
        {
            //TODO support paging
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiOrdersSearch + $"?query={text}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiOrdersSearch} failed: {result.StatusCode.ToReadableCode()}");

            var resultString = result.BodyAsString;
            try
            {
                return JsonConvert.DeserializeObject<IEnumerable<OrderModel>>(resultString);
            }
            catch (Exception e)
            {
                await Console.Error.WriteLineAsync($"Failed to deserialize JSON of orders '{resultString}' found by query '{text}': {e}");
                throw new CheckerException(ExitCode.MUMBLE, $"Failed to deserialize JSON from {ApiOrdersSearch}");
            }
        }

        private async Task<IEnumerable<OrderModel>> SearchOrdersOfProduct(string productId, string cookies)
        {
            //TODO support paging
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiOrdersSearchForMyProduct + $"?productId={productId}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiOrdersSearchForMyProduct} failed: {result.StatusCode.ToReadableCode()}");

            var resultString = result.BodyAsString;
            try
            {
                return JsonConvert.DeserializeObject<IEnumerable<OrderModel>>(resultString);
            }
            catch (Exception e)
            {
                await Console.Error.WriteLineAsync($"Failed to deserialize JSON of orders '{resultString}' found for product '{productId}': {e}");
                throw new CheckerException(ExitCode.MUMBLE, $"Failed to deserialize JSON from {ApiOrdersSearchForMyProduct}");
            }
        }

        private async Task<OrderModel> GetOrder(string orderId, string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiOrdersGet + orderId, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiOrdersGet} failed: {result.StatusCode.ToReadableCode()}");

            var resultString = result.BodyAsString;
            try
            {
                return JsonConvert.DeserializeObject<OrderModel>(resultString);
            }
            catch (Exception e)
            {
                await Console.Error.WriteLineAsync($"Failed to deserialize JSON of order '{orderId}' from '{resultString}': {e}");
                throw new CheckerException(ExitCode.MUMBLE, $"Failed to deserialize JSON from {ApiOrdersGet}");
            }
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

        private string GenerateOrderText(string flag = null, string checksystemFlagId = null, string randomGuid = null)
        {
            var text = RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            text = text + " " + checksystemFlagId;

            if (RndUtil.GetInt(0, 3) == 0) text += ", " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 2) == 0) text += ", " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 2) == 0) text += ". " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();
            else if (RndUtil.GetInt(0, 3) == 0) text += "; " + RndText.RandomText(RndUtil.GetInt(10, 64)).RandomUpperCase().RandomLeet();

            text += flag != null ? " " + flag : null;
            if (RndUtil.GetInt(0, 3) == 0) text += ", " + RndText.RandomText(32).RandomUpperCase();
            text += randomGuid != null ? $" {randomGuid} " : null;
            text += flag != null ? $" (it's for {RndUtil.Choice("my mom", "my dad", "me", "my brother", "my sister")})" : null;
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

        private async Task<string> WhoAmIUser(string cookies)
        {
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var result = await client.DoRequestAsync(HttpMethod.Get, ApiWhoAmI, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
            if (result.StatusCode != HttpStatusCode.OK)
                throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiWhoAmI} failed: {result.StatusCode.ToReadableCode()}");

            return result.BodyAsString;
        }

        private async Task<IEnumerable<ProductModel>> SearchProducts(string text, string cookies)
        {
            //TODO support paging
            var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
            var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);
            client.Cookies.SetCookies(baseUri, cookies);

            var utcNow = DateTime.UtcNow;

            var query = $"?query={HttpUtility.UrlEncode(text)}&clientDt={HttpUtility.UrlEncode(utcNow.ToString("s"))}";
            var sw = Stopwatch.StartNew();
            var suffix = GenerateSuffixForPOW($"{baseUri.Host}{query}");
            sw.Stop();
            await Console.Error.WriteLineAsync($"Generated POW: query '{query}' : suffix '{suffix}' in {sw.ElapsedMilliseconds}ms");
            var result = await client.DoRequestAsync(HttpMethod.Get, ApiProductsSearch + query + suffix, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
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
        private const string ApiWhoAmI = "/Users/whoami";

        private const string ApiProductsCreate = "/api/Products/create";
        private const string ApiProductsSearch = "/api/Products/search";
        private const string ApiProductsGet = "/api/Products/";

        private const string ApiOrdersCreate = "/api/Orders/create";
        private const string ApiOrdersSearchForMyProduct = "/api/Orders/searchForMyProduct";
        private const string ApiOrdersSearch = "/api/Orders/search";
        private const string ApiOrdersGet = "/api/Orders/";

        private const int MaxHttpBodySize = 512 * 1024;
        private const int NetworkOpTimeout = 8000;

        private const int Port = 80;

        private static Uri GetBaseUri(string host) => new($"http://{host}:{Port}/");
    }
}
