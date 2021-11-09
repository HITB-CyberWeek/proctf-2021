using System;
using System.IO;
using System.Net;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Logging;

namespace timecapsule
{
	static class Program
	{
		static async Task Main()
		{
			AppDomain.CurrentDomain.ProcessExit += (_, _) => DatabaseContext.Flush();

			await new WebHostBuilder()
				.UseKestrel(options =>
				{
					options.Listen(IPAddress.Loopback, 7007);
					options.AddServerHeader = false;
					options.Limits.KeepAliveTimeout = TimeSpan.FromSeconds(30.0);
					options.Limits.MaxRequestBodySize = 2048L;
					options.Limits.MaxRequestLineSize = 2048;
					options.Limits.MaxRequestHeaderCount = 64;
					options.Limits.MaxRequestHeadersTotalSize = 8192;
					options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(3.0);
				}).UseContentRoot(Directory.GetCurrentDirectory()).UseStartup<Startup>().ConfigureLogging(builder => builder.AddConsole()).Build().RunAsync();
		}
	}
}
