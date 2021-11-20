using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace mp.Models.Users
{
    public class UserModel
    {
        [DefaultValue("user1")]
        public string Login { get; set; }

        [DefaultValue("user1")]
        public string Password { get; set; }
    }
}
