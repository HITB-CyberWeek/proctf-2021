using System.Text.Json.Serialization;

namespace checker
{
	internal abstract class PutResult
	{
		[JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }
		[JsonPropertyName("public_flag_description")] public string PublicFlagDescription { get; set; }
	}
}
