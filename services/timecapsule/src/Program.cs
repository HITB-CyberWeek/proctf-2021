using System;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Hosting;

namespace timecapsule
{
	static class Program
	{
		static async Task Main()
		{
			AppDomain.CurrentDomain.ProcessExit += (_, _) => DatabaseContext.Flush();

			var settings = await Settings.ReadAsync(CancellationToken.None);
			await new WebHostBuilder()
				.UseKestrel(options =>
				{
					options.Listen(IPAddress.Any, settings.Port);
					options.AddServerHeader = false;
					options.Limits.KeepAliveTimeout = TimeSpan.FromSeconds(30.0);
					options.Limits.MaxRequestBodySize = settings.MaxRequestBodySize;
					options.Limits.MaxRequestLineSize = settings.MaxRequestLineSize;
					options.Limits.MaxRequestHeaderCount = 64;
					options.Limits.MaxRequestHeadersTotalSize = settings.MaxRequestHeadersTotalSize;
					options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(3.0);
				}).UseContentRoot(Directory.GetCurrentDirectory()).UseStartup<Startup>().Build().RunAsync();
		}
	}
}
