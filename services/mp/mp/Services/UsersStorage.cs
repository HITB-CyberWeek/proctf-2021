using System;
using System.Collections.Concurrent;
using System.IO;
using System.Threading.Tasks;
using mp.Entities;
using Newtonsoft.Json;

namespace mp.Services
{
    class UsersStorage
    {
        private string stateDir;

        private ConcurrentDictionary<string, User> users = new();
        private readonly StreamWriter usersWriter;

        public UsersStorage(string stateDir)
        {
            var filePath = Path.Combine(stateDir, "records");
            if(File.Exists(filePath))
                InitFromFile(filePath);
            Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);
            usersWriter = File.AppendText(filePath);
        }

        private void InitFromFile(string filePath)
        {
            foreach(var line in File.ReadLines(filePath))
            {
                User user = null;
                try
                {
                    user = JsonConvert.DeserializeObject<User>(line);
                }
                catch(Exception e)
                {
                    Console.Error.WriteLine($"{nameof(UsersStorage)}.{nameof(InitFromFile)}: failed to parse user from '{line}'. Skipping", e);
                }
                TryAddToMemory(user);
            }
        }

        public User Find(string login)
        {
            return login != null && users.TryGetValue(login, out var result) ? result : null;
        }

        public async Task<bool> TryAdd(User user)
        {
            if(!TryAddToMemory(user))
                return false;

            return await TryPersistToFile(user);
        }

        private async Task<bool> TryPersistToFile(User user)
        {
            try
            {
                await usersWriter.WriteLineAsync(JsonConvert.SerializeObject(user));
                await usersWriter.FlushAsync();
            }
            catch(Exception e)
            {
                Console.Error.WriteLine($"{nameof(UsersStorage)}.{nameof(TryPersistToFile)}: failed to persist user '{user.Login}'. Skipping", e);
                return false;
            }

            return true;
        }

        private bool TryAddToMemory(User user)
        {
            if (user == null)
                return false;
            return users.TryAdd(user.Login, user);
        }
    }
}