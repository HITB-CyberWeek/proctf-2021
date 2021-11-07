using System;
using System.Text.Json.Serialization;

namespace checker.timecapsule
{
	public class Container
	{
		[JsonPropertyName("id")] public Guid? Id { get; set; }
		[JsonPropertyName("secret")] public Guid? Secret { get; set; }
		[JsonPropertyName("createDate")] public DateTime CreateDate { get; set; }
		[JsonPropertyName("expireDate")] public DateTime ExpireDate { get; set; }
		[JsonPropertyName("text")] public string Text { get; set; }
		[JsonPropertyName("author")] public string Author { get; set; }
		[JsonPropertyName("timeCapsule")] public string TimeCapsule { get; set; }
	}
}
