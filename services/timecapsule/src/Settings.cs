using System;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace timecapsule
{
	public struct Settings
	{
		public int Port { get; set; }
		public long MaxRequestBodySize { get; set; }
		public int MaxRequestLineSize { get; set; }
		public int MaxRequestHeadersTotalSize { get; set; }
		public Guid Key { get; set; }

		static Settings()
		{
			if(File.Exists(SettingsFilepath))
				return;

			Directory.CreateDirectory(Path.GetDirectoryName(SettingsFilepath));

			using var stream = File.OpenWrite(SettingsFilepath);
			JsonSerializer.SerializeAsync(stream, new Settings { Port = 7007, MaxRequestBodySize = 2048L, MaxRequestLineSize = 2048, MaxRequestHeadersTotalSize = 8192, Key = Guid.NewGuid() }, JsonSerializerOptions).GetAwaiter().GetResult();
		}

		public static Task<Settings> ReadAsync(CancellationToken token)
			=> ReadAsync(new byte[4096], token);
		public static async Task<Settings> ReadAsync(byte[] temp, CancellationToken token)
			=> JsonSerializer.Deserialize<Settings>(new ReadOnlySpan<byte>(temp, 0, await Helper.ReadFileAsync(SettingsFilepath, temp, token)), JsonSerializerOptions);

		private static readonly JsonSerializerOptions JsonSerializerOptions = new() { ReadCommentHandling = JsonCommentHandling.Skip, PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
		private const string SettingsFilepath = "settings/timecapsule";
	}
}
