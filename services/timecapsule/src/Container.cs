using System;
using System.Threading;
using System.Threading.Tasks;

namespace timecapsule
{
	public class Container
	{
		public Guid? Id { get; set; }
		public Guid? Secret { get; set; }
		public DateTime CreateDate { get; set; }
		public DateTime ExpireDate { get; set; }
		public string Text { get; set; }
		public string Author { get; set; }
		public string TimeCapsule { get; set; }

		public async Task<string> Wrap(CancellationToken token) => TimeCapsule = await TimeCapsuleWrapper.WrapAsync(this, token, Secret);
	}
}
