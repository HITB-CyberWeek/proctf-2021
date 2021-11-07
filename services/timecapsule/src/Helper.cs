using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace timecapsule
{
	public static class Helper
	{
		public static async Task<int> ReadFileAsync(string name, byte[] output, CancellationToken token)
		{
			int bytesRead, total = 0;
			await using var stream = File.OpenRead(name);
			while((bytesRead = await stream.ReadAsync(output, total, output.Length - total, token)) > 0)
				total += bytesRead;
			return total;
		}

		public static IEnumerable<T> With<T>(this IEnumerable<T> enumerable, Action<T> action)
		{
			foreach(var item in enumerable)
			{
				action(item);
				yield return item;
			}
		}
	}
}
