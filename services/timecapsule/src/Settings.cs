using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace timecapsule
{
	public struct Settings
	{
		public int Port { get; set; }
		public Guid Key { get; set; }

		public static async Task<Settings> ReadAsync(byte[] temp, CancellationToken token)
			=> JsonSerializer.Deserialize<Settings>(new ReadOnlySpan<byte>(temp, 0, await Helper.ReadFileAsync("settings/timecapsule", temp, token)), new JsonSerializerOptions { ReadCommentHandling = JsonCommentHandling.Skip });
	}
}
