using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace checker.mp
{
    public class UserModel
    {
        public string Login { get; set; }
        public string Password { get; set; }
    }

    public class OrderModelPut
    {
        public string ProductId { get; set; }
        public string Description { get; set; }
    }

    public class OrderModel : OrderModelPut
    {
        public string Id { get; set; }
        public string Creator { get; set; }
        public DateTime Dt { get; set; }
    }

    public class ProductModelPut
    {
        public string Name { get; set; }
        public string Description { get; set; }
    }

    public class ProductModel : ProductModelPut
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string Creator { get; set; }
        public DateTime Dt { get; set; }
    }
}
