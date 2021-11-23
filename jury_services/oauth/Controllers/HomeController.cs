using Microsoft.AspNetCore.Mvc;

namespace OAuthServer.Controllers
{
    public class HomeController : Controller
    {
        public IActionResult Index()
        {
            return View();
        }
    }
}