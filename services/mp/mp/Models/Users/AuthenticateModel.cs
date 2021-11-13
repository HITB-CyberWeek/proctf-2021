using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace mp.Models.Users
{
    public class AuthenticateModel
    {
        [Required]
        [DefaultValue("user1")]
        public string Login { get; set; }

        [Required]
        [DefaultValue("user1")]
        public string Password { get; set; }
    }
}
