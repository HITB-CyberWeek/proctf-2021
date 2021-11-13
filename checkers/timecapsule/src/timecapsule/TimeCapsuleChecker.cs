using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using checker.net;
using checker.rnd;
using checker.utils;

namespace checker.timecapsule
{
	internal class TimeCapsuleChecker : IChecker
	{
		public Task<string> Info() => Task.FromResult("vulns: 1");

		public async Task Check(string host)
		{
			var baseUri = GetBaseUri(host);

			var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
			await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
			var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: false);

			var result = await client.DoRequestAsync(HttpMethod.Get, "/", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get / failed: {result.StatusCode.ToReadableCode()}");

			await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);

			result = await client.DoRequestAsync(HttpMethod.Get, ApiList, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiList} failed: {result.StatusCode.ToReadableCode()}");

			var items = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<List<Container>>(result.BodyAsString));
			if(items == null)
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiList} response: capsule collection expected");

			var date = DoIt.TryOrDefault(() => result.Headers.Date?.UtcDateTime);
			if(date == null)
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiList} response: bad server date");

			if(items.Any(item => item.ExpireDate < date.Value.AddMinutes(-1) && item.Secret == null))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiList} response: expired capsules expected to be open");

			if(items.Where(item => item.CreateDate > date.Value.AddMinutes(-3) && item.Secret != null).Any(item => DoIt.TryOrDefault(() => TimeCapsuleWrapper.Unwrap(item.TimeCapsule, item.Secret.Value))?.Text == null))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiList} response: failed to open some recent time capsules");

			await Console.Error.WriteLineAsync($"capsules {items.Count}").ConfigureAwait(false);
		}

		public async Task<PutResult> Put(string host, string flagId, string flag, int vuln)
		{
			var baseUri = GetBaseUri(host);

			var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
			await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
			var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

			var login = RndText.RandomWord(RndUtil.GetInt(10, 32)).RandomLeet().RandomUmlauts().RandomUpperCase();
			var password = RndText.RandomText(RndUtil.GetInt(8, 48)).RandomLeet().RandomUmlauts().RandomUpperCase();

			var result = await client.DoRequestAsync(HttpMethod.Post, ApiSignUp + $"?login={WebUtility.UrlEncode(login)}&password={WebUtility.UrlEncode(password)}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiSignUp} failed: {result.StatusCode.ToReadableCode()}");

			await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);

			result = await client.DoRequestAsync(HttpMethod.Get, ApiAuth, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiAuth} failed: {result.StatusCode.ToReadableCode()}");

			var authLogin = result.BodyAsString;
			if(authLogin.Trim().ToLower() != login.Trim().ToLower())
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiAuth} response: not signed in");

			await Console.Error.WriteLineAsync($"signed up as '{login}' logged in as '{authLogin}' password '{password}'").ConfigureAwait(false);
			login = authLogin;

			await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);

			var text = StringUtils.NullAwareJoin(" ",
				RndUtil.Bool() ? null : RndText.RandomText(RndUtil.GetInt(8, 48)).RandomLeet().RandomUmlauts().RandomUpperCase(),
				flag,
				RndUtil.Bool() ? null : RndText.RandomText(RndUtil.GetInt(8, 48)).RandomLeet().RandomUmlauts().RandomUpperCase());
			await Console.Error.WriteLineAsync($"generated text '{text}'").ConfigureAwait(false);

			var toBeOpened = DateTime.UtcNow.AddMinutes(RndUtil.GetInt(60, 180));
			result = await client.DoRequestAsync(HttpMethod.Post, ApiCapsule + $"?text={WebUtility.UrlEncode(text)}&toBeOpened={toBeOpened:s}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiCapsule} failed: {result.StatusCode.ToReadableCode()}");

			var capsule = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<Container>(result.BodyAsString));
			if(capsule?.Id == null || capsule.Secret == null || string.IsNullOrEmpty(capsule.TimeCapsule) || !string.Equals(capsule.Author, login, StringComparison.OrdinalIgnoreCase))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiCapsule} response: invalid capsule returned");
			var unwrapped = DoIt.TryOrDefault(() => TimeCapsuleWrapper.Unwrap(capsule.TimeCapsule, capsule.Secret.Value));
			if(unwrapped == null)
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiCapsule} response: can't open time capsule");
			if(unwrapped.Text == null || !unwrapped.Text.Contains(flag, StringComparison.OrdinalIgnoreCase))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiCapsule} response: flag not found in capsule");

			await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);

			result = await client.DoRequestAsync(HttpMethod.Get, ApiList, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiList} failed: {result.StatusCode.ToReadableCode()}");

			var items = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<List<Container>>(result.BodyAsString));
			if(items == null || items.Count == 0)
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiList} response: non-empty capsule collection expected");

			var container = items.FirstOrDefault(item => item.Id == capsule.Id);
			if(container == null || container.Author != capsule.Author || container.TimeCapsule != capsule.TimeCapsule)
				throw new CheckerException(ExitCode.MUMBLE, $"posted capsule not found in {ApiList} response");

			var cookie = client.Cookies?.GetCookieHeader(baseUri);
			await Console.Error.WriteLineAsync($"cookie '{cookie.ShortenLog(MaxCookieSize)}' with length '{cookie?.Length ?? 0}'").ConfigureAwait(false);

			if(cookie == null || cookie.Length > MaxCookieSize)
				throw new CheckerException(ExitCode.MUMBLE, "too large or invalid cookies");

			var bytes = DoIt.TryOrDefault(() => Encoding.UTF8.GetBytes(cookie));
			if(bytes == null || bytes.Length > MaxCookieSize)
				throw new CheckerException(ExitCode.MUMBLE, "too large or invalid cookies");

			return new TimeCapsulePutResult
			{
				Login = login,
				Password = password,
				Secret = capsule.Secret.Value,
				CapsuleId = capsule.Id.Value,
				TimeCapsule = capsule.TimeCapsule,
				Cookie = Convert.ToBase64String(bytes),

				PublicFlagId = capsule.Id.ToString(),
				PublicFlagDescription = "time capsule id"
			};
		}

		public async Task Get(string host, PutResult state, string flag, int vuln)
		{
			if(!(state is TimeCapsulePutResult put))
				throw new Exception($"Invalid state '{JsonSerializer.Serialize(state)}'");

			var baseUri = GetBaseUri(host);
			var cookie = Encoding.UTF8.GetString(Convert.FromBase64String(put.Cookie));

			#region WithoutAuth

			var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
			await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
			var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: false);

			var result = await client.DoRequestAsync(HttpMethod.Get, ApiCapsule + '/' + put.CapsuleId, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiList} failed: {result.StatusCode.ToReadableCode()}");

			var capsule = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<Container>(result.BodyAsString));
			if(capsule == null)
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiCapsule} response: capsule with flag not found");

			if(!string.Equals(put.Login, capsule.Author, StringComparison.OrdinalIgnoreCase))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiCapsule} response: some capsule fields corrupted");

			var unwrapped = DoIt.TryOrDefault(() => TimeCapsuleWrapper.Unwrap(put.TimeCapsule, put.Secret));
			if(unwrapped == null)
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiCapsule} response: failed to open time capsule");
			if(unwrapped.Text == null || !unwrapped.Text.Contains(flag, StringComparison.OrdinalIgnoreCase))
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiCapsule} response: flag not found");

			#endregion

			await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);

			#region WithAuth

			randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
			await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
			client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

			if(RndUtil.Bool())
			{
				await Console.Error.WriteLineAsync($"use saved cookie '{cookie}'").ConfigureAwait(false);
				client.Cookies.SetCookies(baseUri, cookie);
			}
			else
			{
				await Console.Error.WriteLineAsync($"use saved login '{put.Login}' and password '{put.Password}'").ConfigureAwait(false);

				result = await client.DoRequestAsync(HttpMethod.Post, ApiSignIn + $"?login={WebUtility.UrlEncode(put.Login)}&password={WebUtility.UrlEncode(put.Password)}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
				if(result.StatusCode != HttpStatusCode.OK)
					throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiSignIn} failed: {result.StatusCode.ToReadableCode()}");

				await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);
			}

			result = await client.DoRequestAsync(HttpMethod.Get, ApiAuth, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiAuth} failed: {result.StatusCode.ToReadableCode()}");

			var authLogin = result.BodyAsString;
			if(authLogin?.Trim().ToLower() != put.Login.ToLower())
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiAuth} response: not signed in");

			await RndUtil.RndDelay(MaxDelay).ConfigureAwait(false);

			result = await client.DoRequestAsync(HttpMethod.Get, ApiList + $"?author={WebUtility.UrlEncode(authLogin)}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiList} failed: {result.StatusCode.ToReadableCode()}");

			var items = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<List<Container>>(result.BodyAsString));
			if(items == null || items.Count == 0)
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiList} response: non-empty capsule collection expected");

			var container = items.FirstOrDefault(item => item.Id == put.CapsuleId);
			if(container == null || container.TimeCapsule != put.TimeCapsule || container.Secret == null)
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiList} response: time capsule with flag not found");

			unwrapped = DoIt.TryOrDefault(() => TimeCapsuleWrapper.Unwrap(container.TimeCapsule, container.Secret.Value));
			if(unwrapped == null)
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiCapsule} response: failed to open time capsule");
			if(unwrapped.Text == null || !unwrapped.Text.Contains(flag, StringComparison.OrdinalIgnoreCase))
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiCapsule} response: flag not found");

			#endregion
		}

		private const int Port = 7007;

		private const int MaxHttpBodySize = 512 * 1024;
		private const int MaxCookieSize = 1024;

		private const int MaxDelay = 3000;
		private const int NetworkOpTimeout = 8000;

		private static Uri GetBaseUri(string host) => new($"http://{host}:{Port}/");

		private const string ApiAuth = "/auth";
		private const string ApiList = "/capsules";
		private const string ApiSignUp = "/signup";
		private const string ApiSignIn = "/signin";
		private const string ApiCapsule = "/capsule";
	}
}
