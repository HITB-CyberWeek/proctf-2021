using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace mp.Entities
{
    public class User
    {
        public string FirstName { get; set; }
        public string LastName { get; set; }

        public string Login { get; set; }
        public byte[] PasswordHash { get; set; }
    }
}
